import uuid
import socket
import threading
from asys import logger, cfg, db
import struct
import asysio
import queue
import math
import os
import json
from queue import Empty
import asystp
import gzip

syn = []


def listener() -> socket:
    """listen on the port and pass the connect socket to the receiver
    """
    n = 1
    host = cfg["server"]["host"]
    port = cfg["server"]["port"]
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, port))
        s.listen()
        logger(f"Server is listening on ATP://{host}:{port} <{n}>", "listener")
        while len(syn) == 0:
            connection, addr = s.accept()
            logger(f"<{n}> Connected by {addr}", "listener")
            # create new thread to receiver
            threading.Thread(target=receiver, args=(
                connection,), name=f"Receiver-{n}").start()
            n += 1
        logger("break", "listener")


def due_send(connection: socket, header: dict, q: queue, start_index=0):
    """it due 2 kinds of head
    1. send, start_index=0
    2. update, start_index=header["start_index"]
    """
    filename = header["filename"]
    notation = "<SED>"
    if start_index != 0:
        notation = "<UPT>"
    logger(f"{notation}{header}", 'due_send')
    stop = []
    # 把正在传的文件记录一下, 文件锁
    transfering_set = set(db["transfering"])
    transfering_set.add(header["filename"])
    # converge list to set, aviod to repeat
    s = set(db["recv_files"])
    s.add(header["filename"])
    db["recv_files"] = list(s)
    data_dump_threading = threading.Thread(
        target=data_dump, args=(header, q, stop, start_index), name=f"{threading.current_thread().name}-data_dump")
    data_dump_threading.start()
    # 不停的收, 放到 queue 里面
    while True:
        receive_bytes = connection.recv(cfg["buffer_size"])
        if not receive_bytes:
            stop.append(1)
            break
        q.put(receive_bytes)
    # 解开文件锁
    data_dump_threading.join()
    # handle decompress
    if filename.endswith(".temp"):
        logger("handle decompress", "due_send")
        with open(filename, "rb") as of:
            with open(filename[:-5], "wb") as f:
                ori_data = of.read()
                data = gzip.decompress(ori_data)
                logger("decompressing", "decompress")
                f.write(data)
        os.remove(filename)
        logger(f"{filename} removed", "due_send")

    transfering_set.discard(header["filename"])
    db["transfering"] = list(transfering_set)
    logger(f"{notation} is finish", "due_send")


def due_request(header):
    filename = header["filename"]
    logger(f"<REQ>{header}", 'due_request')
    if filename not in db["sync_files"]:
        logger(f"<REQ>{filename} is received file.", "due_request")
        return
    with open(filename, "r+b") as f:
        start_index = header["start_index"]
        f.seek(start_index)
        data = f.read()
        package = asysio.Package().update(filename, start_index, data)
        asystp.send(package)
        logger(f"<REQ>{filename} is update", "due_request")


def receiver(connection: socket):
    """receiver due with the message 
    """
    global syn
    buffer_size = cfg["buffer_size"]
    # the first time received data
    store = bytearray(b"")
    # data queue
    q = queue.Queue()
    with connection:
        # receive_bytes is this time received data
        receive_bytes = connection.recv(buffer_size)
        store.extend(receive_bytes)
        header_length, body_length = struct.unpack("!II", store[:8])
        header = eval(store[8:8 + header_length].decode())
        q.put(store[8 + header_length:])

        if header["method"] == "SYN":
            logger(f"<SYN>{header}", 'receiver')

        if header["method"] == "FIN":
            logger(f"<FIN>{header}", 'receiver')
            syn.append("FINISH")

        if header["method"] == "SED":
            due_send(connection, header, q)

        if header["method"] == "UPT":
            start_index = header["start_index"]
            due_send(connection, header, q, start_index)

        if header["method"] == "REQ":
            due_request(header)


def data_dump(header, q: queue.Queue, stop, start_index=0):
    """dump data into file from Queue
    header: transfer header;
    q: data store.
    stop: stop signal.
    start_index: for Discontinued transmission, write into file from a contain point 
    """
    filename = header["filename"]
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    # this is a new file
    if start_index == 0:
        open_mode = "wb"
    else:
        open_mode = "r+b"
    with open(filename, open_mode) as f:
        f.seek(start_index)
        while len(stop) == 0 or not q.empty():
            try:
                content = q.get(block=False, timeout=1)
                f.write(content)
            except queue.Empty:
                continue
            except Exception:
                logger(f"Some error appearance: {Exception}.", "data_dump")
    logger(f"{filename} finish write in.", "data_dump")
