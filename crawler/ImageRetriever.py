"""

Saves all the images that are found in the given FileSet of htmls.

File structure under its directory:

| images/ (the folder where all the images are saved)
|
| state.json (the file that stores the state of the ImageRetriever)

State to be stored:
- To which entry in the FileSet the ImageRetriever has processed. (int)
- The list of failed urls. (list[str])



"""
import json
import os.path as osp
import os
import shutil
import time
import urllib.parse
import urllib.request
from collections import namedtuple
from typing import Optional

import requests

import loguru

import FileSet as fs
import request_utils as ru

logger = loguru.logger

INTERVAL_SEC = 0.2
GET_TIMEOUT_SEC = 1.0


class ImageRetriever:
    directory: str
    fileset_directory: str
    done_count: int
    failed: list[str]
    excluded_extensions: list[str]
    excluded_hosts: list[str]

    def __init__(self,
                 directory=None,
                 fileset_directory=None,
                 excluded_extensions=None,
                 excluded_hosts=None,
                 state_dict=None,
                 load_fileset=True,
                 ):
        if excluded_extensions is None:
            excluded_extensions = []

        if excluded_hosts is None:
            excluded_hosts = []

        if state_dict is None:
            self.directory = directory
            self.fileset_directory = fileset_directory
            self.done_count = 0
            self.failed_urls = []
            self.excluded_extensions = excluded_extensions
            self.excluded_hosts = excluded_hosts
        else:
            self.directory = state_dict['directory']
            self.fileset_directory = state_dict['fileset_directory']
            self.done_count = state_dict['done_count']
            self.failed_urls = state_dict['failed_urls']
            self.excluded_extensions = state_dict['excluded_extensions']
            self.excluded_hosts = state_dict['excluded_hosts']

        self.image_directory = osp.join(self.directory, 'images')

        if state_dict is None:
            self._init_directory()

        if self.fileset_directory is not None and load_fileset:
            # None means this ImageRetriever is only used for reading.
            # Not None means this ImageRetriever is to be run.
            self.fileset = fs.FileSet.load_from(self.fileset_directory,
                                                mode='append-full-load', )

        logger.info(f'ImageRetriever {"initialized" if state_dict is None else "loaded"}: {self}')

    def __repr__(self):
        return f"ImageRetriever(directory={self.directory}, fileset_directory={self.fileset_directory}, " \
               f"done_count={self.done_count}, failed_urls_count={len(self.failed_urls)}, " \
               f"excluded_extensions={self.excluded_extensions}, excluded_hosts={self.excluded_hosts})"

    def get_location(self, image_src) -> Optional[str]:
        """
        根据给定的image_src，返回其在本地的路径。
        如果该文件没有被保存，返回None。

        注：理论上来说，只要是在对应FileSet中的entry中的网页中出现过的image_src，
        就可以调用这个函数，不用对image_src做去除fragment、去除query的操作。

        :param image_src:
        :return:
        """

        path_and_dir = self.concat_file_path_and_directory(image_src)

        if osp.isfile(path_and_dir.path):
            return path_and_dir.path
        else:
            return None

    def run(self, iterations=None):
        cur_done_count = self.done_count
        this_count = 0

        for entry_index in range(cur_done_count, len(self.fileset)):
            logger.info(f'Processing entry {entry_index:4d}...')
            entry: fs.FileSetRecordedEntry = self.fileset.recorded_entries[entry_index]

            self._process_entry(entry)

            self.done_count += 1
            this_count += 1
            if iterations is not None and this_count >= iterations:
                break

        self.save()

    def retry_failed(self):
        """
        Retry failed urls. If an url is successfully crawled, it will be removed from the failed list.
        :return:
        """
        cur_failed_urls = self.failed_urls
        new_failed_urls = []

        for image_src in cur_failed_urls:
            logger.info(f'Retrying failed url {image_src}...')
            path_and_dir = self.concat_file_path_and_directory(image_src)

            # crawl the image
            try:
                r = requests.get(image_src, timeout=GET_TIMEOUT_SEC)
                if r.status_code != 200:
                    raise Exception(f"status code is {r.status_code}")
                content = r.content
                ext = r.headers['Content-Type'].split('/')[1]
            except Exception as e:
                logger.error(f"Exception: {e} with url {image_src}")
                new_failed_urls.append(image_src)

                time.sleep(INTERVAL_SEC)
                continue

            os.makedirs(path_and_dir.dir, exist_ok=True)
            with open(path_and_dir.path, 'wb') as f:
                f.write(content)
            logger.info(f"Saved image {image_src} to {path_and_dir.path}")
            time.sleep(INTERVAL_SEC)

        self.failed_urls = new_failed_urls
        self.save()

    def _process_entry(self, entry: fs.FileSetRecordedEntry, skip_failed=False):
        filename = entry.content_filename
        url = entry.url
        filepath = osp.join(self.fileset_directory, 'contents', filename)
        with open(filepath, 'rb') as f:
            content = f.read()

        new_image_srcs = set(ru.parse_all_img_src(content, url))

        filtered_image_srcs = set(filter(self._filter, new_image_srcs))

        unsaved_image_srcs = set(
            filter(lambda x: not osp.isfile(self.concat_file_path_and_directory(x).path), filtered_image_srcs))

        logger.info(f"{len(filtered_image_srcs)} images left after filtering, {len(unsaved_image_srcs)} are new.")

        for image_src in unsaved_image_srcs:
            path_and_dir = self.concat_file_path_and_directory(image_src)

            # # if the file already exists, skip it.
            # if osp.isfile(path_and_dir.path):
            #     continue

            # if the file is in the failed list, skip it.
            if skip_failed and image_src in self.failed_urls:
                continue

            # crawl the image
            try:
                r = requests.get(image_src, timeout=GET_TIMEOUT_SEC)
                if r.status_code != 200:
                    raise Exception(f"status code is {r.status_code}")
                content = r.content
                ext = r.headers['Content-Type'].split('/')[1]
            except Exception as e:
                logger.error(f"Exception: {e} with url {image_src}")
                self.failed_urls.append(image_src)
                time.sleep(INTERVAL_SEC)
                continue

            os.makedirs(path_and_dir.dir, exist_ok=True)
            with open(path_and_dir.path, 'wb') as f:
                f.write(content)
            logger.info(f"Saved image {image_src} to {path_and_dir.path}")
            time.sleep(INTERVAL_SEC)

    def _filter(self, url):
        parse_result = urllib.parse.urlparse(url)
        if parse_result.netloc in self.excluded_hosts:
            return False
        ext = parse_result.path.split('/')[-1].split('.')[-1].lower()
        if ext in self.excluded_extensions:
            return False
        return True

    def concat_file_path_and_directory(self, image_src):
        """
        根据给定的image_src，假如它被保存在本地，返回其在本地的路径和所在的文件夹。
        :param image_src:
        :return:
        """
        parse_result = urllib.parse.urlparse(image_src)

        _netloc = parse_result.netloc
        _path = parse_result.path[1:] if parse_result.path.startswith('/') else parse_result.path

        full_path = osp.join(self.image_directory, _netloc, _path)
        full_dir = osp.dirname(full_path)

        return namedtuple('PathAndDir', ['path', 'dir'])(full_path, full_dir)

    def as_state_dict(self):
        return {
            'directory': self.directory,
            'fileset_directory': self.fileset_directory,
            'done_count': self.done_count,
            'excluded_extensions': self.excluded_extensions,
            'excluded_hosts': self.excluded_hosts,
            'failed_urls': self.failed_urls,
        }

    def save(self):
        with open(osp.join(self.directory, 'state.json'), 'w') as f:
            json.dump(self.as_state_dict(), f, indent=2)
        logger.info(f"ImageRetriever saved to {self.directory}")

    @staticmethod
    def load_from(directory, load_fileset=True):
        with open(osp.join(directory, 'state.json'), 'r') as f:
            state_dict = json.load(f)
        return ImageRetriever(state_dict=state_dict, load_fileset=load_fileset)

    def _init_directory(self):
        # clear the directory
        if osp.exists(self.directory):
            shutil.rmtree(self.directory, ignore_errors=True)

        os.makedirs(self.image_directory, exist_ok=True)


