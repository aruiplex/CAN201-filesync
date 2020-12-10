import os
from asys import logger, cfg, db
import gzip
import struct
import asysio
from asysfs import SyncFile
import enum

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


Methods = enum.Enum("SYN", "DEL", "ALI", "UPT", "SED", "REQ")


def spliter(filename: str, index: int) -> bytes:
    with open(filename, "r") as file_:
        file_.seek()


class Header():
    """build the header for Package
    """
    method = b""

    def __init__(self):
        pass

    def alive(self):
        self.method = "ALI".encode()
        return self

    def send(self, index: int, total: int, filename: str):
        self.method = "SED".encode()
        return self

    def sync(self):
        self.method = "SYN".encode()
        return self

    def delete(self, sync_file_list: list):
        """sync_file_list: List<SyncFile>
        """
        self.method = "DEL".encode()
        return self

    def request(self):
        self.method = "REQ".encode()
        return self


class Package():
    """build a package
    """
    header_length = 0
    body_length = 0
    header = b""
    body = b""

    # def __init__(self, header: dict, body: str):
    #     self.header = str(header).encode()
    #     self.body = body.encode()
    #     self.header_length = len(header)
    #     self.body_length = len(body)

    def wrap(self, header: dict, body: str) -> bytes:
        """wrap the package
        """
        header = str(header)
        self.header = header.encode()
        self.body = body.encode()
        self.header_length = len(header)
        self.body_length = len(body)
        return struct.pack("!II", self.header_length, self.body_length) + self.header + self.body
        # return self.header_length.to_bytes(
        #     4, "big") + self.body_length.to_bytes(4, "big") + self.header + self.body

    def unwarp(self, package):
        """unwrap the package 
        """
        self.header_length, self.body_length = struct.unpack(
            "!II", package[:8])
        self.header = package[8:8+self.header_length]
        self.body = package[8+self.header_length:]


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


if __name__ == "__main__":
    header_in = {
        "filename": "helloworld.txt",
        "index": 1,
        "total": 10,
        "size": 114514,
        "time": 1414815
    }
    body_in = "hahahahahahaha"
    a = Package()
    package = a.wrap(header_in, body_in)
    b = Package()
    b.unwarp(package)
    print(b.__dict__)
