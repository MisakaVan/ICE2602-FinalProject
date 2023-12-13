import logging
import queue
from typing import Optional, Callable
from urllib import request

logger = logging.getLogger(__name__)


def _crawl(_url: str,
           _queue: queue.Queue,
           _output_dir: str,
           _db_path: str,
           _request_header_dict: Optional[dict] = None,
           _filter_func: Optional[Callable[[str], bool]] = None,
           ):
    """

    :param _url: the url to be crawled.
    :param _queue: the urls crawled from the url will be added to this queue. generally, this is the Crawler._queue.
    :param _output_dir: the raw html file will be saved in this directory.
    :param _db_path: record the url-filename-crawled_time mapping.
    :param _filter_func: a function to filter the urls. only the urls that pass the filter will be added to the queue.
    :return:
    """
    new_request = request.Request(_url)
    if _request_header_dict is not None:
        for key, value in _request_header_dict.items():
            new_request.add_header(key, value)

    try:
        response = request.urlopen(new_request, timeout=0.5)
    except Exception as e:
        pass

    raise NotImplementedError

def _sub_worker(_queue: queue.Queue,
                _output_dir: str,
                _db_path: str,
                _request_header_dict: Optional[dict] = None,
                _filter_func: Optional[Callable[[str], bool]] = None,
                ):
    """
    a sub-process to crawl urls from the queue.
    Basically, it gets an url from the queue, crawls the url (use _crawl() function), and adds the urls crawled from the url to the queue.
    :param _queue:
    :param _output_dir:
    :param _db_path:
    :param _request_header_dict:
    :param _filter_func:
    :return:
    """
    raise NotImplementedError


class MultithreadCrawler:
    def __init__(self,
                 max_threads=4,
                 interval_ms=3000,
                 output_dir='output',
                 request_header_dict: Optional[dict] = None,
                 filter_func: Optional[Callable[[str], bool]] = None,
                 max_count=500,
                 max_queue_size=1000,

                 ):
        """

        :param max_threads:
        :param interval_ms:
        :param output_dir: a new dir of the current time will be created under this dir. and the raw html files will be saved under that.
        :param request_header_dict: allows customizing the request header.
        :param filter_func: only the urls that pass the filter will be stored.
        """
        self._max_threads = max_threads
        self._interval_ms = interval_ms
        self._output_dir = output_dir
        self._request_header_dict = request_header_dict
        self._filter_func = filter_func
        self._max_count = max_count

        self._queue = queue.Queue(maxsize=max_queue_size)

        raise NotImplementedError

    def run(self):
        """
        create sub-processes to crawl the urls in the queue.
        :return:
        """

        raise NotImplementedError


def test1():
    crawler = MultithreadCrawler(
        max_threads=4,
        output_dir='./output',
        request_header_dict={
            "User-Agent":
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15"
        }
    )


if __name__ == '__main__':
    pass
