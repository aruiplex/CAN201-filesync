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
+------+-------------------+----------------------------------------------------------------+
| code |       method      |                     description                                |
+------+-------------------+----------------------------------------------------------------+
|  1   |        REQ        |  send request message to get messing file                      |
|  2   |        SED        |  send send message to send a whole file                        |
|  3   |        UPT        |  send update message to send a part of whole file              |
|  4   |        DEL        |  send delete messafe to delete a file                          |
+------+-------------------+----------------------------------------------------------------+

ATP package header: 
 
|--8Bytes-|
+----+----+------------+------------------------------------+
|1234|5678|   header   |                 body               |
+----+----+------------+------------------------------------+
|    |
|    +body_length
+header_length

header fields:
(* is must)
1. *methods;
2. filename;
3. start index;


"""
import os
from asys import logger, cfg, db
import gzip
import struct
from Crypto.Cipher import AES
import zlib

"""
Methods = enum.Enum("SYN", "DEL", "ALI", "UPT", "SED", "REQ")
"""


def compress(new_file: str) -> str:
    """ 
    open the original file and create a new compressed file
    """
    temp_filename = new_file + ".temp"
    # write down protect, avoid file system track
    recv_files = set(db["recv_files"])
    recv_files.add(temp_filename)
    db["recv_files"] = recv_files
    with open(new_file, "rb") as infile:
        with open(temp_filename, "wb") as zip_output:
            compress_obj = zlib.compressobj(1)
            data = infile.read(10240)
            while data:
                zip_output.write(compress_obj.compress(data))
                data = infile.read(10240)
            zip_output.write(compress_obj.flush())
    return temp_filename


def decompress(filename):
    real_name = filename[:-5]
    logger("handle decompress", "due_send")
    recv_files = set(db["recv_files"])
    recv_files.add(real_name)
    db["recv_files"] = recv_files
    with open(filename, "rb") as file_name:
        with open(real_name, "wb") as endFile:
            decompress_obj = zlib.decompressobj()
            data = file_name.read(10240)
            logger("decompressing", "decompress")
            while data:
                endFile.write(decompress_obj.decompress(data))
                data = file_name.read(10240)
    os.remove(filename)
    logger(f"{filename} removed", "due_send")


def add_to_16(value: bytes):
    while len(value) % 16 != 0:
        value += (b'\0')
    return value


def encrypt(key: str, text: bytes):
    aes = AES.new(add_to_16(key.encode()), AES.MODE_ECB)
    encrypt_aes = aes.encrypt(add_to_16(text))
    return encrypt_aes


def decrypt(key: str, text: bytes):
    aes = AES.new(add_to_16(key.encode()), AES.MODE_ECB)
    decrypted_text = aes.decrypt(text).replace(b'\0', b'')
    return decrypted_text


class Package:
    """wrap the header and data into a package base on the format
    1. class variables are headers;
    2. class functions are constructors of header and body 
    """
    body = bytearray(b"")

    def build(self, header: dict, body: str):
        self.header = str(header).encode()
        self.body = body.encode()
        self.header_length = len(header)
        self.body_length = len(body)
        return self

    def __wrap(self, header: dict, body: bytes) -> bytes:
        """wrap the package
        1. header: MUST BE DICT (str)
        2. data: MUST BE BYTES
        """
        header = str(header).encode()
        self.header = header
        self.body = body
        self.header_length = len(header)
        self.body_length = len(body)
        return struct.pack("!II", self.header_length, self.body_length) + self.header + self.body

    def send(self, filename: bytes, data: bytes):
        self.method = "SED"
        self.filename = filename
        package = Package().__wrap(self.__dict__, data)
        return package

    def update(self, filename: bytes, start_index: int, data: bytes):
        self.method = "UPT"
        self.filename = filename
        self.start_index = start_index
        package = Package().__wrap(self.__dict__, data)
        return package

    def request(self, filename: bytes, start_index: int):
        """The request header of the breakpoint continuation, 
        1. filename is the broken file, 
        2. start_index is its last byte
        """
        self.method = "REQ"
        self.filename = filename
        self.start_index = start_index
        package = Package().__wrap(self.__dict__, b"")
        return package

    def alive(self):
        """Deprecated
        """
        self.method = "ALI"
        package = Package().__wrap(self.__dict__, "")
        return package

    def sync(self):
        """Deprecated
        """
        self.method = "SYN"
        package = Package().__wrap(self.__dict__, "")
        return package
