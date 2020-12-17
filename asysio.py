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

ATP: aruix transfer protocol
+------+--------------------------+----------------------------------------------------------------+
| code |       method             |                     description                                |
+------+--------------------------+----------------------------------------------------------------+
|  0?  |        ALI               |  send alive message to check peer get ready to perform action  |
|  1   |        SYN               |  send sync message to identify which file to sync              |
|  2   |        REQ               |  send request message to get messing file                      |
|  3   |        SED               |  send send message to send a whole file                        |
|  4   |        UPT               |  send update message to send a part of whole file              |
|  5   |        DEL               |  send delete messafe to delete a file                          |
+------+--------------------------+----------------------------------------------------------------+

ATP package header: 
 
|--8Bytes-|
+----+----+------+----+
|1234|5678|header|body|
+----+----+------+----+
|    |
|    +body_length
+header_length

header fields:
(* is must)
1. *methods;
2. filename;
3. index;
4. total;

"""
import os
from io import TextIOWrapper
from typing import BinaryIO
from devTool import time_consume
from asys import logger, cfg, db
import gzip
import struct
import asysio
from asysfs import SyncFile
import enum
import math
import hashlib


"""
Methods = enum.Enum("SYN", "DEL", "ALI", "UPT", "SED", "REQ")
"""


def file_manager(filename: str) -> bytes:
    sync_file = SyncFile(filename)
    # this total is total index
    total = math.ceil(sync_file.size / cfg["file_block_size"])
    with open(filename, mode="rb") as f:
        for index in range(total):
            splitter(f, index, total)


def splitter(f: BinaryIO, index: int, total: int) -> bytes:
    file_block_size = cfg["file_block_size"]
    f.seek(index * file_block_size)
    content = f.read(file_block_size)
    return content


def merger(f: TextIOWrapper):
    pass

# 这个版本的类是 里面的所有信息都是 bytes


class Package:
    """build the header for Package
    build a package, all data in package is bytes
    """
    # # header data
    # method = b""
    # filename = b""
    # # package data
    # header_length = 0
    # body_length = 0
    # header = b""
    body = bytearray(b"")

    def build(self, header: dict, body: str):
        self.header = str(header).encode()
        self.body = body.encode()
        self.header_length = len(header)
        self.body_length = len(body)
        return self

    def __wrap(self, header: dict, body: bytes) -> bytes:
        """wrap the package
        """
        header = str(header)
        self.header = header.encode()
        self.body = body
        self.header_length = len(header)
        self.body_length = len(body)
        return struct.pack("!II", self.header_length, self.body_length) + self.header + self.body
        # 另一种写 pack 的方法
        # return self.header_length.to_bytes(
        #     4, "big") + self.body_length.to_bytes(4, "big") + self.header + self.body

    def __unwrap(self, store):
        """已弃用
        unwrap the package from store
        """
        self.header_length, self.body_length = struct.unpack(
            "!II", store[:8])
        self.header = store[8:8 + self.header_length]
        self.header = eval(self.header.decode())
        self.body = store[8 + self.header_length:8 +
                          self.header_length + self.body_length]
        store = store[8 + self.header_length + self.body_length:]
        # if FIN is true, the finish
        FIN = self.body_length == 0 and self.header_length == 0
        return self, store, FIN

    def alive(self):
        self.method = "ALI".encode()
        package = Package().__wrap(self.__dict__, "")
        return package

    def send(self, filename: bytes, data: bytes):
        self.method = "SED".encode()
        self.filename = filename
        package = Package().__wrap(self.__dict__, data)
        return package

    def update(self, filename: bytes, start_index: int, data: bytes):
        self.method = "UPT".encode()
        self.filename = filename
        self.start_index = start_index
        package = Package().__wrap(self.__dict__, data)
        return package

    def sync(self):
        self.method = "SYN".encode()
        package = Package().__wrap(self.__dict__, "")
        return package

    def delete(self, sync_file_set: set):
        """sync_file_list: List<SyncFile>
        """
        self.method = "DEL".encode()
        package = Package().__wrap(header=self.__dict__, body=str(sync_file_set).encode())
        return package

    def request(self, filename: str, start_index: int):
        """The request header of the breakpoint continuation, 
        filename is the broken file, start_index is its last byte
        """
        self.method = "REQ".encode()
        self.filename = filename
        self.start_index = start_index
        package = Package().__wrap(self.__dict__, "")
        return package

    # def finish(self):
    #     package = Package().__wrap("", "")
    #     return package


def data2file(f: TextIOWrapper, index, data: bytes):
    """byte stream to file
    1. low level.
    2. base on directory to create file
    """
    part_size = cfg["file_block_size"]
    logger(f"write file", "asysio")
    # TODO:
    # os.makedirs(os.path.dirname(filename), exist_ok=True)
    f.seek(index * part_size)
    f.write(data.decode())


def file2data(data_file: TextIOWrapper, index: int) -> bytes:
    """byte file to stream 
    1. low level.
    2. base on directory to read file
    """
    part_size = cfg["file_block_size"]
    position = index * part_size
    data_file.seek(position)
    logger(f"read part <{index}> into bytes", "asysio")
    return data_file.read(part_size)


def compress(data: bytes) -> bytes:
    """compress for files and folders
    """
    return gzip.compress(data, cfg["compress_level"])


def decompress(data: bytes) -> bytes:
    """decompress for files and folders
    """
    return gzip.decompress(data)


def get_version(filename: str) -> bytes:
    # block_size = cfg["file_block_size"]
    block_size = 1024*1024
    sync_file = SyncFile(filename)
    total = math.ceil(sync_file.size/block_size)
    version_bytes = bytearray(b"")
    with open(filename, "rb") as f:
        for partion_index in range(total):
            base_index = partion_index*block_size
            for i in range(0, block_size, 1024):
                f.seek(base_index + i)
                version_bytes.extend(f.read(1))
            # logger(version_bytes,"version_bytes: ")
            # logger(hashlib.md5(version_bytes).hexdigest(), f"partion_index: {partion_index}")
            version_bytes = bytearray(b"")


def test1():
    body_in = "hahahahahahaha"
    a = Package()
    package = a.send("helloworld.txt", body_in)
    b = Package()
    b.unwrap(package)
    print(b.__dict__)


def test3():
    filename = "./share/hello_world"
    sync_file = SyncFile(filename)
    with open(file=filename, mode="rb") as f:
        total = math.ceil(sync_file.size / cfg["file_block_size"])
        print("total", total)
        print(splitter(f, 14, 16))


def test_get_version():
    # get_version("./share/hello_world")
    get_version("C:\\Users\\zcrbb\\Downloads\\ideaIU-2020.3.exe")


if __name__ == "__main__":
    # file_manager("./share/hello_world")
    # time_consume(test_get_version)
    test1()
