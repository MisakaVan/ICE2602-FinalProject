import logging
import os
import time
from collections import defaultdict
from typing import Dict

import lucene
from java.io import File
from org.apache.lucene.analysis.cjk import CJKAnalyzer
from org.apache.lucene.index import DirectoryReader
from org.apache.lucene.queryparser.classic import QueryParser
from org.apache.lucene.search import IndexSearcher
from org.apache.lucene.store import SimpleFSDirectory
from org.apache.lucene.index import DirectoryReader
from org.apache.lucene.search import BooleanQuery
from org.apache.lucene.search import BooleanClause
Url = str


class HtmlIndexSearcher:
    def __init__(self, store_dir: str, ):
        self.directory = SimpleFSDirectory(File(store_dir).toPath())
        self.searcher = IndexSearcher(DirectoryReader.open(self.directory))
        self.analyzer = CJKAnalyzer()

    def parse_command(self, command: str) -> Dict[str, str]:
        default_option = "contents"
        available_options = ["contents", "site"]
        ret = defaultdict(str)
        slices = command.split(" ")
        cur_option = default_option
        for piece in slices:
            if ":" not in piece:
                to_append = piece
            else:
                cur_option, _piece = piece.split(":")[:2]
                to_append = _piece

            if cur_option in available_options:
                if ret[cur_option]:
                    ret[cur_option] += " "
                ret[cur_option] += to_append

        return ret

    def query(self, command: str):
        logging.info(f"Searching for '{command}'")
        _query_dict = self.parse_command(command)

        logging.info(f"Query as dict: {_query_dict}")

        _querys = BooleanQuery.Builder()
        for k, v in _query_dict.items():
            _querys.add(
                QueryParser(k, self.analyzer).parse(v),
                BooleanClause.Occur.MUST
            )

        # _query = QueryParser("contents", self.analyzer).parse(command)
        score_docs = self.searcher.search(_querys.build(), 200).scoreDocs

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
