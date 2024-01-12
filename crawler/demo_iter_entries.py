import os.path as osp

import FileSet as fs

"""
在FileSet中并没有直接建立从网页url到文件或entry的映射。使用了顺序存储，在entry组成的列表中，每个entry记录了网页的url，以及网页内容的文件名。

你可以顺序遍历FileSet中的entry，然后根据entry中的url，和用文件名拼接出的文件路径，在处理网页内容的时候知道原文url是什么。
"""


def do_something(_fileset, _entry: fs.FileSetRecordedEntry):
    file_path = osp.join(_fileset.directory, "contents", _entry.content_filename)
    print(f"Url: {_entry.url}, File at: {file_path}")


if __name__ == "__main__":
    crawler_file_directory = "./crawler_test_cache"
    fileset_directory = osp.join(crawler_file_directory, "saved_files")

    fileset = fs.FileSet.load_from(fileset_directory, mode="append-full-load")

    for entry in fileset: # 其实是遍历fileset.recorded_entries
        do_something(fileset, entry)
