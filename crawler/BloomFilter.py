import json

import numpy as np
import math
import os.path as osp
import os

import threading


class BKDRHashGenerator:
    def __init__(self, size):
        self.length = size
        self.seed = 131
        self.p = 3
        self.count = 0

    def __next__(self):
        if self.count == self.length:
            raise StopIteration

        def BKDRHash(key, seed=self.seed):
            _hash = 0
            for i in range(len(key)):
                _hash = (_hash * seed) + ord(key[i])
            return _hash

        self.seed = self.seed * 10 + self.p
        self.p = 4 - self.p
        self.count += 1
        return BKDRHash

    def __iter__(self):
        return self


class BitArray:
    """
    BitArray implemented with Bytearray
    """

    def __init__(self, _size: int = 0, _bytearray=None):
        """
        size: the size of the bytearray
        """
        if _bytearray is not None:
            self.bytearray = _bytearray
            self.size = len(_bytearray) * 8

        else:
            assert _size > 0
            # make size a multiple of 8
            byte_count = math.ceil(_size / 8.)
            self.bytearray = bytearray(byte_count)
            self.size = byte_count * 8

    def set(self, n):
        """
        Sets the nth element of the bitarray
        """
        index = int(n / 8)
        position = n % 8
        self.bytearray[index] = self.bytearray[index] | 1 << (7 - position)

    def get(self, n):
        """
        Gets the nth element of the bitarray
        """
        index = n // 8
        position = n % 8
        return (self.bytearray[index] & (1 << (7 - position))) > 0

    def save(self, path, filename="bitarray.npy"):
        """
        Save the bitarray to a file
        """
        _dir = osp.join(path, filename)
        np.save(_dir, self.bytearray)

    @staticmethod
    def load(path, filename="bitarray.npy"):
        """
        Load the bitarray from a file
        """
        _dir = osp.join(path, filename)
        if not osp.exists(_dir):
            raise FileNotFoundError(f"File {_dir} not found!")
        _bytearray = np.load(_dir)
        return BitArray(_bytearray=_bytearray)


class BloomFilter:
    """
    BloomFilter implemented with BitArray
    """

    def __init__(self, size, hash_num, bitarray=None):
        """
        size: the size of the bytearray
        hash_num: the number of hash functions
        """
        self.lock = threading.Lock()

        self.size = size
        self.hash_num = hash_num
        if bitarray is not None:
            self.bitarray = bitarray
        else:
            self.bitarray = BitArray(size)
        self.hash_funcs = list(BKDRHashGenerator(hash_num))

    def add(self, key):
        """
        Add a key to the BloomFilter
        """
        with self.lock:
            for hash_func in self.hash_funcs:
                self.bitarray.set(hash_func(key) % self.size)

    def __contains__(self, key):
        """
        Check if the key is in the BloomFilter
        """
        with self.lock:
            for hash_func in self.hash_funcs:
                if not self.bitarray.get(hash_func(key) % self.size):
                    return False
        return True

    def __str__(self):
        return f"BloomFilter(size={self.size}, hash_num={self.hash_num})"

    __repr__ = __str__


    def as_state_dict(self):
        return {
            "size": self.size,
            "hash_num": self.hash_num,
            "bitarray": self.bitarray
        }

    @staticmethod
    def load_from(path, filename="BloomFilter.json"):
        _filepath = osp.join(path, filename)
        _bitarray_dir = osp.join(path, ".bitarray")
        if not osp.exists(_filepath):
            raise FileNotFoundError(f"File {_filepath} not found!")
        if not osp.exists(_bitarray_dir):
            raise FileNotFoundError(f"File {_bitarray_dir} not found!")
        with open(_filepath, "r") as f:
            state_dict = json.load(f)

        bitarray = BitArray.load(_bitarray_dir)
        ret = BloomFilter(size=state_dict["size"], hash_num=state_dict["hash_num"], bitarray=bitarray)
        return ret

    def save_to(self, path, filename="BloomFilter.json"):
        """
        Save the BloomFilter to a directory. The bitarray is saved as another file.
        :param path:
        :param filename:
        :return:
        """
        _filepath = osp.join(path, filename)
        _bitarray_dir = osp.join(path, ".bitarray")
        if not osp.exists(path):
            os.makedirs(path)
        if not osp.exists(_bitarray_dir):
            os.makedirs(_bitarray_dir)

        with self.lock:
            state_dict = self.as_state_dict()
            state_dict_to_json = {k: v for k, v in state_dict.items() if k != "bitarray"}
            with open(_filepath, "w") as f:
                json.dump(state_dict_to_json, f)
                
            self.bitarray.save(_bitarray_dir)

    @staticmethod
    def best_args(capacity, error_rate):
        size = int(-capacity * math.log(error_rate) / (math.log(2) ** 2))
        func_count = int(math.log(2) * size / capacity)
        return size, func_count


def bloom_filter_maker(capacity, error_rate):
    size, hash_func_count = BloomFilter.best_args(capacity, error_rate)
    return BloomFilter(size, hash_func_count)


def test_best_args():
    size, hash_funcs = BloomFilter.best_args(capacity=1000000, error_rate=1e-6)
    print(f"Space needed (MB): {size / 8 / 1024 / 1024}")
    print(f"Hash functions needed: {hash_funcs}")


if __name__ == "__main__":
    bf_save_dir = "./.test_cache"
    bf = BloomFilter.load_from(bf_save_dir)
    print(bf)
    print("hello" in bf)
    print("world" in bf)
    bf.add("hello")
    print("hello" in bf)
    bf.save_to(bf_save_dir)
