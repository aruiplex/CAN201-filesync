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
import time


def send(package):
    # host = cfg["server"]["host"]
    # port = cfg["server"]["port"]
    host = "127.0.0.1"
    ports = cfg["ips"]
    for port in ports:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        send_to_peer_threading = threading.Thread(target=send_to_peer,
                                                    args=(s, host, port, package), name="send_to_peer")
        send_to_peer_threading.start()


def send_to_peer(s: socket, host: str, port: int, package):
    # todo: 不停访问一个 peer
    while True:
        try:
            s.connect((host, port))
        except ConnectionRefusedError:
            time.sleep(0.1)
            continue
        else:
            logger(f"has connect to {host}:{port}", "sender")
            break    
    logger("start send")
    s.send(package)
    s.close()



def send_signal():
    filename = "./share/hello_world"
    with open(filename, "rb") as f:
        data = f.read()
        send(asysio.Package().send(filename, data))


def del_signal():
    del_file_set = {"./share/hello_world"}
    print(del_file_set)
    send(asysio.Package().delete(del_file_set))


def upt_signal():
    with open("test.data", 'r') as f:
        data = f.read()
    package = asysio.Package().update("./share/hello_world", 10, data)
    send(package)


if __name__ == "__main__":
    upt_signal()
