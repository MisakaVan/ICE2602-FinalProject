# Crawler

## 需求

### 原始网页

- 爬取指定域名下指定前缀的网页。
- 自定义爬取的最大数量、并发数、时间间隔。
- 爬取的原始网页存储到本地文件系统。需要记录爬取的时间、网页地址等信息。
- 可能可以使用sql存储原始网页。

### 针对两个目标网站的网页解析

需要存储的信息：
- 标题
- 文章url
- 发布时间
- 正文文本
- 正文图片url
-

#### 新浪体育网页结构

标题在`<h1 class="main-title"> abc </h1>`

文章正文在一个`<div class="article" id="artibody" ...>`内部。

#### 懂球帝网页结构

东西都在`<div class="news-left"> ... </div>`内部。

标题：`<h1 class="news-title">abc</h1>`

正文：`<div class="con"> ... </div>`






