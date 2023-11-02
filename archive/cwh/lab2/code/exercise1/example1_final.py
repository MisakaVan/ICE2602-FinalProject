# SJTU EE208
# Lab2

import sys
import urllib.parse
import urllib.request
from http import cookiejar

from bs4 import BeautifulSoup


def make_opener():
    cookie = cookiejar.CookieJar()
    cookie_handler = urllib.request.HTTPCookieProcessor(cookie)
    opener_ = urllib.request.build_opener(cookie_handler)
    opener_.addheaders = [("User-Agent",
                           "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15")]  # 本机Edge报头
    return opener_


def make_post_data(dict_=None, **kwargs):
    data_dict = dict(kwargs)
    if type(dict_) is dict:
        data_dict.update(dict_)
    post_data_ = urllib.parse.urlencode(data_dict).encode("utf8")
    return post_data_


def main(username, password):
    sign_in_url = "https://www.yaozh.com/login/"
    info_url = "https://www.yaozh.com/member/basicinfo/"
    opener = make_opener()
    postdata = make_post_data(username=username,
                              pwd=password,
                              formhash="4A95C39D38",
                              backurl="https%3A%2F%2Fwww.yaozh.com%2F")
    # 7. 构建Request请求对象，包含需要发送的用户名和密码
    request = urllib.request.Request(sign_in_url,
                                     data=postdata,
                                     headers=dict(Referer=sign_in_url))
    # 8. 通过opener发送这个请求，并获取登陆后的Cookie值
    opener.open(request)
    # 9. opener包含用户登陆后的Cookie值，可以直接访问那些登陆后才能访问的页面
    response = opener.open(info_url).read()
    # 10. The rest is done by you
    soup = BeautifulSoup(response, features="html.parser")
    info_div = soup.find("div", {"class": "U_myinfo clearfix"})
    print(f'真实姓名: {info_div.contents[3].find("input").get("value", "")}')
    print(f'用户名: {info_div.contents[5].find("input").get("value", "")}')
    print(f'性别: {info_div.contents[7].find("input").get("value", "")}')
    print(f'出生日期: {info_div.contents[9].find("input").get("value", "")}')
    print(f'个人简介: {info_div.contents[11].find("textarea").contents[0]}')


def test():
    main("Chenwenhao123", "20Sovn300")


if __name__ == '__main__':
    if len(sys.argv) == 1:
        test()
    else:
        username = sys.argv[1]
        password = sys.argv[2]
        main(username=username, password=password)
