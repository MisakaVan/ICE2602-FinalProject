# SJTU EE208

import math


class Bitarray:
    def __init__(self, size: int):
        """ Create a bit array of a specific size """
        self.size = size
        self.bitarray = bytearray(math.ceil(size / 8.))

    def set(self, n: int):
        """ Sets the nth element of the bitarray """

        index = int(n / 8)
        position = n % 8
        self.bitarray[index] = self.bitarray[index] | 1 << (7 - position)

    def get(self, n: int) -> bool:
        """ Gets the nth element of the bitarray """

        index = n // 8
        position = n % 8
        return (self.bitarray[index] & (1 << (7 - position))) > 0





def test_bloomfilter():
    raise NotImplementedError


if __name__ == "__main__":
    bitarray_obj = Bitarray(32000)
    for i in range(5):
        print(f"Setting index {i:d} of bitarray ..")
        bitarray_obj.set(i)
        print(f"bitarray[{i:d}] = {bitarray_obj.get(i):d}")
