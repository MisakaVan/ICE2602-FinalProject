import logging
import random
import string
import time

from BloomFilter import *


def timeit(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        return end_time - start_time, result

    return wrapper


def random_string(length):
    chars = string.ascii_letters + string.digits
    ret = ''
    for i in range(length):
        ret += random.choice(chars)

    return ret


def make_random_string_list(length):
    return [random_string(32) for _ in range(length)]


def make_random_string_list_plus(length):
    return [random_string(random.randint(8, 64)) for _ in range(length)]


string_list1 = [random_string(16) for _ in range(5)]
string_list2 = [random_string(16) for _ in range(5)]


def test_bloomfilter1():
    bloom_filter = BloomFilter(size=10000)
    for s in string_list1:
        bloom_filter.add(s)
    for s in string_list1:
        assert s in bloom_filter

    for s in string_list2:
        print(s in bloom_filter)


def test_bloomfilter2():
    """ false positive? """
    string_count = 1000
    l1 = make_random_string_list(string_count)
    l2 = make_random_string_list(string_count)
    bf = BloomFilter(size=300000)
    record_set = set(l1)

    logging.info(f"Initialization over")
    for s in l1:
        bf.add(s)
    logging.info(f"Testing on l2")
    count = 0
    for s in l2:
        if s in bf and s not in record_set:
            count += 1
    logging.info(f"{count} out of {string_count} strings are false positive.")


def make_geometric_seq(start, ratio, count):
    ret = [start]
    for i in range(count - 1):
        start = int(start * ratio)
        ret.append(start)
    return ret


def test_bloomfilter_false_positive_rate():
    k_range = range(1, 11)
    slots_range = make_geometric_seq(1000, 1.5, 5)
    strs_range = make_geometric_seq(100, 1.5, 10)
    str_count = strs_range[-1]
    str_insert_list = make_random_string_list(str_count)
    str_test_list = make_random_string_list(10000)
    str_test_set = set(str_test_list)

    for k in k_range:
        for size in slots_range:
            _test_bloomfilter_fp_rate(k, size, str_insert_list, str_test_list, strs_range)


def _test_bloomfilter_fp_rate(k, size, str_insert_list, str_test_list, strs_range):
    logging.info(f"testing on BloomFilter(size={size}, hash_func_count={k})")
    bf = BloomFilter(size=size, hash_func_count=k)
    insert_set = set()
    prev_item_idx = 0
    for cur_item_idx in strs_range:
        for i in range(prev_item_idx, cur_item_idx):
            bf.add(str_insert_list[i])
            insert_set.add(str_insert_list[i])
        prev_item_idx = cur_item_idx

        false_count = 0
        for test_item in str_test_list:
            if test_item not in insert_set and test_item in bf:
                false_count += 1

        logging.info(f"{cur_item_idx:>5} strs inserted.\tTested {false_count / len(str_test_list):.6f} false positive.")


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
    # test_bloomfilter_false_positive_rate()
    logging.info("Starting test")

    str_insert_list = make_random_string_list_plus(30000)
    str_test_list = make_random_string_list_plus(10000)

    logging.info("Init over")

    capacity = 10000
    error_rate = 1e-5
    size, func_count = suggested_bloom_filter_args(_capacity=capacity, _error_rate=error_rate)
    logging.info(f"BloomFilter expected to hold {capacity} items with error rate {error_rate:}.")
    logging.info(f"Suggested {size} slots with {func_count} hash functions.")

    _test_bloomfilter_fp_rate(
        func_count,
        size,
        str_insert_list,
        str_test_list,
        [30, 300, 600, 1000, 3000, 6000, 10000, 12000, 15000, 20000, 25000, 30000,]
    )
