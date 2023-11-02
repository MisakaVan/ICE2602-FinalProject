# SJTU EE208

from flask import Flask, redirect, render_template, request, url_for
from search import run

app = Flask(__name__)


@app.route('/', methods=['POST', 'GET'])
def search_form():
    if request.method == "POST":
        keyword = request.form['keyword']
        return redirect(url_for('result', keyword=keyword))
    return render_template("search.html")


@app.route('/result', methods=['POST', 'GET'])
def show_result():
    searchword = request.args.get('keyword')
    title, url, content = run(searchword)
    lens = [i for i in range(len(title))]
    if request.method == 'POST':
        keyword = request.form['keyword']
        return redirect(url_for('result', keyword=keyword))
    return render_template("show_result.html", searchword=searchword, title=title, url=url, content=content, lens=lens)


if __name__ == '__main__':
    app.run(debug=True, port=8080)