import uuid
import socket
import threading
from asys import logger, cfg
import struct
from asysio import Package
import math
import os
import json

syn = True
peers = []


def listener() -> socket:
    n = 1
    host = cfg["server"]["host"]
    port = cfg["server"]["port"]
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, port))
        s.listen()
        logger(f"<{n}> Listening on ATP://{host}:{port}", "listener")
        while syn:
            connection, addr = s.accept()
            logger(f"<{n}> Connected by {addr}", "listener")
            # create new thread to re
            threading.Thread(target=receiver, args=(
                connection,)).start()
            n = n+1
        logger("break", "listener")


def receiver(connection: socket):
    global syn, peers
    buffer_size = cfg["buffer_size"]
    store = b""
    with connection:
        while True:
            # receive_bytes is this time receive data
            receive_bytes = connection.recv(buffer_size)
            # if there is no package then break
            if not receive_bytes:
                break
            store += receive_bytes
            # if it is common signal
            package, store, FIN = Package().unwrap(store)
            # if it is finish signal
            if FIN:
                syn = False
                logger("break", "receiver")
                break
            package_analysis(package)


def package_analysis(package: Package):
    if package.method == b"SED":
        logger("i am here")
        with open("."+package.filename, "wb") as f:
            f.write(package.body)
    # elif package.method == b"SYC":
    #     pass
    


if __name__ == "__main__":
    listener_t = threading.Thread(
        target=listener, name="listener", daemon=True)
    listener_t.start()
    listener_t.join()
    logger("退出")
