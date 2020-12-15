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
# import asystp

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
    # current exist files
    cur_files = set()
    # past exist files
    ori_files = set()
    # modified files
    mod_files = set()
    # ignored files
    ign_files = set(db["ignore"])

    for sync_recording in db["sync_files"]:
        ori_files.add(sync_recording["name"])

    for root, dirs, files in os.walk(sync_dir):
        for cur_file in files:
            # add path at the start of filename
            cur_file = os.path.join(root, cur_file)
            cur_files.add(cur_file)

    for cur_file in cur_files:
        file_obj = SyncFile(cur_file)
        for ori_file in db["sync_files"]:
            if file_obj.name == ori_file["name"]:
                if file_obj.size != ori_file["size"] or file_obj.time != ori_file["time"]:
                    mod_files.add(file_obj.name)

    new_files = cur_files - ori_files - ign_files
    deleted_files = ori_files - cur_files
    return new_files, deleted_files, mod_files


def save_files_list(new_files: set, deleted_files: set, mod_files: set):
    """persist the list of file names to db
    """
    if not new_files and not deleted_files and not mod_files:
        return
    # original files dict
    sync_files = db["sync_files"]
    new_sync_files = []
    # if mod_files:
    #     sync_files = [x for x in sync_files if x["name"] not in mod_files]

    # if there has deleted files
    if deleted_files or mod_files:
        # minus deleted files in dict
        deleted_files.update(mod_files)
        sync_files = [x for x in sync_files if x["name"] not in deleted_files]

    # current files to dict
    if new_files or mod_files:
        new_files.update(mod_files)
        for new_file in new_files:
            new_sync_files.append(SyncFile(new_file).__dict__)

    # original files dict + current files to dict - deleted files in dict
    sync_files = sync_files + new_sync_files
    db.update(sync_files=sync_files)
    with open(cfg["db_file"], "w") as outfile:
        json.dump(db, outfile)


def check_files():
    sync_interval = cfg["sync_interval"]
    while True:
        time.sleep(sync_interval)
        new_files, deleted_files, mod_files = sync_files()
        save_files_list(new_files, deleted_files, mod_files)
        if deleted_files:
            package = asysio.Package().delete(deleted_files)
            asystp.send(package)
        if new_files:
            for new_file in new_files:
                package = asysio.Package().send(new_file)
                asystp.send(package)
        


def asysfs_main():
    threading.Thread()


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


if __name__ == "__main__":
    new_files, deleted_files, mod_files = sync_files()
    save_files_list(new_files, deleted_files, mod_files)
    print("mod: ",  mod_files)
