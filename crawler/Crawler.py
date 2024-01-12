"""
A multithread crawler.

Details:
- use bfs to crawl the urls.
  - the urls crawled from the url will be added to the queue.
  - use a filter function to filter the urls. only the urls that pass the filter will be added to the queue.
  - use another filter function to determine which files to save.
- use bloom filter.
  - one bloom filter recording the urls that have been crawled.
  - one bloom filter recording the urls whose files have been saved.
- use DataSet to save the crawled data.
- multithread.
  - use a queue to store the urls to be crawled. (queue.Queue)
  - control the behavior of the threads by using threading.Event.
    - Auto-save: the main thread holds an event "stop_event".
      - the main thread will set the event every constant time interval, or every 500 files saved, etc.
      - sub-threads will cease to crawl urls when the event is set.
      - when all sub-threads cease, the main thread will save the current state.
        this is to make sure all the tasks are either in the queue, or are done when the state is saved.
- Auto-save.
  - the state to be tracked are:
    - the current queue.
    - current bloom filters. (uses its own save/load mechanism)
    - the current DataSet state. (uses its own save/load mechanism)


"""
import json
import queue
import threading
import shutil
import time
import os.path as osp
import os
import urllib.parse

from typing import Optional

import loguru
import numpy as np

import FileSet as fs
import BloomFilter as bf
import utils
import request_utils

logger = loguru.logger

strict_filter_recipe = {
    "sina": utils.is_sina_sports_football_article,
    "zhibo8": utils.is_zhibo8_news_football_article
}

loose_filter_recipe = {
    "sina": utils.is_sina_sports_domain,
    "zhibo8": utils.is_zhibo8_football_domain
}

zhibo8_seeds = [
    'https://news.zhibo8.com/zuqiu/more.htm?label=中超',
    'https://news.zhibo8.com/zuqiu/more.htm?label=英超',
    'https://news.zhibo8.com/zuqiu/more.htm?label=法甲',
    'https://news.zhibo8.com/zuqiu/more.htm?label=西甲',
    'https://news.zhibo8.com/zuqiu/more.htm?label=意甲',
    'https://news.zhibo8.com/zuqiu/more.htm?label=德甲',
    'https://news.zhibo8.com/zuqiu/more.htm?label=欧冠',
    'https://news.zhibo8.com/zuqiu/more.htm',
]

zhibo8_seeds_quoted = list(map(lambda url: urllib.parse.quote(url, safe='/:?='), zhibo8_seeds))

# these urls may be manually added to the queue.
# when they are popped out, they bypass the met-check.
# they still won't be added to the queue by the sub-threads.
bypass_bloomfilter_recipe = {
    "sina": set().copy(),
    "zhibo8": set(zhibo8_seeds_quoted).copy()
}


