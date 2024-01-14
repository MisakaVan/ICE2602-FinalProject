import sys, os, lucene
import math
from java.io import File
from org.apache.lucene.analysis.cjk import CJKAnalyzer
from org.apache.lucene.index import DirectoryReader
from org.apache.lucene.queryparser.classic import QueryParser
from org.apache.lucene.store import SimpleFSDirectory
from org.apache.lucene.search import IndexSearcher
from org.apache.lucene.util import Version
from org.apache.pylucene.search.similarities import PythonSimilarity, PythonClassicSimilarity

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


def run(searcher, analyzer):
    while True:
        print()
        print("Hit enter with no input to quit.")
        command = input("Query:")
        if command == '':
            return

        print()
        print("Searching for:", command)
        query = QueryParser("content", analyzer).parse(command)
        scoreDocs = searcher.search(query, 50).scoreDocs
        print("%s total matching documents." % len(scoreDocs))

        for i, scoreDoc in enumerate(scoreDocs):
            doc = searcher.doc(scoreDoc.doc)
            try:
                print("url:", doc.get("url"))
                print()
                print("title:", doc.get("title"))
                print()
                print("date:", doc.get("date"))
                print()
                print("content:", doc.get("content"))
                print()
                print("Image URLs:")
                print()
                print("First Image:", doc.get("img_first"))
                print()
                print("All Images:", doc.get("img_all"))
                print()
                
                print()
                print('------------------------------------------')
                print()
            except:
                continue

if __name__ == '__main__':
    STORE_DIR = "myIndex"  # 指定新创建的Index文件夹路径
    lucene.initVM(vmargs=['-Djava.awt.headless=true'])
    print('lucene', lucene.VERSION)
    directory = SimpleFSDirectory(File(STORE_DIR).toPath())
    searcher = IndexSearcher(DirectoryReader.open(directory))
    # 设置新的相似度计算方法
    searcher.setSimilarity(SimpleSimilarity())
    analyzer = CJKAnalyzer()
    run(searcher, analyzer)
    del searcher
