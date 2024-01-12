import urllib.parse
import urllib.request
import urllib.response
import urllib.error
from typing import Optional

import loguru

from lxml import html

logger = loguru.logger

@logger.catch()
def get_content(url:str, user_agent) -> Optional[bytes]:
    """
    Get the content of the url.

    :param url:
    :param user_agent:
    :return:
    """
    try:
        request = urllib.request.Request(url)
        request.add_header("User-Agent", user_agent)
        response = urllib.request.urlopen(url, timeout=0.5)

    except urllib.error.HTTPError as e:
        logger.error(f"HTTPError: {e}")
        return None
    except urllib.error.URLError as e:
        logger.error(f"URLError: {e}")
        return None
    except Exception as e:
        logger.error(f"Exception: {e}")
        raise e
        # return None

    return response.read()


@logger.catch()
def parse_all_urls(content: bytes, home_url: str):
    """
    Parse all urls in the content.

    use bs4 to parse the content.

    :param content:
    :param home_url:
    :return:
    """
    tree = html.fromstring(content)
    for href in tree.xpath('//a/@href'):
        _new_url = urllib.parse.urljoin(home_url, href)
        _parse_result = urllib.parse.urlparse(_new_url)
        if _parse_result.scheme not in ('http', 'https'):
            continue
        if _parse_result.netloc == '':
            continue
        yield _new_url

@logger.catch()
def parse_all_img_src(content: bytes, home_url: str):
    """
    Parse all img src in the content.

    use bs4 to parse the content.

    :param content:
    :param home_url:
    :return:
    """
    tree = html.fromstring(content)
    for src in tree.xpath('//img/@src'):
        _new_url = urllib.parse.urljoin(home_url, src)
        _parse_result = urllib.parse.urlparse(_new_url)
        if _parse_result.scheme not in ('http', 'https'):
            continue
        if _parse_result.netloc == '':
            continue
        yield _new_url

def get_extension_from_image_src(image_src: str):
    parse_result = urllib.parse.urlparse(image_src)
    path = parse_result.path
    filename = path.split('/')[-1]
    ext = filename.split('.')[-1]
    return ext.lower()


if __name__ == '__main__':
    url1 = "https://news.zhibo8.com/zuqiu/more.htm?label=欧冠"
    url1 = urllib.parse.quote(url1, safe='/:?=')
    print(url1)
    content1 = get_content(url1, user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1.2 Safari/605.1.15")
    # print(content.decode())
    res = list(parse_all_urls(content1, url1))
    # for new_url in res:
    #     parse_result = urllib.parse.urlparse(new_url)
    #     print(new_url, parse_result.netloc)
    print(len(res))