class Crawler:
    """
    File structure:
    | CrawlerParams.json
    | met_urls/ (BloomFilter)
    | saved_urls/ (BloomFilter)
    | saved_files/ (FileSet)
    | snapshots/


    """

    queue: queue.Queue
    met_url_bf: bf.BloomFilter
    saved_url_bf: bf.BloomFilter
    saved_content: fs.FileSet

    def __init__(self,
                 directory: Optional[str] = None,
                 max_queue_size: int = 1000,
                 max_workers: int = 4,
                 interval_ms: int = 3000,
                 met_url_bf_capacity: int = 100000,
                 saved_url_bf_capacity: int = 100000,
                 error_rate: float = 1e-5,
                 filter_config: str = "sina",
                 user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1.2 Safari/605.1.15",
                 state_dict: Optional[dict] = None,

                 ):
        self.lock = threading.Lock()
        self.pause_event = threading.Event()
        self.stop_event = threading.Event()

        if state_dict is None:
            self.queue = queue.Queue(maxsize=max_queue_size)

            self.directory = directory
            self.max_workers = max_workers
            self.interval_ms = interval_ms
            self.user_agent = user_agent
            self.met_url_bf = bf.bloom_filter_maker(capacity=met_url_bf_capacity, error_rate=error_rate)
            self.saved_url_bf = bf.bloom_filter_maker(capacity=saved_url_bf_capacity, error_rate=error_rate)
            self.saved_content = fs.FileSet(directory=osp.join(directory, "saved_files"))

            self.filter_config = filter_config

            self.met_url_bf_dir = osp.join(directory, "met_urls")
            self.saved_url_bf_dir = osp.join(directory, "saved_urls")
            self.saved_content_dir = osp.join(directory, "saved_files")

            self.init_directory()

        else:
            self.queue = state_dict["queue"]

            self.directory = state_dict["directory"]
            self.max_workers = state_dict["max_workers"]
            self.interval_ms = state_dict["interval_ms"]
            self.user_agent = state_dict["user_agent"]
            self.met_url_bf = state_dict["met_url_bf"]
            self.saved_url_bf = state_dict["saved_url_bf"]
            self.saved_content = state_dict["saved_content"]

            self.filter_config = state_dict["filter_config"]

            self.met_url_bf_dir = osp.join(self.directory, "met_urls")
            self.saved_url_bf_dir = osp.join(self.directory, "saved_urls")
            self.saved_content_dir = osp.join(self.directory, "saved_files")

        self.strict_filter = strict_filter_recipe[self.filter_config]
        self.loose_filter = loose_filter_recipe[self.filter_config]

        logger.info(f"Crawler's strict filter is {self.strict_filter}")
        logger.info(f"Crawler's loose filter is {self.loose_filter}")

    def run(self,
            epoch_count: int = 2,
            secs: int = 30,
            start_epoch: int = 0,
            make_snapshot: bool = True
            ):
        """
        Run the crawler.
        :param epoch_count:
        :param secs:
        :param start_epoch:
        :param make_snapshot:
        :return:
        """
        logger.info(f"Starting the crawler.")
        for epoch in range(start_epoch, start_epoch + epoch_count):
            self.stop_event.clear()
            logger.info(f"Starting epoch {epoch}")
            start_time = time.time()
            workers = []
            for i in range(self.max_workers):
                # t = threading.Thread(target=self.worker, name=f"worker-{i}")
                # t.start()
                workers.append(threading.Thread(target=self.worker, name=f"worker-{i}"))

            for worker in workers:
                worker.start()

            while True:
                cur_time = time.time()
                logger.info(
                    f"MainThread : Epoch {epoch}, Tick: {cur_time - start_time:.3f} seconds passed. Queue length ~ {self.queue.qsize()}.")
                if cur_time - start_time > secs:
                    break
                time.sleep(5)

            logger.info(f"MainThread : set the Stopping flag...")
            self.stop_event.set()

            time.sleep(self.interval_ms / 800 + 2)
            # if there are still unfinished workers, kill them.
            for t in workers:
                if t.is_alive():
                    logger.info(f"MainThread : Killing worker {t.name}")
                    t._stop()

            logger.info(f"MainThread : All workers stopped.")

            if make_snapshot:
                snapshot_name = fs.get_snapshot_name()
                self.make_snapshot(snapshot_name)

            logger.info(f"Epoch {epoch} completed.")
            logger.info(f"Total {self.saved_content.recorded_entries.__len__()} files saved.")

            self.save()

        logger.info(f"Completed the crawler.")

    def worker(self,
               ):
        bypass_bloomfilter_set = bypass_bloomfilter_recipe[self.filter_config]
        worker_name = threading.current_thread().name
        logger.info(f"{worker_name} started.")
        while True:
            if self.stop_event.is_set():
                logger.info(f"{worker_name} sees the stop event.")
                break
            try:
                cur_url = self.queue.get(timeout=1)
            except queue.Empty:
                continue

            if self.queue.qsize() > 0.5 * self.queue.maxsize:
                # dropout some here
                if not self.strict_filter(cur_url):
                    if np.random.uniform() > 0.25:
                        self.queue.task_done()
                        continue

            if cur_url not in bypass_bloomfilter_set:
                with self.lock:
                    if self.met_url_bf.__contains__(cur_url):
                        logger.info(f"{worker_name} : {cur_url} has been met.")
                        self.queue.task_done()
                        continue

            # logger.info(f"{worker_name} : {cur_url} to crawl.")

            _content = self.get_content(cur_url)
            if _content is None:
                self.queue.task_done()
                continue

            logger.info(f"{worker_name} : {cur_url} : crawled success.")
            # mark the url as met
            self.met_url_bf.add(cur_url)

            if self.strict_filter(cur_url):
                self.saved_url_bf.add(cur_url)
                # save the file
                self.save_file(_content, cur_url)
                logger.info(f"{worker_name} : {cur_url} : saved.")
            else:
                logger.info(f"{worker_name} : {cur_url} : not saved.")


            # logger.info(f"{worker_name} : {cur_url}, adding urls to the queue.")
            # add the urls to the queue
            new_urls = set(request_utils.parse_all_urls(_content, cur_url))

            logger.info(f"{worker_name} : {cur_url} : found {len(new_urls)} urls.")

            max_insert_count = int(0.1 * self.queue.maxsize)
            insert_count = 0

            for new_url in new_urls:

                # fuck I forgot this until halfway
                new_url = utils.as_unique_url(new_url)

                if self.met_url_bf.__contains__(new_url):
                    continue
                try:
                    if self.strict_filter(new_url):
                        self.queue.put(new_url, block=False)
                        insert_count += 1
                    elif self.loose_filter(new_url):
                        # randomly dropout
                        # the more elements in the queue, the more likely to drop out
                        # this may change.
                        _max_size = self.queue.maxsize
                        _cur_size = self.queue.qsize()

                        _prob = (_cur_size / _max_size) ** 2

                        if np.random.uniform() > _prob:
                            continue
                        self.queue.put(new_url, block=False)
                        insert_count += 1
                except queue.Full:
                    pass
                if insert_count >= max_insert_count:
                    break

            delay_ms = np.random.uniform(0.8, 1.2) * self.interval_ms
            time.sleep(delay_ms / 1000)

            self.queue.task_done()

        logger.info(f"{worker_name} stopped.")

    # loading and saving stuff

    def init_directory(self,
                       ):
        # create/clear the directory
        if osp.exists(self.directory):
            shutil.rmtree(self.directory)
        os.makedirs(self.directory, exist_ok=True)
        os.makedirs(osp.join(self.directory, "met_urls"), exist_ok=True)
        os.makedirs(osp.join(self.directory, "saved_urls"), exist_ok=True)
        os.makedirs(osp.join(self.directory, "saved_files"), exist_ok=True)
        os.makedirs(osp.join(self.directory, "snapshots"), exist_ok=True)

    def as_state_dict(self,
                      ):

        state_dict = {
            "directory": self.directory,
            "max_queue_size": self.queue.maxsize,
            "max_workers": self.max_workers,
            "interval_ms": self.interval_ms,
            "filter_config": self.filter_config,
            "user_agent": self.user_agent,
            "queue": list(self.queue.queue),
            "met_url_bf": self.met_url_bf,
            "saved_url_bf": self.saved_url_bf,
            "saved_content": self.saved_content,
        }
        return state_dict

    def save(self,
             ):
        """
        save the current state to the directory.
        :return:
        """
        with self.lock:
            logger.info(f"Saving crawler to {self.directory}")
            state_dict = self.as_state_dict()
            state_dict_to_save = {k: v for k, v in state_dict.items()
                                  if k not in ("met_url_bf", "saved_url_bf", "saved_content")}
            with open(osp.join(self.directory, "CrawlerParams.json"), "w") as f:
                json.dump(state_dict_to_save, f)

            self.met_url_bf.save_to(osp.join(self.directory, "met_urls"))
            self.saved_url_bf.save_to(osp.join(self.directory, "saved_urls"))
            self.saved_content.save()
            logger.info(f"Completed Saving crawler to {self.directory}")

    def make_snapshot(self,
                      snapshot_name: str,
                      ):
        """

        :return:
        """
        logger.info(f"Making snapshot {snapshot_name}")
        snapshot_dir = osp.join(self.directory, "snapshots")
        snapshot_inner_dir = osp.join(snapshot_dir, snapshot_name)
        os.makedirs(snapshot_inner_dir, exist_ok=True)
        with self.lock:
            state_dict = self.as_state_dict()
            state_dict_to_save = {k: v for k, v in state_dict.items()
                                  if k not in ("met_url_bf", "saved_url_bf", "saved_content")}
            with open(osp.join(snapshot_inner_dir, "CrawlerParams.json"), "w") as f:
                json.dump(state_dict_to_save, f)

            self.met_url_bf.save_to(osp.join(snapshot_inner_dir, "met_urls"))
            self.saved_url_bf.save_to(osp.join(snapshot_inner_dir, "saved_urls"))

            self.saved_content.make_snapshot(version_name=snapshot_name)

        logger.info(f"Completed making snapshot {snapshot_name}")

    @staticmethod
    def load(
            path: str,
    ):
        """
        load the crawler from the directory.
        :param path:
        :return:
        """
        logger.info(f"Loading crawler from {path}")

        with open(osp.join(path, "CrawlerParams.json"), "r") as f:
            state_dict = json.load(f)

        # state_dict["queue"] now is a list. convert it to a queue.Queue.
        _queue = queue.Queue(maxsize=state_dict["max_queue_size"])
        for url in state_dict["queue"]:
            _queue.put(url)

        state_dict["queue"] = _queue

        state_dict["met_url_bf"] = bf.BloomFilter.load_from(osp.join(path, "met_urls"))
        state_dict["saved_url_bf"] = bf.BloomFilter.load_from(osp.join(path, "saved_urls"))
        state_dict["saved_content"] = fs.FileSet.load_from(osp.join(path, "saved_files"), mode="append-full-load")

        return Crawler(state_dict=state_dict)

    @staticmethod
    def load_snapshot(
            path: str,
            snapshot_name: str,
    ):
        """
        load the crawler from the directory.
        :param path:
        :param snapshot_name:
        :return:
        """
        logger.info(f"Loading crawler from '{path}' snapshot '{snapshot_name}'")
        snapshot_dir = osp.join(path, "snapshots")
        snapshot_inner_dir = osp.join(snapshot_dir, snapshot_name)
        with open(osp.join(snapshot_inner_dir, "CrawlerParams.json"), "r") as f:
            state_dict = json.load(f)

        # state_dict["queue"] now is a list. convert it to a queue.Queue.
        _queue = queue.Queue(maxsize=state_dict["max_queue_size"])
        for url in state_dict["queue"]:
            _queue.put(url)

        state_dict["queue"] = _queue

        state_dict["met_url_bf"] = bf.BloomFilter.load_from(osp.join(snapshot_inner_dir, "met_urls"))
        state_dict["saved_url_bf"] = bf.BloomFilter.load_from(osp.join(snapshot_inner_dir, "saved_urls"))
        state_dict["saved_content"] = fs.FileSet.load_from_snapshot(snapshot_name, osp.join(path, "saved_files"))

        # replace the followings with what's in the snapshot
        # | CrawlerParams.json
        # | met_urls/ (BloomFilter)
        # | saved_urls/ (BloomFilter)
        shutil.copyfile(osp.join(snapshot_inner_dir, "CrawlerParams.json"), osp.join(path, "CrawlerParams.json"))
        shutil.rmtree(osp.join(path, "met_urls"))
        shutil.copytree(osp.join(snapshot_inner_dir, "met_urls"), osp.join(path, "met_urls"))
        shutil.rmtree(osp.join(path, "saved_urls"))
        shutil.copytree(osp.join(snapshot_inner_dir, "saved_urls"), osp.join(path, "saved_urls"))

        # clear newer snapshots
        snapshot_folders = os.listdir(snapshot_dir)
        for folder in snapshot_folders:
            if folder > snapshot_name:
                shutil.rmtree(osp.join(snapshot_dir, folder))

        return Crawler(state_dict=state_dict)

    # web request stuff

    def get_content(self, url) -> Optional[bytes]:
        content = request_utils.get_content(url, user_agent=self.user_agent)
        return content

    # file saving stuff

    def save_file(self,
                  content: bytes,
                  url: str,
                  title: str = None,
                  download_time: str = None,
                  ):
        _title = title if title is not None else "Untitled"
        _download_time = download_time if download_time is not None else fs.get_timestamp_string()
        entry = fs.as_insert_entry(content, url, _title, _download_time)
        self.saved_content.insert(entry)

    # status stuff
    def file_count(self,
                   ):
        return self.saved_content.recorded_entries.__len__()
