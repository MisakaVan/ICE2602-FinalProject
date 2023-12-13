# functions for filtering the urls.
# for example, we only desire the urls with the prefix "https://sports.sina.com.cn/"

from bs4 import BeautifulSoup

def is_sina_sports_url(url):
    return url.startswith('https://sports.sina.com.cn/')

def is_dqd_url(url):
    return url.startswith('https://www.dongqiudi.com/articles/')
