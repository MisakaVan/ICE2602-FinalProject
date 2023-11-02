# SJTU EE208

import re
import urllib.parse
import urllib.request

from bs4 import BeautifulSoup


def parse_url(content, home_url):
    url_set = set()
    soup = BeautifulSoup(content, "html.parser")
    http_filter = re.compile("^https?://")
    for tag in soup.find_all(name="a"):
        raw_url = tag.get("href", "")
        possible_url = urllib.parse.urljoin(home_url, raw_url)
        # judging on possible url
        result = http_filter.match(possible_url)
        if result is None:
            # Not an url
            continue
        possible_url_no_frag = urllib.parse.urldefrag(possible_url).url
        url_set.add(possible_url_no_frag)

    return url_set


def write_outputs(urls, filename):
    file = open(filename, 'w', encoding='utf-8')
    for url in urls:
        file.write(url)
        file.write('\n')
    file.close()


def main():
    url = "https://docs.python.org/3.8/library/urllib.parse.html"
    content = urllib.request.urlopen(url).read()
    url_set = parse_url(content, url)
    write_outputs(url_set, "result1.txt")


if __name__ == '__main__':
    main()
