import queue
import sys
import os.path as osp
import os

import random

import Crawler
import loguru
from FileSet import get_snapshot_name

logger = loguru.logger


@logger.catch()
def start_crawler(seed):
    #
    # d_crawler = Crawler.Crawler(directory="./crawler_test_cache",
    #                             max_workers=4,
    #                             interval_ms=4000,
    #                             filter_config="sina")
    # d_crawler.save()

    cache_path = "./crawler_test_cache"

    d_crawler = Crawler.Crawler(directory=cache_path,
                                max_workers=8,
                                interval_ms=3600,
                                met_url_bf_capacity=1000000,
                                saved_url_bf_capacity=1000000,
                                filter_config="sina")
    d_crawler.queue.put(seed)
    d_crawler.run(epoch_count=1, secs=10, make_snapshot=True)
    d_crawler.save()


@logger.catch()
def resume_crawler(cache_path="./crawler_test_cache", epoch_count=30, secs=180):
    # find the latest snapshot
    snapshot_dir = osp.join(cache_path, "snapshots")
    snapshot_list = os.listdir(snapshot_dir)
    snapshot_list.sort()
    latest_snapshot_name = snapshot_list[-1]

    crawler = Crawler.Crawler.load_snapshot(path=cache_path, snapshot_name=latest_snapshot_name)
    crawler.run(epoch_count=epoch_count, secs=secs, make_snapshot=True)

    crawler.save()


@logger.catch()
def start_zhibo8_crawler():
    cache_path = "./crawler_zhibo8_cache"

    d_crawler = Crawler.Crawler(directory=cache_path,
                                max_workers=3,
                                interval_ms=4800,
                                met_url_bf_capacity=1000000,
                                saved_url_bf_capacity=1000000,
                                filter_config="zhibo8",
                                max_queue_size=4000,
                                )
    d_crawler.queue.put(Crawler.zhibo8_seeds_quoted[0])
    d_crawler.queue.put(Crawler.zhibo8_seeds_quoted[1])
    d_crawler.queue.put(Crawler.zhibo8_seeds_quoted[-1])

    d_crawler.run(epoch_count=2, secs=10, make_snapshot=True)

    d_crawler.save()


@logger.catch()
def resume_zhibo8_crawler(cache_path="./crawler_zhibo8_cache", epoch_count=30, secs=180):
    # find the latest snapshot
    snapshot_dir = osp.join(cache_path, "snapshots")
    snapshot_list = os.listdir(snapshot_dir)
    snapshot_list.sort()
    latest_snapshot_name = snapshot_list[-1]

    crawler = Crawler.Crawler.load_snapshot(path=cache_path, snapshot_name=latest_snapshot_name)

    crawler.max_workers = 8
    crawler.interval_ms = 4000

    # add a random seed to the queue
    seeds = Crawler.zhibo8_seeds_quoted
    for out_epoch in range(epoch_count):

        for _ in range(5):
            random_seed = random.choice(seeds)
            try:
                crawler.queue.put(random_seed, block=False)
            except queue.Full:
                pass


        crawler.run(epoch_count=1, secs=secs, make_snapshot=True, start_epoch=out_epoch)

        crawler.save()


if __name__ == "__main__":
    logger.remove()
    logger.add(sink=sys.stderr, level="INFO", enqueue=True)

    # start_crawler(seed="https://sports.sina.com.cn/global/")

    # resume_crawler(epoch_count=10, secs=300)

    # start_zhibo8_crawler()

    resume_zhibo8_crawler(epoch_count=20, secs=120)
