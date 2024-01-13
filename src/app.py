# SJTU EE208

#from searchIndex import HtmlIndexSearcher
import hashlib
import random
import string

from flask import Flask, redirect, render_template, request, url_for
from markupsafe import escape

app = Flask(__name__)

class SearchResult:
    def __init__(self, title, url="https://www.example.com", date="2023-12-17", content="news content here "*10, containimg=0, filename="sample1.jpg"):
        '''
        SearchResult is a class with attributes:
        title: string
        url: string that should be a complete url
        date: string in format "yyyy-mm-dd"
        content: string
        containimg: 0 or 1 (0 means no image, 1 means contain image)
        filename: string that should be a relative file path under folder "static/images"
        '''
        self.title = title
        self.url = url
        self.date = date
        self.content = content
        self.containimg = containimg
        self.filename = filename

class ImageResult:
    def __init__(self, title, url="https://www.example.com", filename="sample1.jpg"):
        '''
        ImageResult is a class with attributes:
        title: string
        url: string that should be a complete url
        filename: string that should be a relative file path under folder "static/images"
        '''
        self.title = title
        self.url = url
        self.filename = filename

class Date:
    def __init__(self, year, month, day):
        self.year = year
        self.month = month
        self.day = day

def getResults(searchword, category):
    '''
    TODO
    searchword: string
    category: string from ["all","csl","epl","bundesliga","seriea","ligue1","laliga","url"]
    return: list of SearchResult
    
    '''
    pass

def cutResults(results, page):
    return results[10*(page-1):10*page]

def Text4ImageResult(keyword):
    '''
    TODO
    keyword: string
    return: list of ImageResult
    '''
    pass

def Image4ImageResult(filename):
    '''
    TODO
    filename: string that is a relative file path under folder "static/upload"
    return: list of ImageResult
    '''
    pass

def getStartDate(start_year, start_month, start_day):
    if start_year == "all":
        return Date(2010, 1, 1)
    if start_month == "all":
        return Date(int(start_year), 1, 1)
    if start_day == "all":
        return Date(int(start_year), int(start_month), 1)
    return Date(int(start_year), int(start_month), int(start_day))

def getEndDate(end_year, end_month, end_day):
    if end_year == "all":
        return Date(2024, 12, 31)
    if end_month == "all":
        return Date(int(end_year), 12, 31)
    if end_day == "all":
        return Date(int(end_year), int(end_month), 31)
    return Date(int(end_year), int(end_month), int(end_day))

def validDate(start_date, end_date, news):
    news_date = news.date.split("-")
    news_date = Date(int(news_date[0]), int(news_date[1]), int(news_date[2]))
    if news_date.year >= start_date.year and news_date.year <= end_date.year and news_date.month >= start_date.month and news_date.month <= end_date.month and news_date.day >= start_date.day and news_date.day <= end_date.day:
        return True
    return False

@app.route('/', methods=['POST', 'GET'])
def search_form():
    if request.method == "GET":
        imagesearch = request.args.get('imagesearch')
        if imagesearch == None:
            imagesearch = 0
        imagesearch = int(imagesearch)
    if request.method == "POST":
        keyword = request.form.get('keyword')
        category = request.form.get('category')
        if category:
            page = 1
            filt = 0
            return redirect(url_for('show_result', keyword=keyword, category=category, page=page, filt=filt))
        else:
            return redirect(url_for('show_image_result', keyword=keyword, imageinput=0))
    return render_template("index.html", imagesearch=imagesearch)

@app.route('/image', methods=['GET'])
def search_image():
    return render_template("search_img.html")

@app.route('/upload', methods=['POST'])
def upload_image():
    file = request.files['file']
    if file:
        filename = file.filename
        file.save("./static/upload/" + filename)
        return redirect(url_for('show_image_result', filename=filename, imageinput=1))

@app.route('/result', methods=['GET'])
def show_result():
    keyword = request.values.get('keyword')
    category = request.values.get('category')
    page = request.values.get('page')
    filt = request.values.get('filt')
    if page == None:
        page = 1
    else:
        page = int(page)
    results = getResults(keyword, category)
    if filt == "1":
        start_year = request.args.get('start_year')
        start_month = request.args.get('start_month')
        start_day = request.args.get('start_day')
        if start_day == None:
            start_day = "all"
        end_year = request.args.get('end_year')
        end_month = request.args.get('end_month')
        end_day = request.args.get('end_day')
        if end_day == None:
            end_day = "all"
        start_date = getStartDate(start_year, start_month, start_day)
        end_date = getEndDate(end_year, end_month, end_day)
        results = list(filter(lambda x: validDate(start_date, end_date, x), results))
    maxlen = (len(results)-1)//10+1
    results = cutResults(results, page)
    lens = [i for i in range(len(results))]
    if filt == "1":
        return render_template("result.html", keyword=keyword, category=category, results=results, lens=lens, current_page=page, last_page=maxlen, filt=1, start_year=start_year, start_month=start_month, start_day=start_day, end_year=end_year, end_month=end_month, end_day=end_day)
    return render_template("result.html", keyword=keyword, category=category, results=results, lens=lens, current_page=page, last_page=maxlen, filt=0)

@app.route('/imageresult', methods=['GET'])
def show_image_result():
    imageinput = request.args.get('imageinput')
    imageinput = int(imageinput)
    if imageinput == 0:
        keyword = request.args.get('keyword')
        results = Text4ImageResult(keyword)
        lens = len(results)
    else:
        filename = request.args.get('filename')
        results = Image4ImageResult(filename)
        lens = len(results)
    if imageinput == 0:
        return render_template("img_result.html", keyword=keyword, results=results, lens=lens, imageinput=imageinput)
    else:
        return render_template("img_result.html", filename=filename, results=results, lens=lens, imageinput=imageinput)

if __name__ == '__main__':
    app.run(debug=True, port=8080)