too_large_extensions = ['gif']

bad_hosts = ['p.v.iask.com']


@logger.catch()
def retrieve_sina(epoch=5, batch_size=100):
    directory = './image_sina_cache'
    crawler_cache_directory = './crawler_test_cache'
    fileset_directory = osp.join(crawler_cache_directory, 'saved_files')

    # d_image_retriever = ImageRetriever(directory=directory,
    #                                    fileset_directory=fileset_directory,
    #                                    excluded_extensions=too_large_extensions.copy(),
    #                                    excluded_hosts=bad_hosts.copy(),
    #                                    )
    # d_image_retriever.save()

    # test the ImageRetriever's _filter

    # res = list(filter(d_image_retriever._filter, ['https://p.v.iask.com/138/950/165/1150000165_1.gif?foo=bar']))
    #
    # print(res)

    image_retriever = ImageRetriever.load_from(directory)

    for _ in range(epoch):
        logger.info(f"Epoch {_}")
        start_time = time.time()
        image_retriever.run(iterations=batch_size)
        image_retriever.save()
        logger.info(f"Epoch {_} done. Time used: {time.time() - start_time:.3f} secs. Current state: {image_retriever}")


@logger.catch()
def retry_failed_sina():
    directory = './image_sina_cache'
    image_retriever = ImageRetriever.load_from(directory)
    image_retriever.retry_failed()
    image_retriever.save()


@logger.catch()
def retrieve_zhibo8(epoch=5, batch_size=100):
    directory = './image_zhibo8_cache'
    crawler_cache_directory = './crawler_zhibo8_cache'
    fileset_directory = osp.join(crawler_cache_directory, 'saved_files')

    # d_image_retriever = ImageRetriever(directory=directory,
    #                                  fileset_directory=fileset_directory,
    #                                  excluded_extensions=too_large_extensions.copy(),
    #                                  excluded_hosts=bad_hosts.copy(),
    #                                  )
    # d_image_retriever.save()

    image_retriever = ImageRetriever.load_from(directory)

    for _ in range(epoch):
        logger.info(f"Epoch {_}")
        start_time = time.time()
        image_retriever.run(iterations=batch_size)
        image_retriever.save()
        logger.info(f"Epoch {_} done. Time used: {time.time() - start_time:.3f} secs. Current state: {image_retriever}")


if __name__ == '__main__':
    # retrieve_sina(epoch=70, batch_size=100)
    # retry_failed_sina()
    retrieve_zhibo8(epoch=40, batch_size=100)
