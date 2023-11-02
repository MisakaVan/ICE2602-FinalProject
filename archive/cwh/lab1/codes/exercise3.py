# SJTU EE208

import urllib.parse
import urllib.request
from typing import List, Tuple

from bs4 import BeautifulSoup


def parse_zhihu_daily(content, home_url):
    zhihu_list = list()

    soup = BeautifulSoup(content, "html.parser")

    for tag in soup.find_all("div", attrs={"class": "box"}):
        """
        e.g.
        <div class="box">
            <a href="/story/9765413" class="link-button">
                <img src="https://picx.zhimg.com/v2-525567e19d74958bf57d1e9e8966db55.jpg?source=8673f162" class="preview-image">
                <span class="title">瞎扯 · 如何正确地吐槽</span>
            </a>
        </div>
        """
        try:
            raw_href: str = tag.a.get("href", "")
            raw_src: str = tag.a.img.get("src", "")
            item_title: str = tag.a.span.string
            item_href: str = urllib.parse.urljoin(home_url, raw_href)
            item_src: str = urllib.parse.urljoin(home_url, raw_src)
            zhihu_list.append((item_src, item_title, item_href))
        except Exception as e:
            pass
    return zhihu_list


def write_outputs(zhihu_items: List[Tuple[str, str, str]], filename):
    file = open(filename, "w", encoding="utf-8")
    for zhihu in zhihu_items:
        for element in zhihu:
            file.write(element)
            file.write("\t")
        file.write("\n")
    file.close()


def main():
    url = "http://daily.zhihu.com/"
    # request1 = urllib.request.Request(url)
    # request1.add_header()
    content = urllib.request.urlopen(url).read()
    zhihu_daily_items = parse_zhihu_daily(content, url)
    write_outputs(zhihu_daily_items, "result3.txt")


if __name__ == "__main__":
    main()
