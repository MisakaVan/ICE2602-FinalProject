import lucene
import math
from org.apache.pylucene.search.similarities import PythonClassicSimilarity


class Similarity1(PythonClassicSimilarity):

    def lengthNorm(self, numTerms):
        return 1 / math.sqrt(numTerms)

    def tf(self, freq):
        return math.log(1 + freq)

    def sloppyFreq(self, distance):
        return math.exp(-distance)

    def idf(self, docFreq, numDocs):
        return math.log(numDocs / docFreq)

    def idfExplain(self, collectionStats, termStats):
        return Explanation.match(self.idf(termStats.docFreq(), collectionStats.numDocs()), "inexplicable", [])


class Similarity2(PythonClassicSimilarity):

    def lengthNorm(self, numTerms):
        return 1 / math.sqrt(numTerms)

    def tf(self, freq):
        return math.sqrt(1 + freq)

    def sloppyFreq(self, distance):
        return 1 / (1 + distance)

    def idf(self, docFreq, numDocs):
        return numDocs / docFreq

    def idfExplain(self, collectionStats, termStats):
        return Explanation.match(self.idf(termStats.docFreq(), collectionStats.numDocs()), "inexplicable", [])

if __name__ == "__main__":
    lucene.initVM()
    sim = Similarity1()
