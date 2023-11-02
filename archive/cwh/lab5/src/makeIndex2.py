import logging
import os
import urllib.parse
from pathlib import Path
from typing import Dict, List
from tqdm import tqdm

import lucene
from bs4 import BeautifulSoup
# from java.io import File
from java.nio.file import Paths
from org.apache.lucene.analysis.miscellaneous import LimitTokenCountAnalyzer
from org.apache.lucene.analysis.cjk import CJKAnalyzer
from org.apache.lucene.document import Document, Field, FieldType
from org.apache.lucene.index import IndexWriter, IndexWriterConfig, IndexOptions
from org.apache.lucene.store import SimpleFSDirectory

Url = str


class HtmlIndexer:
    def __init__(self,
                 store_dir: str,
                 source_index: str,
                 source_dir: str):
        if not os.path.exists(source_dir):
            logging.error(f"Source dir {source_dir} does not exist.")
            raise FileNotFoundError()
        if not os.path.exists(source_index):
            logging.error(f"Source index {source_index} does not exist.")
            raise FileNotFoundError()

        self.source_index = Path(source_index)
        self.source_dir = Path(source_dir)

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

    def run(self):
        t1 = FieldType()
        t1.setStored(True)
        t1.setTokenized(False)
        t1.setIndexOptions(IndexOptions.NONE)  # Not Indexed

        t2 = FieldType()
        t2.setStored(False)
        t2.setTokenized(True)
        t2.setIndexOptions(IndexOptions.DOCS_AND_FREQS_AND_POSITIONS)  # Indexes documents, frequencies and positions.

        for _filename, url in tqdm(self.html_dict.items()):
            _r_filename = self.source_dir / _filename
            logging.debug(f"Processing {_r_filename}")
            try:
                with open(_r_filename, "rb") as html_file:
                    content = html_file.read()

                soup = BeautifulSoup(content.decode("utf-8", errors="ignore"), "html.parser")

                try:
                    title = soup.title.string.strip()
                except:
                    logging.debug(f"File {_filename} has no title")
                    title = "<MissingTitle>"

                try:
                    hostname = urllib.parse.urlparse(url).hostname
                except:
                    logging.debug(f"Url {url} has no hostname. WHY?")
                    hostname = "<MissingHostname>"

                _tokenized_hostname = hostname.replace(".", " . ")

                doc = Document()
                doc.add(Field("name", _filename.__str__(), t1))
                doc.add(Field("path", _r_filename.__str__(), t1))
                doc.add(Field("title", title, t1))
                doc.add(Field("site", hostname, t1))
                doc.add(Field("url", url, t1))
                doc.add(Field("site", _tokenized_hostname, t2))

                text = ''.join(soup.findAll(text=True))

                logging.debug(f"{_filename} has content size {len(text)}")

                doc.add(Field("contents", text, t2))

                self.writer.addDocument(doc)
            except Exception as e:
                logging.debug(f"Failed processing {_filename}: {e}")
                # raise e


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s.%(msecs)03d [%(levelname)s] %(message)s",
                        datefmt="%H:%M:%S")

    print(os.getcwd())

    html_index_file = "./Crawler_lab3/cache/index.txt"
    html_cache_dir = "./Crawler_lab3/cache/html/"
    store_dir = "./lucene_index"

    if not os.path.exists(store_dir):
        os.mkdir(store_dir)

    lucene.initVM()

    indexer = HtmlIndexer(store_dir=store_dir,
                          source_dir=html_cache_dir,
                          source_index=html_index_file)

    indexer.run()
    indexer.writer.commit()
    indexer.writer.close()
