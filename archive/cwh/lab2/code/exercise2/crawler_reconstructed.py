# SJTU EE208
# Lab2
# This is a rewritten version of crawler.py for readability's sake.

import http
import http.client
import logging
import os
import string
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import deque, namedtuple
from typing import List, Iterable, Set, Deque, Callable, Literal, Dict, Tuple, AnyStr

import MyParserLib

# Logging config
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")

# Type alias
Url = str

# Constants
VALID_CHARS = f"-_.() {string.ascii_letters}{string.digits}"


def as_valid_filename(s: Url, postfix: str = None) -> str:
    if postfix is None:
        postfix = "txt"
    return urllib.parse.quote_plus(s) + "." + postfix
    # return "".join(ch for ch in s if ch in VALID_CHARS) + ".txt"


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


def update_deque_bfs(deque_: Deque[str],
                     crawled_set_: Set[str],
                     urls_: Iterable[Url]) -> None:
    for url in urls_:
        if url not in crawled_set_:
            deque_.append(url)


def update_deque_dfs(deque_: Deque[str],
                     crawled_set_: Set[str],
                     urls_: Iterable[Url]) -> None:
    for url in urls_:
        if url not in crawled_set_:
            deque_.appendleft(url)


def crawl(seed: Url,
          _method: Literal["bfs", "dfs"],
          _max_page_count: int = 100,
          interval_ms=500) -> Tuple[Dict[str, List[str]], List[str]]:
    interval_sec = interval_ms / 1000

    if _method not in ("bfs", "dfs"):
        raise ValueError("method should be dfs or bfs")
    update_method: Callable[[Deque[str], Set[str], Iterable[str]], None] \
        = update_deque_dfs if _method == "dfs" else update_deque_bfs

    deque_to_crawl: deque[str] = deque([seed])
    crawled_list: List[str] = list()
    crawled_set: Set[str] = set()
    crawled_count = 0
    graph: Dict[str, List[str]] = dict()

    start_time = time.time()

    while crawled_count < _max_page_count and deque_to_crawl:
        time.sleep(interval_sec)
        cur_url = deque_to_crawl.popleft()
        if cur_url in crawled_set:
            continue
        crawled_count += 1
        crawled_set.add(cur_url)
        crawled_list.append(cur_url)

        # Do something with cur_url

        res = get_content(cur_url)
        if res.status == -1:
            continue

        add_page_to_folder(cur_url, res.content)
        urls = parse_all_urls(res.content, cur_url)
        graph.update({cur_url: urls})
        update_method(deque_to_crawl, crawled_set, urls)

    end_time = time.time()

    logging.info(
        f"Crawled {len(crawled_list)} urls, succeeded {len(graph)} urls, time used {end_time - start_time:.3f} secs")
    return graph, crawled_list


def test_crawler():
    graph1, crawled_list1 = crawl("https://www.sjtu.edu.cn", "bfs", 100, interval_ms=500)


if __name__ == "__main__":
    argv_length = len(sys.argv)
    if argv_length == 1:
        test_crawler()
    else:
        seed_url = sys.argv[1]
        method = sys.argv[2]
        max_page_count = int(sys.argv[3])
        crawl(seed_url, method, max_page_count)
