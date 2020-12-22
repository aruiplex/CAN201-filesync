import socket
import threading
from asys import logger, cfg, db
import struct
import asysio
import queue
import os
import asystp

syn = []


def listener() -> socket:
    """listen on the port and pass the connect socket to the receiver
    """
    n = 1
    port = cfg["server"]["port"]
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", port))
        s.listen(6)
        logger(f"Server is listening on ATP://127.0.0.1:{port}", "listener")
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
    notation = "rec<SED>"
    if start_index != 0:
        notation = "rec<UPT>"
    logger(f"{notation}{header}", 'due_send')
    stop = []
    # Record the file being transferred, file lock
    transfering_set = set(db["transfering"])
    transfering_set.add(header["filename"])
    db["transfering"] = transfering_set
    # converge list to set, aviod to repeat
    s = set(db["recv_files"])
    s.add(header["filename"])
    db["recv_files"] = list(s)
    data_dump_threading = threading.Thread(
        target=data_dump, args=(header, q, stop, start_index), name=f"{threading.current_thread().name}-dump")
    data_dump_threading.start()
    # Keep receiving, put in the queue
    while True:
        receive_bytes = connection.recv(cfg["buffer_size"])
        q.put(receive_bytes)
        if not receive_bytes:
            stop.append(1)
            break
    # Unlock file lock
    data_dump_threading.join()
    # handle decompress
    if filename.endswith(".temp"):
        asysio.decompress(filename)

    transfering_set.discard(header["filename"])
    db["transfering"] = list(transfering_set)
    logger(f"{notation} is finish", "due_send")


def due_request(header):
    filename = header["filename"]
    logger(f"rec<REQ>{header}", 'due_request')
    if filename in db["recv_files"]:
        logger(f"rec<REQ>{filename} is received file.", "due_request")
        return
    with open(filename, "r+b") as f:
        start_index = header["start_index"]
        f.seek(start_index)
        data = f.read()
        package = asysio.Package().update(filename, start_index, data)
        asystp.send(package)
        logger(f"rec<REQ>{filename} is update", "due_request")


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
            logger(f"rec<SYN>{header}", 'receiver')

        if header["method"] == "FIN":
            logger(f"rec<FIN>{header}", 'receiver')
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

    if cfg["encryption"] == "True":
        logger("decryptoing", "due_send")
        ori_data = b""
        with open(filename, 'r+b') as f:
            ori_data = f.read()
        with open(filename, "wb") as f:
            data = asysio.decrypt(cfg["key"], ori_data)
            f.write(data)

    logger(f"{filename} finish write in.", "data_dump")
