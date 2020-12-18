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

"""
sync_files() -> new_files, deleted_files, mod_files:
通过遍历sync文件夹来找到new_files, deleted_files, mod_files, 返回的是str

save_files_list(new_files: set, deleted_files: set, modified_files: set):
通过sync_files()的返回值来持续化到db.json中

check_files():
整个filesystem的入口
"""


def sync_files() -> tuple:
    """
    return new files and deleted files
    """
    # sync directory
    sync_dir = cfg["sync_dir"]
    # receive files
    rev_files = set(db["recv_files"])
    # current exist files
    cur_files = set()
    # past exist files
    ori_files = set(db["sync_files"]).union(rev_files)
    # modified files
    mod_files = set()
    # ignored files
    ign_files = set(db["ignore"])

    for root, dirs, files in os.walk(sync_dir):
        for cur_file in files:
            # add path at the start of filename
            cur_file = os.path.join(root, cur_file)
            cur_files.add(cur_file)

    for cur_file in cur_files:
        file_obj = SyncFile(cur_file)
        # TODO: 没考虑接收方文件修改的方案
        for ori_file in db["sync_files"]:
            if file_obj.name == ori_file["name"]:
                # 在时间不同但是size相同的情况下, 则是被认为文件被修改了
                if file_obj.size == ori_file["size"] and file_obj.time != ori_file["time"]:
                    mod_files.add(file_obj.name)

    new_files = cur_files - ori_files - ign_files - rev_files
    deleted_files = ori_files - cur_files
    return new_files, deleted_files, mod_files


def persist_db_file():
    """persist the list of file names to db
    """
    with open(cfg["db_file"], "w") as outfile:
        json.dump(db, outfile)


def update_db_file(new_files: set, deleted_files: set, mod_files: set):
    """update db dict in memory
    """
    global cfg, db
    if not new_files and not deleted_files and not mod_files:
        return
    # original local files dict
    sync_files = set(db["sync_files"])
    # origin receive files dict
    rev_files = set(db["recv_files"])
    # need to add into sync_files. this is local file.
    new_sync_files = set()

    # if there has deleted files or modified files
    # TODO: 这里可能会有接收文件方文件修改, 处理方案?
    # 把修改过的文件的记录先删掉, 再赋予他一个新的记录
    if deleted_files or mod_files:
        deleted_files.update(mod_files)
        # minus deleted files in dict
        sync_files = {x for x in sync_files if x["name"] not in deleted_files}
        rev_files = {x for x in rev_files if x not in deleted_files}

    # current files to dict
    if new_files or mod_files:
        new_files.update(mod_files)
        for new_file in new_files:
            new_sync_files.add(SyncFile(new_file).__dict__)

    # original files dict + current files to dict - deleted files in dict
    sync_files = sync_files.union(new_sync_files)
    db.update(sync_files=list(sync_files))
    db.update(rev_files=list(rev_files))
    # logger(sync_files, "sync_files")


def file_sys():
    """This function arrange all file system 
    """
    sync_interval = cfg["sync_interval"]
    n = 0
    total = cfg["db_update_persist_ratio"]
    while True:
        time.sleep(sync_interval)
        new_files, deleted_files, mod_files = sync_files()
        update_db_file(new_files, deleted_files, mod_files)

        if deleted_files:
            package = asysio.Package().delete(deleted_files)
            asystp.send(package)
            logger(f"<DEL>{deleted_files}", "file_sys")

        if new_files:
            for new_file in new_files:
                logger(new_files, "new_files")
                with open(new_file, "rb") as f:
                    data = f.read()
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

        # logger("update db", "file_sys")
        n += 1
        if n >= total:
            # logger("persist db", "file_sys")
            persist_db_file()
            n = 0


class SyncFile():
    """
    a file entity class to record file and provide operations.
    a format to presist files entity 
    """
    name = ""
    time = 0
    size = 0

    def __init__(self, name):
        self.name = name
        self.time = self.__get_time()
        self.size = self.__get_size()

    def __get_time(self) -> int:
        """get file modify time by file name 
        """
        return os.path.getmtime(self.name)

    def __get_size(self) -> int:
        """get file size by file name
        """
        return os.path.getsize(self.name)

    def __eq__(self, other):
        return self.name == other.name and self.time == other.time and self.size == other.size
