import signal
import json
import sys
import argparse
import threading
import os
import time
import uuid
from collections import defaultdict
import hashlib

"""
aruix sync system function

get_files() -> list
1. list all files should be synced

logger(message: str, unit=""): None
1. a simple logger to show the message and system part.

load_db() -> dict:
1. load database to system

save_files(files: list):
1. save all filename to database

pass_argument():
1. get cli arguments to config system

load_config() -> dict:
1. load config.json to system 

init():
1. prepare the config file to start system 

Global variables:

cfg:    asys(aruix sync transfer protocol system) global config
db:     persist info to database
"""


def get_file_md5(f, chunk_size=8192):
    h = hashlib.md5()
    while True:
        chunk = f.read(chunk_size)
        if not chunk:
            break
        h.update(chunk)
    return h.hexdigest()


def logger(message: str, unit=""):
    print(f"[{threading.current_thread().name}]\t[{unit}]\t{message}".expandtabs(
        30), end='\n')


def load_config() -> dict:
    """load config file to this sys
    """
    with open("config.json") as cfg_file:
        cfg = json.load(cfg_file)
    return cfg


# global configuration
cfg = load_config()


def load_db() -> dict:
    """load database to sys
    """
    with open("db.json") as db_file:
        db = json.load(db_file)
        # get a uuid for this device
        if db["device_id"] == "":
            db.update(device_id=str(uuid.uuid4()))
    return db


# global database
db = load_db()


def pass_argument():
    """pass cli arguments to cfg
    1. ips,         default: config file
    2. encryption,  default: false
    """
    global cfg
    parser = argparse.ArgumentParser(
        description='aruisync (aruix sync transfor protocol)')
    parser.add_argument(
        '--encryption', '-e', help='encryption for transfer, \'--encryption yes\' for enable', default=False)
    parser.add_argument(
        '--ip', '-i', help='connection to IP addresses')
    args = parser.parse_args()
    if args.encryption == 'yes':
        cfg["encryption"] = True
    if args.ip == None:
        logger("There are no ip input, use ip in config", "pass_arg")
    else:
        cfg["ips"] =  [int(n) for n in args.ip.split(",")]


def load_logo() -> str:
    logo_file = cfg["logo_file"]
    with open(logo_file, "r") as f:
        content = f.read()
    return content


def init():
    """
    判读是否有share文件夹.
    """
    if not os.path.isfile("config.json"):
        with open("config.json", "w") as f:
            cfg_new = {
                "server": {
                    "host": "127.0.0.1",
                    "port": 20001
                },
                "db_file": "db.json",
                "sync_interval": 2,
                "buffer_size": 8,
                "compress_level": 6,
                "encryption": False,
                "ips": [],
                "sync_dir": "./share"
            }
            f.write(cfg_new)

    db_file = cfg["db_file"]

    if not os.path.isfile(db_file):
        with open("db.json", "w") as f:
            cfg_new = {
                "sys_files": [
                    "./asysfs.py",
                    "./asysio.py",
                    "./asystp.py",
                    "./asys.py",
                    "./config.json",
                    "./db.json",
                    "./devTool.py",
                    "./main.py",
                    "./__pycache__"
                ],
                "ignore": [],
                "sync_files": []
            }
            f.write(cfg_new)


stop_times = 0


def receive_signal(signalNumber, frame):
    import asysfs
    global stop_times
    logger("Receive stop signal", "catch_signal")

    # 在退出前保存 db.json
    # new_files, deleted_files, mod_files = asysfs.sync_files()
    # asysfs.update_db_file(new_files, deleted_files, mod_files)
    asysfs.persist_db_file()
    logger("Saved to db", "catch_signal")

    stop_times += 1
    if stop_times >= 2:
        logger("Bye  ヽ(*。>Д<)o゜", "Aruix Sync")
        sys.exit(0)


# if __name__ == "__main__":
#     pass_argument()
