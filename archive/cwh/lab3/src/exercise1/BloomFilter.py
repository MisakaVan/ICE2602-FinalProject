import math

from lib.Bitarray import Bitarray


# GeneralHashFunctions
def BKDRHash(key):
    seed = 131  # 31 131 1313 13131 131313 etc..
    hash = 0
    for i in range(len(key)):
        hash = (hash * seed) + ord(key[i])
    return hash


def hash_yielder(size: int):
    def BKDRHash_of_seed(_seed):
        def BKDRHash(key, seed=_seed):
            _hash = 0
            for i in range(len(key)):
                _hash = (_hash * seed) + ord(key[i])
            return _hash

        return BKDRHash

    seed = 131
    p = 3
    for i in range(size):
        yield BKDRHash_of_seed(seed)
        seed = seed * 10 + p
        p = 4 - p


class BloomFilter:
    def __init__(self, size: int, hash_func_count):
        self.hash_func_count = hash_func_count
        self.size: int = size
        self._bitarray: Bitarray = Bitarray(size)

        self.HASH_FUNCTIONS = list(hash_yielder(self.hash_func_count))

    def add(self, s: str):
        for idx in range(self.hash_func_count):
            res = self.HASH_FUNCTIONS[idx](s)
            self._bitarray.set(res % self.size)

    def __contains__(self, item):
        for idx in range(self.hash_func_count):
            res = self.HASH_FUNCTIONS[idx](item)
            if not self._bitarray.get(res % self.size):
                return False
        return True

    def clear(self):
        self._bitarray = Bitarray(self.size)


def suggested_bloom_filter_args(_capacity: int, _error_rate: float):
    # https://blog.csdn.net/dan_teng/article/details/127424479
    size = int(-_capacity * math.log(_error_rate) / (math.log(2) ** 2))
    func_count = int(math.log(2) * size / _capacity)
    return size, func_count


if __name__ == "__main__":
    funcs = list(hash_yielder(5))
    for func in funcs:
        _ = func('123')
