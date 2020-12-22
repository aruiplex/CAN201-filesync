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
import signal
import json
import sys
from datetime import datetime
import argparse
import threading
import os
import time
import uuid
from collections import defaultdict
import hashlib


def get_file_md5(f, chunk_size=8192):
    h = hashlib.md5()
    while True:
        chunk = f.read(chunk_size)
        if not chunk:
            break
        h.update(chunk)
    return h.hexdigest()


def logger(message: str, unit=""):
    current_time = datetime.now().strftime("%H:%M:%S")
    print(f"|{current_time}| [{threading.current_thread().name}]\t[{unit}]\t{message}".expandtabs(
        30), end='\n')


def load_config() -> dict:
    """load config file to this sys
    """
    with open("config.json") as cfg_file:
        cfg = json.load(cfg_file)
    return cfg


# global configuration
cfg = load_config()


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
        logger("open encryption", "encryption")
        cfg["encryption"] = "True"
    else:
        cfg["encryption"] = "False"
    if args.ip == None:
        logger("There are no ip input, use ip in config", "pass_arg")
    else:
        cfg["ips"] = args.ip.split(",")


def load_logo() -> str:
    logo_file = cfg["logo_file"]
    with open(logo_file, "r") as f:
        content = f.read()
    return content


def init():
    """Determine whether there is a share folder.
    """
    if not os.path.isdir("./share"):
        os.mkdir("./share")

    if not os.path.isfile("config.json"):
        with open("config.json", "w") as f:
            cfg_new = {
                "server": {
                    "host": "127.0.0.1",
                    "port": 20000
                },
                "db_file": "db.json",
                "logo_file": "aruixsync.logo",
                "sync_interval": 0.5,
                "buffer_size": 10240,
                "compress_level": 6,
                "encryption": "False",
                "ips": [],
                "port": 20000,
                "file_block_size": 1024,
                "sync_dir": "./share",
                "key": "This is key",
                "db_update_persist_ratio": 3
            }

            f.write(cfg_new)

    db_file = cfg["db_file"]

    if not os.path.isfile(db_file):
        with open(db_file, "w") as f:
            cfg_new = {"ignore": [], "sync_files": [],
                       "transfering": [], "recv_files": []}
            f.write(cfg_new)


stop_times = 0


class Database:
    mutex = threading.Lock()

    def __init__(self):
        """load database to sys
        """
        with open(cfg["db_file"], "r") as db_file:
            self.db = json.load(db_file)

    def presist_db(self):
        """persist the list of file names to db
        """
        with open(cfg["db_file"], "w") as f:
            logger("database dump", "Database")
            json.dump(self.db, f)

    def __getitem__(self, index):
        return self.db[index]

    def __setitem__(self, key, value):
        if type(value) == set:
            value = list(value)
        self.mutex.acquire()
        self.db[key] = value
        self.mutex.release()


db = Database()


def receive_signal(signal_number, frame):
    import asysfs
    global stop_times

    # Save db.json before exiting
    db.presist_db()
    logger(
        f"Saved to db", "receive_signal")

    stop_times += 1
    if stop_times >= 2:
        logger("Bye", "Aruix Sync")
        sys.exit(0)
