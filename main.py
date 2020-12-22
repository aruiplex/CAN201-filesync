import aserver
from asys import *
import asysfs
import asystp
import signal

"""
This is the py file to start aruix sync
"""

print(logo)

init()

print("|Time| [ThreadName]\t[FunctionName]\t[Operation]".expandtabs(30))

# pass arguments
pass_argument()

# start listening on port
listener_threading = threading.Thread(
    target=aserver.listener, name="listener")
listener_threading.start()

file_sys_threading = threading.Thread(
    target=asysfs.file_sys, name="file_scanner")
file_sys_threading.start()
logger("file system start", "file_sys")

signal.signal(signal.SIGINT, receive_signal)
logger("Listening signal", "catch_signal")

# Breakpoint Resume Protection Mechanism
asystp.retransfer()
logger("checked", "retransfer")

logger("System has been initialized", "asys")

listener_threading.join()
file_sys_threading.join()
logger("Bye", "Aruix Sync")
