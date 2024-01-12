from unittest import TestCase

from utils import is_sina_sports_football_article, as_unique_url
import utils


class Test1(TestCase):

    def test_as_unique_url(self):
        eq_pairs = [
            ("https://www.example.com", "https://www.example.com"),
            ("https://www.example.com/", "https://www.example.com"),
            ("https://www.example.com?foo=bar", "https://www.example.com"),
            ("https://www.example.com#foo", "https://www.example.com"),
            ("https://www.example.com?foo=bar#foo", "https://www.example.com"),
            ("https://www.example.com?foo=bar#foo", "https://www.example.com"),
        ]

        eq_pairs_with_path = [
            ("https://www.example.com/path", "https://www.example.com/path"),
            ("https://www.example.com/path/", "https://www.example.com/path"),
            ("https://www.example.com/path?foo=bar", "https://www.example.com/path"),
            ("https://www.example.com/path#foo", "https://www.example.com/path"),
            ("https://www.example.com/path?foo=bar#foo", "https://www.example.com/path"),
        ]

        for url, expected in eq_pairs:
            self.assertEqual(expected, as_unique_url(url))

        for url, expected in eq_pairs_with_path:
            self.assertEqual(expected, as_unique_url(url))

    def test_is_sina_sports_football_article(self):
        true_urls = [
            'https://sports.sina.com.cn/global/france/2024-01-10/doc-inaayyri7443394.shtml',
            'https://sports.sina.com.cn/g/pl/2024-01-09/doc-inaaxhfz7551761.shtml',
            'https://sports.sina.com.cn/g/laliga/2024-01-08/doc-inaaussx9442794.shtml',
            'https://sports.sina.com.cn/china/2024-01-10/doc-inaazexe4395870.shtml',
            'https://sports.sina.com.cn/china/2023-12-28/doc-imzzpuna7405318.shtml',
            'https://sports.sina.com.cn/china/2023-09-18/doc-imznavsm0042349.shtml',
        ]

        false_urls = [
            'https://sports.sina.com.cn/motorracing/f1/newsall/2023-11-25/doc-imzvwcen7726844.shtml',  # F1
            'https://sports.sina.com.cn/basketball/cba/2024-01-09/doc-inaaxxcv7990344.shtml',  # CBA
            'https://sports.sina.com.cn/basketball/nba/2024-01-09/doc-inaaxhhc8262841.shtml',  # NBA
            'https://sports.sina.com.cn/others/diving/2023-10-02/doc-imzpthhf5098200.shtml',  # 跳水
            'https://k.sina.com.cn/article_3984582452_med7fe73403301131e.html?cre=tianyi&mod=pcspth&loc=4&r=0&rfunc=59&tj=cxvertical_pc_spth&tr=12&from=travel',
            # 灌水文
            'https://k.sina.com.cn/article_2419309333_9033bb15001015gg3.html?cre=tianyi&mod=pcspth&loc=14&r=0&rfunc=59&tj=cxvertical_pc_spth&tr=12&from=sports&subch=pingpang',
            # 新闻看点
            'https://sports.sina.com.cn/others/volleyball/2023-11-25/doc-imzvvnhp2519512.shtml ',
            'https://sports.sina.com.cn/l/2023-12-24/doc-imzzcrft3947548.shtml ',
        ]

        # log the failed cases
        for url in false_urls:
            if is_sina_sports_football_article(url):
                self.fail(f"{url} should not be a football article")

        for url in true_urls:
            if not is_sina_sports_football_article(url):
                self.fail(f"{url} should be a football article")

    def test_is_zhibo8_football_domain(self):

        true_urls = [
            'https://news.zhibo8.com/zuqiu/2024-01-11/659ff140399f2native.htm',
            'https://news.zhibo8.com/zuqiu/2024-01-11/659fbf2114438native.htm',
            'https://news.zhibo8.com/zuqiu/2024-01-10/659e6cf2909d6native.htm',
            'https://news.zhibo8.com/zuqiu/2024-01-11/659fe9c49f15dnative.htm',
            ]

        for url in true_urls:
            self.assertTrue(utils.is_zhibo8_news_football_article(url))

    def test_is_zhibo8_football_article(self):

        true_urls = [
            'https://news.zhibo8.com/zuqiu/2024-01-11/659ff140399f2native.htm',
            'https://news.zhibo8.com/zuqiu/2024-01-11/659fbf2114438native.htm',
            'https://news.zhibo8.com/zuqiu/2024-01-10/659e6cf2909d6native.htm',
            'https://news.zhibo8.com/zuqiu/2024-01-11/659fe9c49f15dnative.htm',
            'https://news.zhibo8.com/zuqiu/2024-01-06/6598890dd80e2native.htm'
        ]

        for url in true_urls:
            self.assertTrue(utils.is_zhibo8_news_football_article(url))
