import difflib
import socket
import threading
from asys import logger, cfg, db
import struct
import json
import asysio
import math
import os
import time
import asystp
import gzip

"""
sync_files() -> new_files, deleted_files, mod_files:
通过遍历sync文件夹来找到new_files, deleted_files, mod_files, 返回的是str

save_files_list(new_files: set, deleted_files: set, modified_files: set):
通过sync_files()的返回值来持续化到db.json中

check_files():
整个filesystem的入口
"""


def file_scanner() -> tuple:
    """return new files and deleted files
    """
    new_files = set()
    mod_files = set()
    cur_files = set()
    ori_files = db["sync_files"]
    # 得到现有的所有文件, 添加到 cur_files 中
    for root, dirs, files in os.walk(cfg["sync_dir"]):
        for cur_file in files:
            # add path at the start of filename
            cur_file = os.path.join(root, cur_file)
            cur_files.add(cur_file)

    

    


def update_db_file(new_files: set,  mod_files: set):
    """update db dict in memory
    1. 从列表中移除删掉和更新的文件
    2. 添加上更新的文件
    """
    global cfg, db
    if not new_files and not mod_files:
        return
    # original local files dict
    sync_files = db["sync_files"]
    # origin receive files dict
    rev_files = set(db["recv_files"])
    # need to add into sync_files. this is local file.
    new_sync_files = []

    # if there has deleted files or modified files
    # 把修改过的文件的记录先删掉, 再赋予他一个新的记录
    if mod_files:
        # minus deleted files in dict
        sync_files = [x for x in sync_files if x["name"] not in deleted_files]

    # current files to dict
    if new_files or mod_files:
        new_files.update(mod_files)
        for new_file in new_files:
            new_sync_files.append(SyncFile(new_file).__dict__)

    # original files dict + current files to dict - deleted files in dict
    sync_files.extend(new_sync_files)
    db["sync_files"] = list(sync_files)


def file_sys():
    """This function arrange all file system 
    """
    sync_interval = cfg["sync_interval"]
    n = 0
    total = cfg["db_update_persist_ratio"]
    while True:
        time.sleep(sync_interval)
        # logger("update db", "file_sys")
        n += 1
        if n >= total:
            # logger("persist db", "file_sys")
            db.presist_db()
            n = 0

        new_files, mod_files = sync_files()
        update_db_file(new_files, mod_files)

        if new_files:
            logger(new_files, "new_files")
            for new_file in new_files:
                sync_file = SyncFile(new_file)
                # 文件大于 250M
                if sync_file.size >= 250*1024*1024:
                    new_file = asysio.compress(new_file)
                else:
                    logger(new_file, "file_sys")
                    with open(new_file, "rb") as f:
                        data = f.read()
                        if cfg["encryption"] == "True":
                            logger("encryption", "file_sys")
                            data = asysio.encrypt(cfg["key"], data)
                        package = asysio.Package().send(new_file, data)
                        asystp.send(package)
                        logger(f"<SED>{new_file} ", "file_sys")

        if mod_files:
            for mod_file in mod_files:
                with open(mod_file, "rb") as f:
                    content = f.read(300*1024)
                    package = asysio.Package().update(mod_file, 0, content)
                    asystp.send(package)
                    logger(
                        f"<UPT>{mod_files}", "file_sys")


class SyncFile():
    """
    a file entity class to record file and provide operations.
    a format to presist files entity 
    """

    def __init__(self, name, is_sync="False"):
        self.name = name
        self.time = self.__get_time()
        self.size = self.__get_size()
        self.is_sync = is_sync

    def __get_time(self) -> int:
        """get file modify time by file name 
        """
        return os.path.getmtime(self.name)

    def __get_size(self) -> int:
        """get file size by file name
        """
        return os.path.getsize(self.name)

    def build(self, d: dict):
        self.name = d["name"]
        self.time = d["time"]
        self.size = d["size"]
        self.is_sync = d["is_sync"]

    def __eq__(self, other):
        return self.name == other.name and self.time == other.time and self.size == other.size

    def is_modified(self, sync_obj):
        return sync_obj["name"] == self.name and sync_obj["time"] != self.time and sync_obj["size"] == self.size
