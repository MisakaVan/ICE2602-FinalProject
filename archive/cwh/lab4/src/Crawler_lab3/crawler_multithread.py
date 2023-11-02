# SJTU EE208
# Lab3

import http
import http.client
import json
import logging
import queue
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import namedtuple
from typing import List

from lib.MyIOLib import *
from lib.MyParserLib import *

# Type alias
Url = str

GetContentResult = namedtuple("GetContentResult",
                              ["status", "content"], )


def make_brief(url: Url):
    if len(url) > 50:
        url_for_logging = url[:47] + "..."
    else:
        url_for_logging = url
    return url_for_logging


def get_content(url: Url) -> GetContentResult:
    url_for_logging = make_brief(url)

    content: bytes = b""
    status = -1

    request = urllib.request.Request(url)
    request.add_header("User-Agent",
                       "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15")
    try:
        response: http.client.HTTPResponse = urllib.request.urlopen(request, timeout=0.5)
    except Exception as e:
        logging.error(f"Crawling {url_for_logging:>50s} failed with exception: {e}")
    else:
        try:
            content = response.read()
            status = response.getcode()
            logging.debug(f"Crawling {url_for_logging:>50s} succeeded with exit code {status}")
        except Exception as e2:
            logging.error(f"Failed in reading response from {url_for_logging:>50s}: {e2}")

    return GetContentResult(status, content)


def parse_all_urls(content: bytes, home_url: Url) -> List[Url]:
    return list(parse_url(content, home_url))


class Counter:
    """
    Wrap an int to make it mutable
    """

    def __init__(self):
        self.value = 0


def sub_crawler(_queue: queue.Queue,
                _succ_count: Counter,
                _count_lock: threading.Lock,
                _set,
                _list,
                max_count=50,
                _interval_ms=500
                ):
    logging.info(f"{threading.current_thread().name} started")
    # global succ_count
    while True:
        time.sleep(_interval_ms / 1000)
        if _succ_count.value >= max_count:
            break

        cur_url = _queue.get()
        if cur_url in _set:
            _queue.task_done()
            continue

        with _count_lock:
            _set.add(cur_url)

        res = get_content(cur_url)
        if res.status == -1:
            _queue.task_done()
            continue

        try:
            add_page_to_folder(cur_url, res.content)
        except Exception as e:
            logging.error(f"Failed to add contents to cache: {cur_url} ")
        else:
            with _count_lock:
                crawled_succ_list.append(cur_url)
                _succ_count.value += 1
                logging.info(f"{threading.current_thread().name:>12s}: {_succ_count.value:>4d}; {make_brief(cur_url)}")


        urls = parse_all_urls(res.content, cur_url)
        try:
            for url in urls:
                _queue.put_nowait(url)
        except queue.Full:
            logging.debug(f"{threading.current_thread().name} finds queue is full")

        _queue.task_done()

    # Remove redundant items
    # One thread ending at a time.
    with cur_count_lock:
        if not _queue.empty():
            logging.debug(f"{threading.current_thread().name} emptying the queue...")
            while not _queue.empty():
                _queue.get()
                _queue.task_done()

    logging.info(f"{threading.current_thread().name} exiting...")


if __name__ == '__main__':

    # Logging config
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s.%(msecs)03d [%(levelname)s] %(message)s",
                        datefmt="%H:%M:%S")

    # Args
    # def test_get_user_input():
    #     _seed = input("输入种子url, 留空为默认值https://www.sjtu.edu.cn.")
    #     if _seed == '':
    #         _seed = 'https://www.sjtu.edu.cn'
    #     _worker_count = input("输入线程数量, 留空为默认值5.")
    #     if _worker_count == '':
    #         _worker_count = 5
    #     _max_page_count = input("输入至少需要爬取的网页数量, 留空为默认值50.")
    #     if _max_page_count == '':
    #         _max_page_count = 50
    #     _interval_ms = input("输入单个线程爬取间隔（毫秒）, 留空为默认值300.")
    #     if _interval_ms == '':
    #         _interval_ms = 300
    #     return _seed, int(_worker_count), int(_max_page_count), int(_interval_ms)

    # argv_length = len(sys.argv)
    # if argv_length == 1:
    #     seed = 'https://www.sjtu.edu.cn'
    #     worker_count = 5
    #     max_page_count = 50
    #     interval_ms = 300
    # else:
    #     seed = sys.argv[1]
    #     worker_count = int(sys.argv[2])
    #     max_page_count = int(sys.argv[3])
    #     interval_ms = int(sys.argv[4])

    with open("crawler_config.json", "r") as f:
        config_dict = json.load(f)

    seed = config_dict.get("seed")
    worker_count = config_dict.get("worker_count")
    max_page_count = config_dict.get("max_page_count")
    interval_ms = config_dict.get("interval_ms")

    # Init

    q = queue.Queue(maxsize=500, )
    q.put(seed)

    cur_count_lock = threading.Lock()
    succ_count = Counter()
    crawled_set = set()
    crawled_succ_list = list()

    workers = [threading.Thread(target=sub_crawler, args=(
        q,
        succ_count,
        cur_count_lock,
        crawled_set,
        crawled_succ_list,
        max_page_count,
        interval_ms
    ), name=f"Worker<{i}>") for i in range(worker_count)]

    # Launch

    start_time = time.time()

    for worker in workers:
        worker.start()

    q.join()  # Wait until q is empty

    # Wait until all workers exit
    for worker in workers:
        worker.join()

    end_time = time.time()
    logging.info(f"Time used: {end_time - start_time:.3f} secs")
    logging.info(f"Tried {len(crawled_set)} urls, succeeded {len(crawled_succ_list)} urls")
