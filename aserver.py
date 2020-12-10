import uuid
import socket
import threading
from asys import logger, cfg
import struct
import asysio
import math
import os

syn = True
peers = []


def listener() -> socket:
    n = 1
    host = cfg["server"]["host"]
    port = cfg["server"]["port"]
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, port))
        s.listen()
        while syn:
            connection, addr = s.accept()
            logger(f"<{n}> Connected by {addr}", "listener")
            threading.Thread(target=receiver, args=(
                connection,)).start()
            n = n+1
        logger("break", "listener")


def receiver(connection: socket):
    global syn, peers
    buffer_size = cfg["buffer_size"] + 13
    with connection:
        while True:
            package = connection.recv(buffer_size)
            # if there is no package
            if not package:
                break
            # if it is finish signal
            if package == b"FIN":
                syn = False
                logger("break", "receiver")
                break
            # if it is common signal
            method = struct.unpack("!B", package[:1])
            if method == 0:
                # know this peer is online
                peers.add(connection)
            # if method == 1:

            # if method == 2:
            # if method == 3:
            # if method == 4:
            # if method == 5:
            #     pass

            method, index, total, filename, data = asysio.unwarp(package)
            asysio.data2file(filename, index, data)


if __name__ == "__main__":
    listener_t = threading.Thread(
        target=listener, name="listener", daemon=True)
    listener_t.start()
    listener_t.join()
    logger("退出")
