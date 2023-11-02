import re
import urllib.parse
import urllib.request
from typing import Set

from bs4 import BeautifulSoup


def parse_url(content: str, home_url: str) -> Set[str]:
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


def parse_img(content: str, home_url: str) -> Set[str]:
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
