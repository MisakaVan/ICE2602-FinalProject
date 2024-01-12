import os.path as osp
import os
import shutil
import json
import sys
import time
import datetime
import loguru

import numpy as np
import threading
from collections import namedtuple

# use loguru to log
logger = loguru.logger

FileSetInsertEntry = namedtuple(
    'FileSetInsertEntry',
    ['content', 'url', 'title', 'download_time']
)
FileSetRecordedEntry = namedtuple(
    'FileSetRecordedEntry',
    ['content_filename', 'url', 'title', 'download_time']
)


def get_timestamp_string():
    """
    "%y%m%d_%H_%M_%S_%f". f is microseconds.
    time.strftime does not support microseconds. so we use datetime.datetime.now().
    :return:
    """
    return datetime.datetime.now().strftime("%y%m%d_%H_%M_%S_%f")


get_snapshot_name = get_timestamp_string

def as_insert_entry(content, url, title, download_time):
    """
    This function is intended for caller of the FileSet, usually the web crawler.
    :param content:
    :param url:
    :param title:
    :param download_time:
    :return:
    """
    return FileSetInsertEntry(content=content,
                              url=url,
                              title=title,
                              download_time=download_time)


class FileSet:
    """
    A set-like data structure that stores data in files.

    For each entry, there contains one large text file (a raw html file)
    and several small fields of data (time, title, etc.).

    the big file will be given a unique name,
    and the filename, together with other fields, will be stored in a json file.

    Feature:
        1. support multi-threading insert
        2. support saving and loading

    File structure by default:
    | FileSet.json: the parameters of the FileSet.
    |
    | FileSetEntries.json: the entries of the FileSet.
    |
    | contents/: the directory that contains the large files.
    | | xxx.html: the large file.
    | | ...
    |
    | snapshots/: the directory that contains the snapshots.
      | some_snapshot_name/: the directory that contains the snapshot.
        | FileSet.json: the parameters of the FileSet.
        | FileSetEntries.json: the entries of the FileSet.

    """

    def __init__(self,
                 directory: str = None,
                 insert_entry_class: type = FileSetInsertEntry,
                 state_dict=None,
                 mode='append'
                 ):
        """

        :param directory:
        :param insert_entry_class:
        :param state_dict:
        :param mode: Only works when state_dict is not None (i.e. loading from a directory).
                Otherwise, it will be defaulted to 'overwrite' i.e. initialize a new FileSet.
                'append', 'append-full-load' or 'overwrite'
                'append' means that the FileSet will not load the existing entries into memory when initialized,
                and will update the json file with the new entries when the FileSet is saved.
                'append-full-load' means that the FileSet will load the existing entries into memory when initialized.
                'overwrite' means that the FileSet will overwrite the json file, clearing all existing entries and contents.
                This is actually the same as initializing a new FileSet with the same directory.
        """
        self.lock = threading.Lock()
        self.insert_entry_class = insert_entry_class

        self.cur_mode = 'overwrite' if state_dict is None else mode

        if state_dict is not None:
            self.directory = state_dict['directory']
            self.recorded_entries = state_dict['recorded_entries']
            self.filename_counter = state_dict['filename_counter']
        else:
            self.directory = directory
            self.recorded_entries: list[FileSetRecordedEntry] = []
            self.filename_counter = 0
            self._clear_and_init_directory()

    def as_state_dict(self):
        return {
            'directory': self.directory,
            'recorded_entries': self.recorded_entries,
            'filename_counter': self.filename_counter
        }

    def __str__(self):
        return f"FileSet(directory={self.directory}, mode={self.cur_mode}, filename_counter={self.filename_counter}, cur_size={len(self.recorded_entries)})"

    __repr__ = __str__

    # iterating over the FileSet will iterate over the recorded entries.

    def __iter__(self):
        return iter(self.recorded_entries)

    def __len__(self):
        return len(self.recorded_entries)


    def save(self, _path=None, filename_params="FileSet.json", filename_entries="FileSetEntries.json"):
        """
        Save the FileSet parameters and entries to a directory.
        :param _path:
        :param filename_params:
        :param filename_entries:
        :return:
        """
        with self.lock:
            path = self.directory if _path is None else _path
            logger.info(f"Saving FileSet to {path}")
            os.makedirs(path, exist_ok=True)
            _filepath_params = osp.join(path, filename_params)
            _filepath_entries = osp.join(path, filename_entries)

            state_dict = self.as_state_dict()
            state_dict_to_save = {k: v for k, v in state_dict.items() if k != 'recorded_entries'}

            if self.cur_mode == 'append':
                # read the existing entries into a list and append the new entries
                with open(_filepath_entries, "r") as f:
                    recorded_entries_to_save = json.load(f)
                recorded_entries_to_save.extend(self.recorded_entries)
            else:
                recorded_entries_to_save = self.recorded_entries

            with open(_filepath_params, "w") as f:
                json.dump(state_dict_to_save, f)
            with open(_filepath_entries, "w") as f:
                json.dump(recorded_entries_to_save, f, indent=4)

    def make_snapshot(self, version_name, _path: str = None, ) -> str:
        """
        Make a snapshot of the FileSet.
        The snapshot folder will be named as "version_name", which will be stored in the directory "_path".
        and _path defaults to "{self.directory}/snapshots/".

        This calls self.save().
        :param _path: if not None, a "{version_name}" folder will be created in this directory and the snapshot will be saved there.
        :param version_name: recommended to be a timestamp.
               Note the timestamp string will be compared lexicographically to determine which snapshot is newer.
               The recommended format is "%y%m%d_%H_%M_%S_%f".
        :return:
        """
        snapshot_dir = osp.join(self.directory, "snapshots") if _path is None else _path
        snapshot_inner_dir = osp.join(snapshot_dir, version_name)
        os.makedirs(snapshot_inner_dir, exist_ok=True)
        self.save(snapshot_inner_dir)

        return snapshot_inner_dir

    @staticmethod
    def load_from(path, mode='append', filename_params="FileSet.json", filename_entries="FileSetEntries.json"):
        """

        :param path: the directory of the FileSet.
        :param mode: 'append', 'append-full-load' or 'overwrite'
        :param filename_params:
        :param filename_entries:
        :return:
        """
        if mode not in ['append', 'append-full-load', 'overwrite']:
            raise ValueError(f"Invalid mode {mode}")

        if mode == 'overwrite':
            return FileSet(directory=path, mode=mode)

        _filepath_params = osp.join(path, filename_params)
        _filepath_entries = osp.join(path, filename_entries)
        if not osp.exists(path):
            raise FileNotFoundError(f"Directory {path} not found!")
        if not osp.exists(_filepath_params):
            raise FileNotFoundError(f"File {_filepath_params} not found!")
        if not osp.exists(_filepath_entries):
            raise FileNotFoundError(f"File {_filepath_entries} not found!")

        with open(_filepath_params, "r") as f:
            state_dict = json.load(f)

        if mode == 'append':
            recorded_entries = []
        else:
            with open(_filepath_entries, "r") as f:
                _recorded_entries = json.load(f)
                # convert the list[list[Any...]] to list[FileSetRecordedEntry]
                recorded_entries = [FileSetRecordedEntry(*entry) for entry in _recorded_entries]

        state_dict['recorded_entries'] = recorded_entries

        ret = FileSet(directory=path, state_dict=state_dict, mode=mode)
        return ret

    @staticmethod
    def load_from_snapshot(version_name: str, _path: str = None):
        """
        Load the FileSet from a snapshot.
        This means that the files that now exist in the contents folder must have been covering what's in the snapshot entries.
        Since we don't keep a copy of the contents when making snapshots, when loading them, the contents folder will
        fall back to the state w.r.t. the snapshot entries.
        All files that are not in the snapshot entries will be deleted.
        :param version_name:
        :param _path: the directory of the FileSet. It should contain a "snapshots" folder, in which there should be a folder "{version_name}".
        :return:
        """
        snapshot_dir = osp.join(_path, "snapshots") if _path is not None else "snapshots"
        snapshot_inner_dir = osp.join(snapshot_dir, version_name)
        _filepath_params = osp.join(snapshot_inner_dir, "FileSet.json")
        _filepath_entries = osp.join(snapshot_inner_dir, "FileSetEntries.json")
        if not osp.exists(snapshot_dir):
            raise FileNotFoundError(f"Directory {snapshot_dir} not found!")
        if not osp.exists(snapshot_inner_dir):
            raise FileNotFoundError(f"Directory {snapshot_inner_dir} not found!")
        if not osp.exists(_filepath_params):
            raise FileNotFoundError(f"File {_filepath_params} not found!")
        if not osp.exists(_filepath_entries):
            raise FileNotFoundError(f"File {_filepath_entries} not found!")

        with open(_filepath_params, "r") as f:
            state_dict = json.load(f)

        with open(_filepath_entries, "r") as f:
            _recorded_entries: list[FileSetRecordedEntry] = json.load(f)
            recorded_entries = [FileSetRecordedEntry(*entry) for entry in _recorded_entries]

        state_dict['recorded_entries'] = recorded_entries

        # replace the FileSet.json and FileSetEntries.json in the directory
        shutil.copy(_filepath_params, osp.join(_path, "FileSet.json"))
        shutil.copy(_filepath_entries, osp.join(_path, "FileSetEntries.json"))

        # delete all files that are not in the snapshot entries
        contained_filenames = set([entry.content_filename for entry in recorded_entries])
        contents_dir = osp.join(state_dict['directory'], "contents")
        for filename in os.listdir(contents_dir):
            if filename not in contained_filenames:
                os.remove(osp.join(contents_dir, filename))

        # remove newer snapshots. compare the timestamp metadata of the snapshots.
        for snapshot_name in os.listdir(snapshot_dir):
            # Note: this may change if the snapshot name format changes.
            if snapshot_name > version_name:
                shutil.rmtree(osp.join(snapshot_dir, snapshot_name))

        ret = FileSet(state_dict=state_dict, mode='append-full-load')
        return ret

    def insert(self, entry: FileSetInsertEntry):
        """
        Insert an entry into the FileSet.
        :param entry:
        :return:
        """
        with self.lock:
            # write the content to a file
            filename = self._assign_filename_for(entry)
            contents_folder = osp.join(self.directory, "contents")
            filepath = osp.join(self.directory, "contents", filename)
            # content may be str or bytes
            if isinstance(entry.content, str):
                content = entry.content.encode()
            else:
                content = entry.content

            if not osp.exists(contents_folder):
                os.makedirs(contents_folder, exist_ok=True)
            with open(filepath, "wb") as f:
                f.write(content)

            # take a record
            recorded_entry = FileSetRecordedEntry(
                content_filename=filename,
                url=entry.url,
                title=entry.title,
                download_time=entry.download_time
            )
            self.recorded_entries.append(recorded_entry)

    def _assign_filename_for(self, entry: FileSetInsertEntry):
        """
        Assign a filename for the entry's content.
        :param entry:
        :return:
        """
        filename = f"{self.filename_counter}.html"
        self.filename_counter += 1

        # for the sake of safety.
        while osp.exists(osp.join(self.directory, "contents", filename)):
            filename = f"{self.filename_counter}.html"
            self.filename_counter += 1
        return filename

    def _clear_and_init_directory(self):
        """
        Initialize the directory.
        the contents will be stored in a subdirectory named "contents".

        :return:
        """
        shutil.rmtree(self.directory, ignore_errors=True)
        # clear the directory
        os.makedirs(self.directory, exist_ok=True)
        os.makedirs(osp.join(self.directory, "contents"), exist_ok=True)
        os.makedirs(osp.join(self.directory, "snapshots"), exist_ok=True)


