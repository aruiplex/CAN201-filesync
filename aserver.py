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

syn = []


def listener() -> socket:
    n = 1
    host = cfg["server"]["host"]
    port = cfg["server"]["port"]
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, port))
        s.listen()
        logger(f"<{n}> Listening on ATP://{host}:{port}", "listener")
        while len(syn) == 0:
            connection, addr = s.accept()
            logger(f"<{n}> Connected by {addr}", "listener")
            # create new thread to re
            threading.Thread(target=receiver, args=(
                connection,), name=f"ReceiverThread-{n}").start()
            n += 1
        logger("break", "listener")


def receiver(connection: socket):
    global syn
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
        method = header["method"]
        q.put(store[8 + header_length:])

        if header["method"] == b"FIN":
            logger(f"<FIN>{header}", 'Header')
            syn.append("FINISH")

        if header["method"] == b"SED":
            logger(f"{header}", '<SED>')
            stop = []
            # 把正在传的文件记录一下, 文件锁
            db["transfering"] = header["filename"]
            # converge list to set, aviod to repeat
            s = set(db["recv_files"])
            s.add(header["filename"])
            db.update(transfering=list[s])
            data_dump_threading = threading.Thread(
                target=data_dump, args=(header, q, stop), name=f"data_dump for {threading.current_thread().name}")
            data_dump_threading.start()
            while True:
                receive_bytes = connection.recv(buffer_size)
                if not receive_bytes:
                    stop.append(1)
                    break
                q.put(receive_bytes)
            # 解开文件锁
            db.update(transfering="")

        if header["method"] == b"UPT":
            logger(f"{header}", '<UPT>')
            start_index = header["start_index"]
            stop = []
            # 把正在传的文件记录一下, 文件锁
            db["transfering"] = header["filename"]
            # converge list to set, aviod to repeat
            s = set(db["recv_files"])
            s.add(header["filename"])
            db.update(transfering=list[s])
            data_dump_threading = threading.Thread(
                target=data_dump, args=(header, q, stop, start_index), name=f"data_dump for {threading.current_thread().name}")
            data_dump_threading.start()
            while True:
                receive_bytes = connection.recv(buffer_size)
                if not receive_bytes:
                    stop.append(1)
                    break
                q.put(receive_bytes)
            # 解开文件锁
            db.update(transfering="")
            logger(f"{header['filename']} Finish", "UPT transfer")

        if method == b"REQ":
            filename = header["filename"]
            logger(f"{header}", '<REQ>')
            if filename not in db["sync_files"]:
                logger(f"{filename} is received file.", "<REQ>")
                return
            with open(filename, "r+b") as f:
                start_index = header["start_index"]
                f.seek(start_index)
                data = f.read()
                package = asysio.Package().update(filename, start_index, data)
                asystp.send(package)
                logger(f"{filename} is update", "<REQ>")

        if header["method"] == b"DEL":
            logger(f"<DEL>: {header}", 'Header')
            while True:
                receive_bytes = connection.recv(buffer_size)
                if not receive_bytes:
                    break
                q.put(receive_bytes)
            del_file_set = eval(q.get())
            logger(f"{del_file_set}", "delete")
            for del_file in del_file_set:
                try:
                    os.remove(del_file)
                except FileNotFoundError:
                    logger(f"{del_file} is not found", "aserver")

        if header["method"] == b"SYN":
            logger(f"<SYN>: {header}", 'Header')


def data_dump(header, q: queue.Queue, stop, start_index=0):
    """dump data into file from Queue
    header: transfer header;
    q: data store.
    stop: stop signal.
    start_index: for Discontinued transmission, write into file from a contain point 
    """
    filename = header["filename"]
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "r+b") as f:
        f.seek(start_index)
        while len(stop) == 0 or not q.empty():
            try:
                content = q.get(block=False, timeout=1)
                f.write(content)
            except queue.Empty:
                continue
            except Exception:
                logger(f"Some error appearance: {Exception}.", "data_dump")
    logger(f"{filename} Finish", "data_dump")
