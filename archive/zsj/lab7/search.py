# SJTU EE208

import sys, os, lucene

from java.io import File
from org.apache.lucene.analysis.standard import StandardAnalyzer
from org.apache.lucene.index import DirectoryReader
from org.apache.lucene.queryparser.classic import QueryParser
from org.apache.lucene.store import SimpleFSDirectory
from org.apache.lucene.search import IndexSearcher
from org.apache.lucene.util import Version
from org.apache.lucene.analysis.cjk import CJKAnalyzer
from org.apache.lucene.analysis.core import WhitespaceAnalyzer
import jieba

"""
This script is loosely based on the Lucene (java implementation) demo class 
org.apache.lucene.demo.SearchFiles.  It will prompt for a search query, then it
will search the Lucene index in the current directory called 'index' for the
search query entered against the 'contents' field.  It will then display the
'path' and 'name' fields for each of the hits it finds in the index.  Note that
search.close() is currently commented out because it causes a stack overflow in
some cases.
"""
def _run(searcher, analyzer, command):
    keyword_search = _content_cut(command)
    query = QueryParser("contents", analyzer).parse(keyword_search)
    scoreDocs = searcher.search(query, 50).scoreDocs

    cnt = 0
    title_list = []
    url_list = []
    content_list = []
    for i, scoreDoc in enumerate(scoreDocs):
        if cnt == 10:
            break
        doc = searcher.doc(scoreDoc.doc)
        title = doc.get("title")
        url = doc.get("url").strip('\'')
        name = doc.get("filename")
        content = _find_keyword(name, keyword_search)
        if title == "" or url == "" or content == "":
            continue
        title_list.append(title)
        url_list.append(url)
        content_list.append(content)
        cnt += 1
    return title_list, url_list, content_list

def _content_cut(content):
    seg_list = jieba.cut_for_search(content)
    return " ".join(seg_list)

def _find_keyword(name, keyword_search):
    keyword_list = keyword_search.split()
    keyword_list = sorted(keyword_list, key=lambda x:-len(x))
    cnt = 0
    i = 0
    file = open(os.path.join('html', name), 'r')
    content = file.read()
    content.replace("\n", "")
    content.replace(" ", "")
    content.replace("\t", "")
    ret = ""
    while(i != len(keyword_list) and cnt < 2):
        keyword = keyword_list[i]
        idx = content.find(keyword)
        if idx == -1:
            i += 1
            continue
        start_idx = max(0, idx-15)
        end_idx = min(len(content), idx+15)
        key_str = content[start_idx:end_idx]
        ret += "..." + key_str + "..." + "\n"
        i += 1
        cnt += 1
    return ret
    

def run(command):
    global searcher, analyzer, vm_env, is_init
    if not is_init:
        searcher, analyzer, vm_env = _init()
        is_init = True
    vm_env.attachCurrentThread()
    ret = _run(searcher, analyzer, command)
    vm_env.detachCurrentThread()
    return ret

def _init():
    STORE_DIR = "index"
    vm_env = lucene.initVM(vmargs=['-Djava.awt.headless=true'])

    directory = SimpleFSDirectory(File(STORE_DIR).toPath())
    searcher = IndexSearcher(DirectoryReader.open(directory))
    analyzer = WhitespaceAnalyzer()
    return searcher, analyzer, vm_env

searcher = ""
analyzer = ""
vm_env = ""
is_init = False

if __name__ == "__main__":
    s = input()
    print(run(s))