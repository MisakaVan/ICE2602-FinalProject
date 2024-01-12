import sys

import Crawler
import loguru
from FileSet import get_snapshot_name
logger = loguru.logger


@logger.catch()
def test_load():
    crawler = Crawler.Crawler(directory="./crawler_test_cache")
    crawler.save()

    crawler = Crawler.Crawler.load(path="./crawler_test_cache")

    for k, v in crawler.as_state_dict().items():
        print(f"{k} : {v}")

@logger.catch()
def test_make_snapshot():
    crawler = Crawler.Crawler.load(path="./crawler_test_cache")

    snapshot_name = get_snapshot_name()
    crawler.make_snapshot(snapshot_name)



if __name__ == "__main__":
    logger.remove()
    logger.add(sink=sys.stderr, level="INFO", enqueue=True)

    # test_load()
    test_make_snapshot()


