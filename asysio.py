import os
from asys import logger, cfg, db
import gzip
import struct
import asysio


"""
This file contains all functions related to the inputs outputs and stream operations

data2file(data: bytes) -> file
1. low level function
2. write bytes stream into file
3. base on directory to read file

file2data(file: str) -> bytes
1. low level.
2. byte file to stream 
3. base on directory to read file

compress(data: bytes) -> bytes
1. compress for bytes stream
2. Data to be compressed

decompress(data: bytes) -> bytes
1. decompress for bytes stream
2. Data to be decompressed

spliter(file: str, index: int) -> bytes
1. low level function
2. pass file and index to seek part to read into memory


+------------------+--------------------------
|                  | r   r+   w   w+   a   a+
|------------------+--------------------------
|read              | +   +        +        +
|write             |     +    +   +    +   +
|write after seek  |     +    +   +
|create            |          +   +    +   +
|truncate          |          +   +
|position at start | +   +    +   +
|position at end   |                   +   +
+------------------+--------------------------
"""


# class asysio():
#     def split(self, filename: str, index: int) -> bytes:
#         with open(filename, "r") as file_:
#             file_.seek()

#     def data2file(self, filename: str, data: bytes):
#         """byte stream to file
#         1. low level.
#         2. base on directory to create file
#         """
#         os.makedirs(os.path.dirname(filename), exist_ok=True)
#         with open(filename, "w") as f:
#             f.write(data)
#         logger(f"write file in {filename}", "asysio")

#     def file2data(self, filename) -> bytes:
#         """byte file to stream
#         1. low level.
#         2. base on directory to read file
#         """
#         with open(file=filename, mode="rb") as data_file:
#             logger(f"read {filename} into bytes", "asysio")
#             return data_file.read()

#     def compress(self, data: bytes) -> bytes:
#         """compress for files and folders
#         """
#         return gzip.compress(data, cfg["compress_level"])

#     def decompress(self, data: bytes) -> bytes:
#         """decompress for files and folders
#         """
#         return gzip.decompress(data)


def spliter(filename: str, index: int) -> bytes:
    with open(filename, "r") as file_:
        file_.seek()


"""
ATP: aruix transfer protocol
+------+--------------------------+----------------------------------------------------------------+
| code |       method             |                     description                                |
+------+--------------------------+----------------------------------------------------------------+
|  0   |        ALIVE             |  send alive message to check peer get ready to perform action  |
|  1   |        SYNC              |  send sync message to identify which file to sync              |
|  2   |        REQUEST           |  send request message to get messing file                      |
|  3   |        SEND              |  send send message to send a whole file                        |
|  4   |        UPDATE            |  send update message to send a part of whole file              |
|  5   |        DELETE            |  send delete messafe to delete a file                          |
+------+--------------------------+----------------------------------------------------------------+

ATP package header: 
|----13 B--------|    
+-+----+----+----+--------+----+
|1|2345|6789|abcd|filename|data|
+-+----+----+----+--------+----+
| |    |    |filename_length
| |    |total 
| |index
|method

"""


def unwarp(package):
    """unwrap the package
    """
    method, index, total, filename_len = struct.unpack(
        "!BIII", package[:13])
    filename = package[13:13+filename_len]
    data = package[13+filename_len:]
    return method, index, total, filename, data


class Wrapper():
    """
    """
    #
    method = 0
    # total package number
    total = 0
    # filename of transfer data
    filename = b""

    def __init__(self, method: int, filename: str, total: int):
        self.method = method
        self.total = total
        # self.size = size
        self.filename = filename
        # self.data = data.encode()

    def wrap(self, index: bytes, data: bytes) -> bytes:
        """wrap the package
        """
        filename_len = len(self.filename)
        header = struct.pack("!BIII", self.method, index,
                             self.total, filename_len)
        package = header + self.filename + data
        return package

    @classmethod
    def unwarp(cls, package):
        """unwrap the package 
        """
        self.method, index, self.total, filename_len = struct.unpack(
            "!BIII", package[:13])
        self.filename = package[13:13+filename_len]
        data = package[13+filename_len:]
        return data


def alive():
    method = 0
    return struct.pack("!B", method)

# def desync():
#     asys

def sync(index: bytes, total: int, data: bytes):
    method = 1
    header = struct.pack("!BIII", method, index,
                         total)
    package = header + data
    return package


def request(filename: str):
    method = 2
    filename_len = len(filename)
    header = struct.pack("!BI", method, filename_len)
    package = header+filename
    return package


def send(filename, index, total, data):
    method = 3
    filename_len = len(filename)
    header = struct.pack("!BIII", method, index,
                         total, filename_len)
    package = header + filename + data
    return package


def update(filename, index, total, data):
    method = 4


def delete(filename):
    method = 5
    filename_len = len(filename)
    header = struct.pack("!BI", method, filename_len)
    package = header + filename
    return package


def unwarp(package):
    """unwrap the package 
    """



    method, index, total, filename_len = struct.unpack(
        "!BIII", package[:13])
    self.filename = package[13:13+filename_len]
    data = package[13+filename_len:]
    return data

def data2file(filename: str, index, data: bytes):
    """byte stream to file
    1. low level.
    2. base on directory to create file
    """
    part_size = cfg["buffer_size"]
    logger(f"write file in {filename}", "asysio")
    print(f"--------------{filename}-----------------")
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "w") as f:
        f.seek(index * part_size)
        f.write(data.decode())


def file2data(filename, index: int) -> bytes:
    """byte file to stream 
    1. low level.
    2. base on directory to read file
    """
    part_size = cfg["buffer_size"]
    position = index * part_size
    with open(file=filename, mode="rb") as data_file:
        data_file.seek(position)
        logger(f"read {filename} part <{index}> into bytes", "asysio")
        return data_file.read(part_size)


def compress(data: bytes) -> bytes:
    """compress for files and folders
    """
    return gzip.compress(data, cfg["compress_level"])


def decompress(data: bytes) -> bytes:
    """decompress for files and folders
    """
    return gzip.decompress(data)
