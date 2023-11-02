import logging
import os
import time

import lucene
from java.io import File
from org.apache.lucene.analysis.cjk import CJKAnalyzer
from org.apache.lucene.store import SimpleFSDirectory
from org.apache.lucene.queryparser.classic import QueryParser

from org.apache.lucene.search import IndexSearcher
from org.apache.lucene.index import DirectoryReader

Url = str


class HtmlIndexSearcher:
    def __init__(self, store_dir: str, ):
        self.directory = SimpleFSDirectory(File(store_dir).toPath())
        self.searcher = IndexSearcher(DirectoryReader.open(self.directory))
        self.analyzer = CJKAnalyzer()

    def query(self, command: str):
        logging.info(f"Searching for '{command}'")
        _query = QueryParser("contents", self.analyzer).parse(command)
        score_docs = self.searcher.search(_query, 200).scoreDocs

        _size = len(score_docs)

        logging.info(f"Found {_size} items.")

        time.sleep(0.2)

        _display_size = min(10, _size)

        for i, score_doc in enumerate(score_docs[:_display_size]):
            doc = self.searcher.doc(score_doc.doc)
            try:
                print(f"Item {i + 1}:")
                print(f'path:\t{doc.get("path")}')
                print(f'name:\t{doc.get("name")}', )
                print(f"url:\t{doc.get('url')}", )
                print(f"title:\t{doc.get('title')}", )
                print(f"Score:\t{score_doc.score}")
                print('------')
            except:
                continue

        time.sleep(0.5)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s.%(msecs)03d [%(levelname)s] %(message)s",
                        datefmt="%H:%M:%S")

    print(os.getcwd())

    lucene.initVM()

    searcher = HtmlIndexSearcher(store_dir="./lucene_index/")

    command = ''
    while True:
        command = input("Search command: ")
        # command = "sjtu"
        if command == "":
            continue

        if command == "q":
            break

        searcher.query(command)

    del searcher

