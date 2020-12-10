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
# import asystp


def sync_files() -> tuple:
    """
    1. return new files and deleted files
    """
    # sync directory
    sync_dir = cfg["sync_dir"]
    cur_files = set()
    ori_files = set()
    ign_files = set(db["ignore"])

    for sync_recording in db["sync_files"]:
        ori_files.add(sync_recording["name"])

    for root, dirs, files in os.walk(sync_dir):
        for cur_file in files:
            # add path at the start of filename
            cur_file = os.path.join(root, cur_file)
            cur_files.add(cur_file)
    new_files = cur_files - ori_files - ign_files
    deleted_files = ori_files - cur_files
    return new_files, deleted_files

    # # sync directory
    # sync_dir = cfg["sync_dir"]
    # # current file list
    # curr_sync_list = []
    # # new file appended
    # sync_files_append = []
    # # old file list
    # ex_files_list = []
    # # old file list + system files
    # ex_all_files_list = []
    # # add all system file
    # ex_all_files_list.extend((db["sys_files"]))
    # # add all db.json old file to list
    # for sync_recording in db["sync_files"]:
    #     ex_files_list.append(sync_recording["name"])

    # ex_all_files_list.extend(ex_files_list)
    # # regex Matching
    # # ex_files_tuple = tuple(ex_all_files_list)

    # for root, dirs, files in os.walk(sync_dir):
    #     for file in files:
    #         # add path at the start of filename
    #         file = os.path.join(root, file)
    #         curr_sync_list.append(file)
    #         # if there don't have this file
    #         # if not file.startswith(ex_files_tuple):
    #         #     sync_files_append.append(file)
    # new_files = list(set(curr_sync_list) - set(ex_files_list))
    # deleted_files = list(set(ex_files_list) - set(curr_sync_list))
    # print("curr_sync_list: ", curr_sync_list)
    # print("deleted_files: ", deleted_files)
    # print("new_files: ", new_files)
    # # return sync_files_append
    # return new_files


def save_files_list(new_files: set, deleted_files: set):
    """persist the list of file names to db
    """
    if not new_files and not deleted_files:
        return
    # original files dict
    sync_files = db["sync_files"]
    new_sync_files = []

    # current files to dict
    for file in new_files:
        new_sync_files.append(SyncFile(file).__dict__)

    if deleted_files:
        # minus deleted files in dict
        sync_files = [x for x in sync_files if x["name"] not in deleted_files]

    # original files dict + current files to dict - deleted files in dict
    sync_files = sync_files + new_sync_files
    db.update(sync_files=sync_files)
    with open(cfg["db_file"], "w") as outfile:
        json.dump(db, outfile)


def check_files():
    sync_interval = cfg["sync_interval"]
    while True:
        time.sleep(sync_interval)
        new_files, deleted_files = sync_files()
        save_files_list(new_files, deleted_files)
        if not deleted_files:
            # to send delete message to every VM
            # TODO: asystp.delete(deleted_files)
            pass


def asysfs_main():
    threading.Thread()


"""
a file entity class to record file and provide operations.

"""


class SyncFile():
    """this is a format to presist files entity 
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


if __name__ == "__main__":
    a, b = sync_files()
    save_files_list(a, b)
