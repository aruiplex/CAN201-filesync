import os
import json
import time
import socket

"""
https://docs.python.org/zh-cn/3/library/struct.html
"""


def print_test_data(n: int, interval: str):
    content = ""
    for i in range(n):
        content += str(i)+interval
    with open("./test.data", "w") as f:
        f.write(content)
    print("Test data is ready")


def sender(host, port, buffer_size, file_name):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))
        s.send()


def create_test_file(file_name: str, content: str, times=1000):
    with open(file_name, "a") as file:
        for i in range(times):
            file.write(str(i)+content+"\n")


def get_files():
    """save all files in the directory
    """
    for file in os.listdir("./"):
        endings = ()
        if not file.endswith(endings):
            json_str = json.dumps(os.path.join(file))
            print(json_str)
            # aslogger(os.path.join(file), "get_files")


def time_consume(function):
    start_time = time.time()
    function()
    print("----- %s seconds -----" % (time.time() - start_time))


if __name__ == "__main__":
    print_test_data(1000,"|")
    # create_test_file("./hello_world", "hello world!", times=10000)
    # create_test_file("./good_morning", "good morning\n")
