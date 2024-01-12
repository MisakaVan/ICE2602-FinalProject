# crawl image from internet and save.

import urllib.request
import urllib.parse
import requests
import os.path as osp
import os
import lxml


def get_image_content(url):
    """
    :param url:
    :return:
    图片的二进制内容、图片的类型（扩展名）。
    """

    r = requests.get(url)
    return r.content, r.headers['Content-Type'].split('/')[1]

def get_image_and_save_under_directory(url, directory):
    """
    在directory下创建一个和url同样结构的文件树，将url的图片保存在该文件树下。
    第一级的文件夹名字是url的域名，后面跟着的是url的path。
    也就是说，如果url是https://www.baidu.com/a/b/c.jpg，那么就在directory下创建一个
    www.baidu.com/a/b的文件夹，将c.jpg保存在该文件夹下。

    :param url:
    :param directory:
    :return:
    """

    # 1. 创建文件夹
    # 2. 保存图片
    # 3. 返回保存的文件名

    # 1. 创建文件夹
    parse_result = urllib.parse.urlparse(url)

    print(parse_result)

    _netloc = parse_result.netloc
    _path = parse_result.path[1:] if parse_result.path.startswith('/') else parse_result.path

    full_path = osp.join(directory, _netloc, _path)
    print(full_path)

    full_dir = osp.dirname(full_path)
    if not osp.exists(full_dir):
        os.makedirs(full_dir)

    print(full_dir)

    # 2. 保存图片
    content, ext = get_image_content(url)
    with open(full_path, 'wb') as f:
        f.write(content)

    # 3. 返回保存的文件名
    return full_path



def test1():
    url = 'https://static4style.duoduocdn.com/common/img/wqrcode_bg_manlian_pcnews2.png'
    directory = './testground2_cache'
    if not osp.exists(directory):
        os.mkdir(directory)


    content, ext = get_image_content(url)

    print(ext)

    filename = osp.join(directory, 'test1.' + ext)
    with open(filename, 'wb') as f:
        f.write(content)

def test2():
    url = 'https://static4style.duoduocdn.com/common/img/wqrcode_bg_manlian_pcnews2.png'
    directory = './testground2_cache/images'
    if not osp.exists(directory):
        os.mkdir(directory)

    filename = get_image_and_save_under_directory(url, directory)
    print(filename)


if __name__ == '__main__':
    test2()
