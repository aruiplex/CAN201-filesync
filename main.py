import aserver
import threading
from asys import *
import asysfs
import asysio
import asystp

"""
This is the py file to start aruix sync
"""

print(load_logo())

init()

print("[线程名]\t[函数名]\t[操作]".expandtabs(27))
logger("System has been initialized", "asys")

# pass arguments
pass_argument()
logger(cfg, "pass_arg")

# start listening on port
listener_threading = threading.Thread(
    target=aserver.listener, name="listener")
listener_threading.start()

file_sys_threading = threading.Thread(
    target=asysfs.file_sys, name="file sys scanner")
file_sys_threading.start()
logger("file system start", "file_sys")


signal.signal(signal.SIGINT, receive_signal)
logger("Listening signal", "catch_signal")

# 断点续传保护机制
if db["transfering"] != "":
    sync_file = asysfs.SyncFile(db["transfering"])
    logger(f"starting continue transfer: {sync_file.name}", "Discontinued transmission")
    package = asysio.Package().request(sync_file.name, sync_file.size)
    asystp.send(package)

listener_threading.join()
file_sys_threading.join()
logger("Bye  ヽ(*。>Д<)o゜", "Aruix Sync")
