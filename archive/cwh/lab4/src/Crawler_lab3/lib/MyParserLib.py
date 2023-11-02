import re
import urllib.parse
import urllib.request
from typing import Set, AnyStr

from bs4 import BeautifulSoup, SoupStrainer

only_a_tags = SoupStrainer('a')
only_img_tags = SoupStrainer('img')


def parse_url(content: AnyStr, home_url: str) -> Set[str]:
    url_set = set()
    soup = BeautifulSoup(content, "html.parser", parse_only=only_a_tags)
    http_filter = re.compile("^https?://")
    for tag in soup.find_all(name="a"):
        raw_url = tag.get("href", "")
        try:
            possible_url = urllib.parse.urljoin(home_url, raw_url)
            # judging on possible url
            result = http_filter.match(possible_url)
            if result is None:
                # Not an url
                continue
            possible_url_no_frag = urllib.parse.urldefrag(possible_url).url
        except Exception as e:
            continue
        url_set.add(possible_url_no_frag)

    return url_set


def parse_img(content: str, home_url: str) -> Set[str]:
    img_set = set()
    soup = BeautifulSoup(content, "html.parser", parse_only=only_img_tags)
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
