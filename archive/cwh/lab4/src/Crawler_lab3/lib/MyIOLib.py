#
import os

import urllib.parse
from typing import Optional

# Type alias
Url = str


def as_valid_filename(s: Url, postfix: str = None) -> str:
    if postfix is None:
        postfix = "txt"
    return urllib.parse.quote_plus(s) + "." + postfix


def add_page_to_folder(url: Url, content: bytes, cache_dir: Optional[str] = None):
    if cache_dir is None:
        cache_dir = "./cache"
    cache_folder = os.path.relpath(cache_dir)
    index_file = os.path.join(cache_folder, "index.txt")
    folder = os.path.join(cache_folder, "html")

    if not os.path.exists(cache_folder):
        os.mkdir(cache_folder)

    if not os.path.exists(folder):
        os.mkdir(folder)

    filename = as_valid_filename(url, postfix="html")
    _file_dir = os.path.join(folder, filename)

    if os.path.exists(_file_dir):
        # 这个网页已经存过了
        return

    # 更新索引txt并创建html文件

    try:
        mode = 'w' if isinstance(content, str) else 'wb'
        # 如果是bytes就用二进制文件的形式打开
        with open(_file_dir, mode) as f:
            f.write(content)  # 将网页存入文件
    except Exception as e:
        # Write failed
        raise e
    else:
        with open(index_file, 'a') as index:
            index.write(url + '\t' + filename + '\n')
