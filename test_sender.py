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


def sender(method: int, filename):

    if method == 0:
        """
        |  0   |        ALIVE             |  send alive message to check peer get ready to perform action  |
        """
        # send(0, "")
        pass
    if method == 1:
        """
        |  1   |        SYNC              |  send sync message (db.json) to identify which file to sync    |
        """
        filename = cfg["db_file"]

    if method == 2:
        """
        |  2   |        REQUEST           |  send request message to get messing file                      |
        """
        pass
    if method == 3:
        """
        |  3   |        SEND              |  send send message to send a whole file                        |
        """
        pass
    if method == 4:
        """
        |  4   |        UPDATE            |  send update message to send a part of whole file              |
        """
        pass
    if method == 5:
        """
        |  5   |        DELETE            |  send delete messafe to delete a file                          |
        """
        pass




def send():
    buffer_size = cfg["buffer_size"]
    host = cfg["server"]["host"]
    port = cfg["server"]["port"]
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))
        logger(f"has connect to {host}:{port}", "sender")
        asysio.alive()
    

def main():
    sender1_t = threading.Thread(
        target=sender, name="sender1", args=("127.0.0.1", 20000, "./sender/hello_world"))
    sender1_t.start()
    # sender2_t = threading.Thread(
    #     target=sender, name="sender1", args=("127.0.0.1", 20000, "./hello_world"))
    # sender2_t.start()

    sender1_t.join()
    # sender2_t.join()


# def que_ren(data1):
    # print(len(data1))
    # print(SyncFile("./good_morning").__dict__)
    # # print(len(data2))
    # print(Sync_file("./hello_world").__dict__)

if __name__ == "__main__":
    send()