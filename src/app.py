# SJTU EE208

#from searchIndex import HtmlIndexSearcher
import hashlib
import random
import string

from flask import Flask, redirect, render_template, request, url_for
from markupsafe import escape

app = Flask(__name__)

class SearchResult:
    def __init__(self, title, url="https://www.example.com", date="2023-12-17", content="news content here "*10):
        self.title = title
        self.url = url
        self.date = date
        self.content = content

def getHotNews():
    ret = []
    for i in range(1, 7):
        news = SearchResult("title" + str(i))
        ret.append(news)
    return ret

def getResults(searchword):
    ret = []
    for i in range(1, 11):
        news = SearchResult("title" + str(i))
        ret.append(news)
    return ret


@app.route('/', methods=['POST', 'GET'])
def search_form():
    if request.method == "POST":
        return redirect(url_for('show_result'))
    hot_news = getHotNews()
    left_column = hot_news[:3]
    right_column = hot_news[3:]
    return render_template("search.html", hashcode=get_sha1("static/search.css"), left_column=left_column, right_column=right_column)


@app.route('/result', methods=['POST', 'GET'])
def show_result():
    searchword = request.args.get('keyword')
    results = getResults(searchword)
    lens = [i for i in range(len(results))]
    if request.method == 'POST':
        keyword = request.form['keyword']
        return redirect(url_for('show_result', keyword=keyword))
    return render_template("show_result.html", searchword=searchword, results=results, lens=lens, hashcode=get_sha1("static/result.css"))

def get_sha1(filename):
    with open(filename, "rb") as f:
        sha1obj = hashlib.sha1()
        sha1obj.update(f.read())
    return sha1obj.hexdigest()

if __name__ == '__main__':
    #searcher = HtmlIndexSearcher(store_dir="./lucene_index/")
    app.run(debug=True, port=8080)