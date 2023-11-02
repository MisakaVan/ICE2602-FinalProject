# SJTU EE208

import re
import urllib.parse
import urllib.request

from bs4 import BeautifulSoup


def parse_img(content, home_url):
    img_set = set()
    soup = BeautifulSoup(content, "html.parser")
    http_filter = re.compile("^https?://")
    for tag in soup.find_all(name="img"):
        raw_src = tag.get("src", "")
        possible_url = urllib.parse.urljoin(home_url, raw_src)
        result = http_filter.match(possible_url)
        if result is None:
            # Not valid
            continue
        img_set.add(possible_url)
    return img_set


def write_outputs(urls, filename):
    file = open(filename, 'w', encoding='utf-8')
    for i in urls:
        file.write(i)
        file.write('\n')
    file.close()


def main():
    url = "https://wiki.biligame.com/mc/Minecraft_Wiki"
    content = urllib.request.urlopen(url).read()
    url_set = parse_img(content, url)
    write_outputs(url_set, "result2.txt")


if __name__ == '__main__':
    main()
