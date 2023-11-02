# SJTU EE208
# Lab3
# A multiprocess web-crawler

import http
import http.client
import logging
import multiprocessing as mp
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import namedtuple
from typing import List, AnyStr, Dict

import lib.MyParserLib as MyParserLib

# Logging config
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")

# Type alias
Url = str


def as_valid_filename(s: Url, postfix: str = None) -> str:
    if postfix is None:
        postfix = "txt"
    return urllib.parse.quote_plus(s) + "." + postfix


def add_page_to_folder(url: Url, content: str):  # 将网页存到文件夹里，将网址和对应的文件名写入index.txt中
    index_filename = 'crawler_cache/index.txt'  # index.txt中每行是'网址 对应的文件名'
    folder = 'crawler_cache/html'  # 存放网页的文件夹
    filename = as_valid_filename(url, postfix="html")  # 将网址变成合法的文件名

    if not os.path.exists('crawler_cache'):  # 如果文件夹不存在则新建
        os.mkdir('crawler_cache')

    if not os.path.exists(folder):  # 如果文件夹不存在则新建
        os.mkdir(folder)

    with open(index_filename, 'a') as index:
        index.write(url + '\t' + filename + '\n')
        # Notice here: 由于依赖库更新，如果在这里写入txt时存在数据类型不符的bug，
        # 尝试将url.encode()的byte类型数据转换成string后写入txt文件。

    with open(os.path.join(folder, filename), 'w') as f:
        f.write(content)  # 将网页存入文件


GetContentResult = namedtuple("GetContentResult",
                              ["status", "content"])


def get_content(url: Url) -> GetContentResult:
    content: AnyStr = ""
    status = -1

    request = urllib.request.Request(url)
    request.add_header("User-Agent",
                       "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15")
    try:
        response: http.client.HTTPResponse = urllib.request.urlopen(request, timeout=0.5)
    except Exception as e:
        logging.error(f"Crawling {url} failed with exception: {e}")
    else:
        content = response.read()
        status = response.getcode()
        logging.info(f"Crawling {url} succeeded with exit code {status}")

    return GetContentResult(status, str(content))


def parse_all_urls(content: str, home_url: Url) -> List[Url]:
    return list(MyParserLib.parse_url(content, home_url))


class CrawlerMultiThread:
    def __init__(self, start_url: Url, max_page_count: int, process_count: int = None, interval_ms: int = 300):
        self.interval_ms = interval_ms
        self.max_page_count = max_page_count
        logging.info(f"cpu count is {mp.cpu_count()}")
        self.process_count = max(mp.cpu_count() - 2, 1)
        if process_count is not None:
            if process_count > mp.cpu_count() - 2:
                logging.warning(f"Initializing with {process_count} processes, which is larger than upper bound")
            else:
                self.process_count = process_count

        self.page_count = mp.Value('i', 0)
        self.manager = mp.Manager()
        self.crawled_urls: Dict[Url, int] = self.manager.dict()
        self.crawled_urls_succ_list: List[Url] = self.manager.list()
        self.queue = mp.Queue()
        self.queue.put(start_url)

        self.crawled_urls_lock = self.manager.Lock()
        self.logger_lock = self.manager.Lock()

        self.workers = [
            mp.Process(
                target=CrawlerMultiThread.sub_crawler,
                name=f"SubCrawler<{i}>",
                args=(self, self.interval_ms),
                daemon=False
            ) for i in range(self.process_count)]

    @staticmethod
    def sub_crawler(_self: 'CrawlerMultiThread', interval_ms: int = None):
        interval = 0.5 if interval_ms is None else interval_ms / 1000
        logging.info(f"{mp.current_process().name} started, {interval = :.3f} secs.")

        while True:
            with _self.crawled_urls_lock:
                # logging.debug(f"{mp.current_process().name} sees {_self.page_count.value = }")
                if _self.page_count.value >= _self.max_page_count:
                    logging.debug(f"{mp.current_process().name} met {_self.page_count.value} urls, exiting")
                    break

            time.sleep(interval)

            cur_url = _self.queue.get()
            if cur_url in _self.crawled_urls:
                continue

            with _self.crawled_urls_lock:
                _self.crawled_urls[cur_url] = 1

            res = get_content(cur_url)
            if res.status == -1:
                continue

            add_page_to_folder(cur_url, res.content)

            with _self.crawled_urls_lock:
                _self.crawled_urls_succ_list.append(cur_url)
                _self.page_count.value += 1

            urls = parse_all_urls(res.content, cur_url)

            for url in urls:
                _self.queue.put(url)

        logging.info(f"{mp.current_process().name} Exiting.")

    def run(self):
        start_time = time.time()
        logging.info(f"Crawler runs")
        logging.info(f"Number of workers is {len(self.workers)}")
        for worker in self.workers:
            worker.start()

        # for worker in self.workers:
        #     worker.join()

        # logging.info(f"{mp.active_children() = }")

        last_page_count = 0
        last_update_time = time.time()
        timeout = 10

        while True:
            time.sleep(1)
            logging.debug(f"Active children: {sorted([proc.name for proc in mp.active_children()])}")
            with self.crawled_urls_lock:
                cur_page_count = self.page_count.value
            logging.info(f"Crawler waiting, {cur_page_count = }, {self.max_page_count = }")

            if cur_page_count > last_page_count:
                last_page_count = cur_page_count
                last_update_time = time.time()

            if time.time() - last_update_time > timeout:
                logging.warning(f"Crawler crawled nothing in the last {timeout} secs. Shutting down.")
                break

            flag = False
            for worker in self.workers:
                if worker.is_alive():
                    flag = True
                    break

            if flag:
                continue

            logging.info(f"Crawler sees all workers ended")
            logging.info(f"{mp.active_children() = }")
            break
        #
        #
        # logging.debug(f"Task done. Waiting for workers to shut down")
        # for worker in self.workers:
        #     worker.join()
        for worker in self.workers:
            if worker.is_alive():
                logging.info(f"{worker.name} shut down by mainThread")
                worker.terminate()

        logging.info(f"Crawler exiting")
        end_time = time.time()
        logging.info(f"Crawler run() used {end_time - start_time:.3f} secs.")

    def state(self):
        logging.info(f"Crawled {self.page_count.value} urls")
        print(self.crawled_urls)
        print(self.crawled_urls.__len__())
        print(self.crawled_urls_succ_list.__len__())


if __name__ == "__main__":
    crawler = CrawlerMultiThread(start_url="https://www.sjtu.edu.cn",
                                 max_page_count=200,
                                 process_count=4,
                                 interval_ms=500
                                 )
    crawler.run()
    crawler.state()
