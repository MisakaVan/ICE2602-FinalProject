# SJTU EE208

from flask import Flask, redirect, render_template, request, url_for
from markupsafe import escape
from searchIndex import HtmlIndexSearcher
import hashlib

app = Flask(__name__)


@app.route('/', methods=['POST', 'GET'])
def search_form():
    if request.method == "POST":
        ky = request.form['keyword']
        return redirect(url_for('show_result', keyword=ky))
    return render_template("search.html", hashcode=get_sha1("static/style.css"))


@app.route('/result', methods=['POST', 'GET'])
def show_result():
    searchword = request.args.get('keyword')
    search_result = searcher.query(searchword)
    title, url, content = [], [], []
    print("len=", len(search_result))
    for result in search_result:
        title.append(result.title)
        url.append(result.url)
        content.append("...add content here...")
    lens = [i for i in range(len(title))]
    if request.method == 'POST':
        keyword = request.form['keyword']
        return redirect(url_for('show_result', keyword=keyword))
    return render_template("show_result.html", searchword=searchword, title=title, url=url, content=content, lens=lens)

def get_sha1(filename):
    with open(filename, "rb") as f:
        sha1obj = hashlib.sha1()
        sha1obj.update(f.read())
    return sha1obj.hexdigest()

if __name__ == '__main__':
    searcher = HtmlIndexSearcher(store_dir="./lucene_index/")
    app.run(debug=True, port=8080)