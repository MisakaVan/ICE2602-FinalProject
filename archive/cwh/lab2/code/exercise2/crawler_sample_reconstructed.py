# SJTU EE208
# Lab2
# This is a rewritten version of crawler_sample.py for readability's sake.

from collections import deque
from typing import List, AnyStr, Iterable, Set, Deque, Callable, Literal, Dict, Tuple

g: Dict[str, List[str]] = {'A': ['B', 'C', 'D'],
                           'B': ['E', 'F'],
                           'D': ['G', 'H'],
                           'E': ['I', 'J'],
                           'G': ['K', 'L']}


def get_page(page: AnyStr) -> List[AnyStr]:
    return g.get(page, [])


def get_all_urls(content: List[AnyStr]) -> List[AnyStr]:
    return content


def update_deque_bfs(deque_: Deque[str],
                     crawled_set_: Set[str],
                     urls_: Iterable[str]) -> None:
    for url in urls_:
        if url not in crawled_set_:
            deque_.append(url)


def update_deque_dfs(deque_: Deque[str],
                     crawled_set_: Set[str],
                     urls_: Iterable[str]) -> None:
    for url in urls_:
        if url not in crawled_set_:
            deque_.appendleft(url)


def crawl(seed: str, method: Literal["bfs", "dfs"]) -> Tuple[Dict[str, List[str]], List[str]]:
    if method not in ("bfs", "dfs"):
        raise ValueError("method should be dfs or bfs")

    update_method: Callable[[Deque[str], Set[str], Iterable[str]], None] \
        = update_deque_dfs if method == "dfs" else update_deque_bfs
    deque_to_crawl = deque([seed])
    crawled_list: List[str] = list()
    crawled_set: Set[str] = set()
    graph: Dict[str, List[str]] = dict()
    while deque_to_crawl:
        cur_url = deque_to_crawl.popleft()
        if cur_url in crawled_set:
            continue
        print(f"Processing {cur_url}")
        crawled_set.add(cur_url)
        crawled_list.append(cur_url)

        # Do something with cur_url
        urls = get_all_urls(get_page(cur_url))
        graph.update({cur_url: urls})
        update_method(deque_to_crawl, crawled_set, urls)

    return graph, crawled_list


def test_crawler_sample():
    graph_dfs, crawled_dfs = crawl('A', 'dfs')
    print('graph_dfs:', graph_dfs)
    print('crawled_dfs:', crawled_dfs)

    graph_bfs, crawled_bfs = crawl('A', 'bfs')
    print('graph_bfs:', graph_bfs)
    print('crawled_bfs:', crawled_bfs)


if __name__ == "__main__":
    test_crawler_sample()
