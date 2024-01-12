# readme

a multithread web crawler written in python

supports：

- [x] multithread
- [x] filter what html files to save
- [x] filter what html files to crawl

feature:

- [x] a data structure to manage the cached files
- [x] saving the state of the crawler so that tasks can be resumed

## 文件结构

缓存文件相关：
- crawler_test_cache/ 爬取新浪体育文章的Crawler的directory
- image_sina_cache/ 对上述Crawler中保存的html文件进行解析，爬取其中的图片的ImageRetriever的directory
- crawler_zhibo8_cache/ 爬取直播吧文章的Crawler的directory
- image_zhibo8_cache/ 对上述Crawler中保存的html文件进行解析，爬取其中的图片的ImageRetriever的directory

爬虫相关：
- __main__.py 爬虫的入口
- BloomFilter.py 布隆过滤器
- FileSet.py 一个数据结构，用于管理缓存文件
- Crawler.py 爬虫
- ImageRetriever.py 图片爬取器
- utils.py 一些工具函数
- request_utils.py 一些工具函数

调用demo：
- demo_iter_entries.py 展示如何将爬虫目录下的FileSet载入内存并遍历其中的条目。
- demo_get_image.py 展示如何载入一个ImageRetriever，通过图片src找到已经缓存在本地的图片路径。

其他：
- test开头的文件为测试文件


