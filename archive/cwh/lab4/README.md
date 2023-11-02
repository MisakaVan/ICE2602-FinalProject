# Lab4

陈文昊 522030910188

src文件夹里存放了练习的源代码。

## 运行搜索方式

运行src文件夹下的.sh脚本（运行searchIndex.py）


## src

### Crawler_lab3/

这是基于lab3多线程爬虫的一个版本。用更多的try-except语句保证运行的稳定性。

其中的`cache/`文件夹下的`html/`文件夹是存放爬取的网页的位置。在此不附文件。

### lucene_index/

存放lucene创建的索引文件。

### makeIndex.py

用网页源文件创建lunene索引。

不需要命令行参数，可以用`python makeIndex.py`或在ide里直接运行。

### makeIndex.py

查询lunene索引。

不需要命令行参数，可以用`python searchIndex.py`或在ide里直接运行。

然后在终端内进行交互。默认每次显示10条搜索结果，若要配置需要修改源码。

注：在本机第一次运行时可能报错，但紧接着再运行一次就能正常运行。无法稳定复现。

