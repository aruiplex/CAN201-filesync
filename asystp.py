"""
This file contains all functions related to the network transfer.

send(data: bytes) -> None
1. low-level function 
2. can only send bytes stream. 
3. compress data. 
4. not automatically split into small packages.

receive(data: bytes) -> None
1. it is a low-level function 
2. can only receive bytes stream. 
3. decompress data.
4. not automatically merge small packages to file.

sender(data: file) -> None
1. high-level function. 
2. pass a file, send this whole file.

receiver() -> None
1. high-level function. 
2. automatically merge small packages to file.

send_header() -> None
1. send the header of 

send_header() -> None

"""

import socket
import threading
from asys import logger, cfg
import struct
import asysio
import math
import devTool
import os


def send(package):
    buffer_size = cfg["buffer_size"]
    host = cfg["server"]["host"]
    port = cfg["server"]["port"]
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))
        logger(f"has connect to {host}:{port}", "sender")
        s.send(package)


def main():
    sender1_t = threading.Thread(
        target=send, name="sender1", args=("127.0.0.1", 20000, "./share/hello_world"))
    sender1_t.start()
    # sender2_t = threading.Thread(
    #     target=sender, name="sender1", args=("127.0.0.1", 20000, "./hello_world"))
    # sender2_t.start()

    sender1_t.join()
    # sender2_t.join()


def send_signal():
    filename = "./share/hello_world"
    with open(filename, "r") as f:
        data = f.read()
        send(asysio.Package().send(filename, data))


def del_signal():
    del_file_set = {"./share/hello_world"}
    print(del_file_set)
    send(asysio.Package().delete(del_file_set))


def upt_signal():
    with open("test.data",'r') as f:
        data = f.read()
    package = asysio.Package().update("./share/hello_world", 10, data)
    send(package)


if __name__ == "__main__":
    upt_signal()
