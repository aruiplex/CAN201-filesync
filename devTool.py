import os
import json
import time
import socket


def sender(host, port, buffer_size, file_name):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))
        s.send()


def create_test_file(file_name: str, content: str, times=1000):
    content = content*times
    with open(file_name, "a") as file:
        file.write(content)


def get_files():
    """save all files in the directory
    """
    for file in os.listdir("./"):
        endings = ()
        if not file.endswith(endings):
            json_str = json.dumps(os.path.join(file))
            print(json_str)
            # aslogger(os.path.join(file), "get_files")


def time_consume(function, args):
    start_time = time.time()
    function(args)
    print("----- %s seconds -----" % (time.time() - start_time))


if __name__ == "__main__":
    create_test_file("./hello_world", "hello world!\n")
    # create_test_file("./good_morning", "good morning\n")
