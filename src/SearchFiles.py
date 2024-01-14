import math
import os
import sys

import lucene
from flask import jsonify
from java.io import File
from org.apache.lucene.analysis.cjk import CJKAnalyzer
from org.apache.lucene.index import DirectoryReader
from org.apache.lucene.queryparser.classic import QueryParser
from org.apache.lucene.search import (BooleanClause, BooleanQuery, Explanation,
                                      IndexSearcher)
from org.apache.lucene.store import SimpleFSDirectory
from org.apache.lucene.util import Version
from org.apache.pylucene.search.similarities import (PythonClassicSimilarity,
                                                     PythonSimilarity)


class SimpleSimilarity(PythonClassicSimilarity):
    def lengthNorm(self, numTerms):
        return 1/math.sqrt(numTerms)

    def tf(self, freq):
        return freq

    def sloppyFreq(self, distance):
        return math.exp(-distance)

    def idf(self, docFreq, numDocs):
        return (numDocs/docFreq)

    def idfExplain(self, collectionStats, termStats):
        return Explanation.match(self.idf(termStats.docFreq(),collectionStats.numDocs()), "inexplicable", [])

def search_documents(keyword, searcher, analyzer):
    result = []
    print("Searching for:", keyword)

    # 为内容字段创建查询
    query = QueryParser("content", analyzer).parse(keyword)
    scoreDocs = searcher.search(query, 50).scoreDocs

    # for scoreDoc in scoreDocs:
    for i, scoreDoc in enumerate(scoreDocs):
        doc = searcher.doc(scoreDoc.doc)
        try:
            document = {
                "url": doc.get("url"),
                "title": doc.get("title"),
                "date": doc.get("date"),
                "content": doc.get("content"),
                "First Image": doc.get("img_first"),
                "All Images": doc.get("img_all")
            }
            result.append(document)
        except:
            continue

    return result

def search_api(keyword):

    vm_env.attachCurrentThread()
    directory = SimpleFSDirectory(File(STORE_DIR).toPath())
    searcher = IndexSearcher(DirectoryReader.open(directory))
    searcher.setSimilarity(SimpleSimilarity())
    analyzer = CJKAnalyzer()

    result = search_documents(keyword, searcher, analyzer)

    del searcher
    vm_env.detachCurrentThread()

    return jsonify({"results": result})

vm_env = lucene.initVM(vmargs=['-Djava.awt.headless=true'])
STORE_DIR = "myIndex"