def random_string(length=10):
    ret = ""
    for _ in range(length):
        ret += chr(np.random.randint(0, 26) + ord('a'))
    return ret


def random_insert_entry():
    content = random_string(100)
    url = random_string(10)
    title = random_string(10)
    # take the current time in YY/MM/DD HH:MM:SS format
    download_time = time.strftime("%y/%m/%d %H:%M:%S", time.localtime())
    entry = as_insert_entry(content, url, title, download_time)
    return entry


@logger.catch()
def test1():
    entries = [random_insert_entry() for _ in range(100)]
    fileset = FileSet.load_from("fileset_cache", mode='overwrite')
    for entry in entries:
        fileset.insert(entry)
    fileset.save()
    fileset = FileSet.load_from("fileset_cache", mode='append')
    entries2 = [random_insert_entry() for _ in range(1000)]
    for entry in entries2:
        fileset.insert(entry)
    fileset.save()


@logger.catch()
def play_with_logger():
    a, b, c = 5, 4, 3
    logger.debug(f"a={a}, b={b}, c={c}")
    d = (a + b) * c / 0
    print(a, b, c, d)


@logger.catch()
def test_snapshotting():
    fileset = FileSet.load_from("fileset_cache", mode='overwrite')
    for epoch in range(10):
        entries = [random_insert_entry() for _ in range(10)]
        for entry in entries:
            fileset.insert(entry)
        fileset.make_snapshot(f"epoch_{epoch}")
    fileset.save()

@logger.catch()
def test_snapshot_loading():
    fileset = FileSet.load_from_snapshot("epoch_6", "fileset_cache")
    print(len(fileset.recorded_entries))
    print(fileset.directory)


if __name__ == '__main__':
    # fileset = FileSet.load_from("test1", mode='overwrite')
    # test1()
    # log to sys.stderr, make this thread-safe
    logger.remove()
    logger.add(sink=sys.stderr, level='INFO', enqueue=True)

    # play_with_logger()
    # test_snapshotting()
    test_snapshot_loading()
