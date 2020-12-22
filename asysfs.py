from asys import logger, cfg, db
import asysio
import os
import time
import asystp
import gzip

"""
sync_files() -> new_files, deleted_files, mod_files:
Find new_files, deleted_files, mod_files by traversing the sync folder, the returned is str

save_files_list(new_files: set, deleted_files: set, modified_files: set):
Continue to db.json through the return value of sync_files()

check_files():
Entrance of the entire filesystem
"""


def sync_files() -> tuple:
    """return new files and deleted files
    """
    # Files to be synchronized, list of SyncFile objects
    sync_objs = db["sync_files"]
    # receive files
    recv_files = set(db["recv_files"])
    # current exist files
    cur_files = set()
    # past exist files
    ori_files = set()
    # modified files
    mod_files = set()
    # ignored files
    ign_files = set(db["ignore"])
    # local file name
    sync_files = set()
    # Put the name of the object in the form of str
    for i in sync_objs:
        sync_files.add(i["name"])
    # All original files = all files received + all local files
    ori_files.update(recv_files)
    ori_files.update(sync_files)

    # Get all existing files and add them to cur_files
    for root, dirs, files in os.walk(cfg["sync_dir"], followlinks=True):
        for cur_file in files:
            # add path at the start of filename
            cur_file = os.path.join(root, cur_file)
            cur_files.add(cur_file)

    # Get the file name of the modified file
    for sync_obj in sync_objs:
        for cur_file in cur_files:
            try:
                cur_obj = SyncFile(cur_file)
                if sync_obj["name"] == cur_obj.name:
                    if sync_obj["time"] != cur_obj.time or sync_obj["size"] != cur_obj.size:
                        mod_files.add(sync_obj["name"])
            except FileNotFoundError:
                logger(f"this file {cur_obj.name} not exist", "SyncFile")

    new_files = cur_files - ori_files - ign_files - mod_files
    __update_db_file(new_files, mod_files)
    return new_files, mod_files


def __update_db_file(new_files: set, mod_files: set):
    """update db dict in memory
    1. Remove deleted and updated files from the list
    2. Add the updated files
    """
    global cfg, db
    if not new_files and not mod_files:
        return
    # original local files dict
    sync_files = db["sync_files"]
    # origin receive files dict
    recv_files = set(db["recv_files"])
    # need to add into sync_files. this is local file.
    new_sync_files = []

    # if there has deleted files or modified files
    # Delete the record of the modified file first, and then give him a new record
    if mod_files:
        # minus deleted files in dict
        sync_files = [x for x in sync_files if x["name"] not in mod_files]
        recv_files = [x for x in recv_files if x not in mod_files]
        for mod_file in mod_files:
            new_sync_files.append(SyncFile(mod_file).__dict__)

    # current files to dict
    if new_files:
        for new_file in new_files:
            new_sync_files.append(SyncFile(new_file).__dict__)

    # original files dict + current files to dict - deleted files in dict
    sync_files.extend(new_sync_files)
    db["sync_files"] = list(sync_files)
    db["recv_files"] = list(recv_files)


def file_sys():
    """This function arrange all file system 
    """
    sync_interval = cfg["sync_interval"]
    n = 0
    total = cfg["db_update_persist_ratio"]
    while True:
        time.sleep(sync_interval)
        n += 1
        if n >= total:
            db.presist_db()
            n = 0

        new_files, mod_files = sync_files()

        if new_files:
            logger(new_files, "new_files")
            for new_file in new_files:
                sync_file = SyncFile(new_file)
                # File larger than 250M
                if sync_file.size >= 250*1024*1024:
                    new_file = asysio.compress(new_file)

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
            logger(mod_files, "mod_files")
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
