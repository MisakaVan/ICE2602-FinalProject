import urllib.parse
import numpy as np

dqd_domain = 'www.dongqiudi.com'


def is_dqd_domain(url) -> bool:
    """
    判断是否是懂球帝的网址。
    :param url:
    :return:
    """
    parse_result = urllib.parse.urlparse(url)
    return parse_result.netloc.lower() == dqd_domain


def is_dqd_football_article(url) -> bool:
    """
    format: "www.dongqiudi.com/articles/{1234567}(.html)".

    note that the ".html" suffix is optional.

    :param url:
    :return:
    """

    parse_result = urllib.parse.urlparse(url)

    if parse_result.netloc != dqd_domain:
        return False

    if not parse_result.path.startswith('/articles/'):
        return False

    paths = parse_result.path.split('/')

    # paths = ['', 'articles', '{1234567}(.html)']
    if len(paths) != 3:
        return False

    return True


zhibo8_news_domain = 'news.zhibo8.com'
zhibo8_news_football_domain = 'news.zhibo8.com/zuqiu/'


def is_zhibo8_football_domain(url) -> bool:
    """
    判断是否是直播吧足球的网址。
    具体地，域名是news.zhibo8.com，且path是/zuqiu开头的网址。
    :param url:
    :return:
    """
    parse_result = urllib.parse.urlparse(url)
    return (parse_result.netloc.lower() == zhibo8_news_domain
            and parse_result.path.startswith('/zuqiu'))


def is_zhibo8_news_football_article(url) -> bool:
    """
    format:
    e.g. https://news.zhibo8.com/zuqiu/2024-01-11/659fccc7124d2native.htm

    the format is:
    https://news.zhibo8.com/zuqiu/{yyyy-mm-dd}/{some random string}native.htm

    :param url:
    :return:
    """

    parse_result = urllib.parse.urlparse(url)

    if parse_result.netloc != zhibo8_news_domain:
        return False

    if not parse_result.path.startswith('/zuqiu/'):
        return False

    paths = parse_result.path.split('/')

    # paths = ['', 'zuqiu', '{yyyy-mm-dd}', '{some random string}native.htm']
    if len(paths) != 4:
        return False

    if not paths[3].endswith('native.htm'):
        return False

    return True


def as_unique_url(_url: str, keep_query=False) -> str:
    """
    将url转换为唯一的url。
    - 去除url中的fragment(以#开头的部分)
    - 去除url中的query(参数)
    - 将url中的scheme和netloc转换为小写
    - 若url以/结尾，则去除(因为https://www.example.com/和https://www.example.com是同一个网址)
    :param _url
    :param keep_query: 是否保留query(参数)
    :return:
    """
    url = urllib.parse.urlparse(_url)
    url = url._replace(fragment="")
    if not keep_query:
        url = url._replace(query="")
    url = url._replace(scheme=url.scheme.lower(), netloc=url.netloc.lower())
    if url.path.endswith("/"):
        url = url._replace(path=url.path[:-1])

    # 如果是懂球帝文章，且没有.html后缀，则加上.html后缀
    if is_dqd_football_article(url.geturl()) and not url.path.endswith(".html"):
        url = url._replace(path=url.path + ".html")

    return url.geturl()


sina_sports_domain = 'sports.sina.com.cn'


def is_sina_sports_domain(url) -> bool:
    """
    判断是否是新浪体育的网址。
    :param url:
    :return:
    """
    parse_result = urllib.parse.urlparse(url)
    return parse_result.netloc.lower() == sina_sports_domain


def is_sina_sports_football_article(url) -> bool:
    """
    判断是否是新浪体育足球文章。
    :param url:
    :return:
    """

    parse_result = urllib.parse.urlparse(url)

    # print(parse_result)

    if parse_result.netloc != sina_sports_domain:
        return False

    if not parse_result.path.startswith('/'):
        # 有些url的path是相对路径，如：'./doc-inaayyri7443394.shtml'
        return False

    if not parse_result.path.endswith('.shtml'):
        # 文章的url必须以.shtml结尾
        return False

    paths = parse_result.path.split('/')

    # 文章的url必须是形如'/xxx/xxxx/xxxx.shtml'的形式
    # 如果是 /china/ 开头，那么形式是 /china/yyyy-mm-dd/doc-xxxxxxx.shtml
    # 如果是 /global/ 或 /g/ 开头，那么形式是 /{global或g}/{表示地区的字符串}/yyyy-mm-dd/doc-xxxxxxx.shtml

    # 只检查paths的长度和最后一个元素的开头。

    expected_path_length = (4 if paths[1] == 'china'
                            else 5 if paths[1] in ('global', 'g') else None)

    if expected_path_length is None:
        return False

    if len(paths) != expected_path_length:
        return False

    if not paths[-1].startswith('doc-'):
        return False

    return True


def count_ones_in_bloomfilter_npy(npy_path):
    """
    npy file must be 1-dim array of type bool.
    :param npy_path:
    :return:
    """
    arr = np.load(npy_path)
    return np.count_nonzero(arr)


is_sina_sports_football_article('https://sports.sina.com.cn/global/france/2024-01-10/doc-inaayyri7443394.shtml'
                                )

if __name__ == '__main__':
    print(is_zhibo8_news_football_article("https://news.zhibo8.com/zuqiu/2024-01-10/659e6cf2909d6native.htm"))
