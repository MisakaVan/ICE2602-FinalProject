import logging
import os
import re
import urllib.parse
from pathlib import Path
from typing import Dict, List, Tuple
from tqdm import tqdm
import urllib.parse as parse

import lucene
from bs4 import BeautifulSoup, NavigableString
# from java.io import File
from java.nio.file import Paths
from org.apache.lucene.analysis.miscellaneous import LimitTokenCountAnalyzer
from org.apache.lucene.analysis.cjk import CJKAnalyzer
from org.apache.lucene.document import Document, Field, FieldType
from org.apache.lucene.index import IndexWriter, IndexWriterConfig, IndexOptions
from org.apache.lucene.store import SimpleFSDirectory



Url = str
MAX_IMG_COUNT = 20000

class ImgIndexer:
    def __init__(self,
                 store_dir: str,
                 source_index: str,
                 source_dir: str,
                 max_image_count: int = MAX_IMG_COUNT):
        if not os.path.exists(source_dir):
            logging.error(f"Source dir {source_dir} does not exist.")
            raise FileNotFoundError()
        if not os.path.exists(source_index):
            logging.error(f"Source index {source_index} does not exist.")
            raise FileNotFoundError()

        self.source_index = Path(source_index)
        self.source_dir = Path(source_dir)
        self.max_image_count = max_image_count

        if not os.path.exists(store_dir):
            os.mkdir(store_dir)

        store = SimpleFSDirectory(Paths.get(store_dir))
        analyzer = LimitTokenCountAnalyzer(CJKAnalyzer(), 1048576)
        config = IndexWriterConfig(analyzer)
        config.setOpenMode(IndexWriterConfig.OpenMode.CREATE)

        self.writer = IndexWriter(store, config)

        self.html_dict: Dict[Path, Url] = dict()
        self.__parse_index_from_crawler()
        pass

    def __parse_index_from_crawler(self):
        """
        Updates self.html_dict according to the
        "index.txt" created by the crawler.
        """
        with open(self.source_index, "r") as index_from_crawler:
            indices: List[Url, Path] = index_from_crawler.readlines()
            for line in indices:
                try:
                    _url, _filename = line.strip().split("\t")
                except:
                    pass
                else:
                    self.html_dict[_filename] = _url


    def __parse_img_and_description(self, soup, home_url:Url)->List[Tuple[Url, str]]:
        min_desc_len = 20
        http_filter = re.compile("^https?://")
        img_file_filter = re.compile(".*\\.(jpg|jpeg|png|JPG|JPEG|PNG|svg|SVG)")
        ret = []
        for tag in soup.find_all("img"):
            # Parse the image source
            raw_src = tag.get("src", "")
            if raw_src == "":
                continue
            abs_url = urllib.parse.urljoin(home_url, raw_src)
            result1 = http_filter.match(abs_url)
            result2 = img_file_filter.match(abs_url)
            result = result1 and result2
            if not result:
                # Not a valid source
                continue

            # Deduce description by the context of the tag
            some_img_tag = tag
            l_tag = some_img_tag.previous_sibling
            r_tag = some_img_tag.next_sibling
            description = some_img_tag.get("alt", "")

            while len(description) < min_desc_len:
                if l_tag is not None:
                    # print(type(l_tag))
                    if isinstance(l_tag, NavigableString):
                        description += l_tag
                    else:
                        try:
                            description += " ".join(l_tag.stripped_strings).strip()
                        except:
                            pass
                    l_tag = l_tag.previous_sibling

                if r_tag is not None:
                    # print(type(r_tag))
                    if isinstance(r_tag, NavigableString):
                        description += r_tag
                    else:
                        try:
                            description += " ".join(r_tag.stripped_strings).strip()
                        except:
                            pass
                    r_tag = r_tag.next_sibling

                if l_tag is None and r_tag is None:
                    some_img_tag = some_img_tag.parent
                    if some_img_tag is None:
                        break
                    l_tag = some_img_tag.previous_sibling
                    r_tag = some_img_tag.next_sibling
                description = description.strip("\n")

            description += " " + abs_url
            ret.append((abs_url, description))

        logging.debug(f"Found {len(ret)} imgs in {home_url}")
        return ret

    def run(self):
        t1 = FieldType()
        t1.setStored(True)
        t1.setTokenized(False)
        t1.setIndexOptions(IndexOptions.NONE)  # Not Indexed

        t2 = FieldType()
        t2.setStored(False)
        t2.setTokenized(True)
        t2.setIndexOptions(IndexOptions.DOCS_AND_FREQS_AND_POSITIONS)  # Indexes documents, frequencies and positions.

        cnt = 0

        for _filename, url in self.html_dict.items():
            if cnt >= self.max_image_count:
                break
            logging.info(f"{cnt} images found")
            _r_filename = self.source_dir / _filename
            logging.debug(f"Processing {_r_filename}")
            try:
                with open(_r_filename, "rb") as html_file:
                    content = html_file.read()

                soup = BeautifulSoup(content.decode("utf-8", errors="ignore"), "html.parser")

                # todo
                try:
                    title = soup.title.string.strip()
                except:
                    logging.debug(f"File {_filename} has no title")
                    title = "<MissingTitle>"

                imgs = self.__parse_img_and_description(soup, url)

                for img, description in imgs:
                    logging.debug(f"Adding img: {img}, desc length {len(description)}.")
                    doc = Document()
                    doc.add(Field("title", title, t1))
                    doc.add(Field("url", url, t1))
                    doc.add(Field("imgurl", img, t1))
                    doc.add(Field("description", description, t2))

                    self.writer.addDocument(doc)
                    cnt += 1
            except Exception as e:
                logging.debug(f"Failed processing {_filename}: {e}")
                # raise e
        self.writer.commit()
        self.writer.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s.%(msecs)03d [%(levelname)s] %(message)s",
                        datefmt="%H:%M:%S")

    print(os.getcwd())

    html_index_file = "./Crawler_lab3/cache/index.txt"
    html_cache_dir = "./Crawler_lab3/cache/html/"
    store_dir = "./lucene_img_index"

    if not os.path.exists(store_dir):
        os.mkdir(store_dir)

    lucene.initVM()

    indexer = ImgIndexer(store_dir=store_dir,
                          source_dir=html_cache_dir,
                          source_index=html_index_file)

    indexer.run()
    # indexer.writer.commit()
    # indexer.writer.close()
