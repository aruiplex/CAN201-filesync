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
from asys import logger, cfg, db
import struct
import asysio
import math
import devTool
import os
import time
import asysfs


def retransfer():
    transfering_set = set(db["transfering"])
    # nothing to retransfer
    if len(transfering_set) == 0:
        return

    logger(f"retransfer files {transfering_set}", "retransfer")
    for filename in transfering_set:
        try:
            sync_file = asysfs.SyncFile(filename)
            logger(
                f"starting continue transfer: {sync_file.name}", "Discontinued transmission")
            package = asysio.Package().request(sync_file.name, sync_file.size)
            send(package)
        except FileNotFoundError:
            logger(
                f"starting continue transfer for a new file: {filename}", "Discontinued transmission")
            package = asysio.Package().request(filename, 0)
            send(package)
    transfering_set.discard(filename)
    db["transfering"] = transfering_set


def send(package):
    # host = "127.0.0.1"
    hosts = cfg["ips"]
    logger(hosts, "hosts")
    port = int(cfg["port"])
    logger(port, "port")
    for host in hosts:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        send_to_peer_threading = threading.Thread(target=__send_to_peer,
                                                  args=(s, host, port, package), name="send_to_peer")
        send_to_peer_threading.start()


def __send_to_peer(s: socket, host: str, port: int, package):
    while True:
        try:
            s.connect((host, port))
        except ConnectionRefusedError:
            time.sleep(0.1)
            continue
        else:
            logger(f"has connect to {host}:{port}", "sender")
            break
    s.send(package)
    s.close()
    logger("File send finish", "sender")
