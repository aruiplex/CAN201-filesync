import uuid
import socket
import threading
from asys import logger, cfg
import struct
import asysio
import queue
import math
import os
import json
from queue import Empty

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
            n = n + 1
        logger("break", "listener")


body = bytearray(b"")


def receiver(connection: socket):
    global syn, peers, body
    buffer_size = cfg["buffer_size"]
    store = bytearray(b"")
    debug_i = 0
    q = queue.Queue()
    with connection:
        # receive_bytes is this time receive data
        receive_bytes = connection.recv(buffer_size)
        store.extend(receive_bytes)
        header_length, body_length = struct.unpack("!II", store[:8])
        header = eval(store[8:8 + header_length].decode())
        q.put(store[8 + header_length:])

        if header["method"] == b"SED":
            logger(f"<SED>{header}", 'Header')
            # with open(header["filename"], "wb") as f:
            stop = []
            data_dump_threading = threading.Thread(
                target=data_dump, args=(header, q, stop), name="data_dump")
            data_dump_threading.start()
            while True:
                receive_bytes = connection.recv(buffer_size)
                if not receive_bytes:
                    stop.append(1)
                    break
                q.put(receive_bytes)
                logger(f"已经接收了<{debug_i}>轮", "data_dump")
                debug_i += 1

        if header["method"] == b"UPT":
            logger(f"<UPT>: {header}", 'Header')
            with open(header["filename"], "r+b") as f:
                start_index = header["start_index"]
                logger(f"start_index: {start_index}", "update")
                f.seek(start_index, 0)
                while True:
                    receive_bytes = connection.recv(buffer_size)
                    q.put(receive_bytes)
                    logger(q)
                    try:
                        content = q.get(block=True, timeout=0.5)
                        f.write(content)
                        logger(f"已经接收了<{debug_i}>轮", "data_dump")
                        debug_i += 1
                        if not receive_bytes:
                            break
                    except Empty:
                        logger(Empty, "Empty")

        if header["method"] == b"DEL":
            logger(f"<DEL>: {header}", 'Header')
            while True:
                logger(f"已经接收了<{debug_i}>轮", "data_dump")
                debug_i += 1
                receive_bytes = connection.recv(buffer_size)
                if not receive_bytes:
                    break
                q.put(receive_bytes)
            del_file_set = eval(q.get())
            logger(f"{del_file_set}", "delete")
            for del_file in del_file_set:
                os.remove(del_file)

        if header["method"] == b"SYN":
            logger(f"<SYN>: {header}", 'Header')


def data_dump(header, q: queue.Queue, stop):
    with open(header["filename"], "wb") as f:
        while len(stop) == 0 or not q.empty():
            try:
                dongxi = q.get(block=False, timeout=1)
                f.write(dongxi)
            except queue.Empty:
                logger(f"Queue empty", "data_dump")
            except Exception:
                logger(f"Some error appearance: {Exception}.", "data_dump")


def package_analysis(package: asysio.Package):
    if package.method == b"SED":
        logger("i am here")
        with open("." + package.filename, "wb") as f:
            f.write(package.body)
    # elif package.method == b"SYC":
    #     pass


if __name__ == "__main__":
    listener_t = threading.Thread(
        target=listener, name="listener", daemon=True)
    listener_t.start()
    listener_t.join()
    logger("退出")
