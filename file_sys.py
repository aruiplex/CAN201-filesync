import os
import asys


def file_scanner() -> tuple:
    # return
    new_files = set()
    del_files = set()
    mod_files = set()

    # 本次查看中, 文件夹的所有文件名
    cur_files = set()
    # 原来记录的所有文件名
    ori_files = set()
    # 收到的所有文件名
    recv_files = asys.db["recv_files"]
    # 原来的所有文件对象
    sync_objs = asys.db["sync_files"]

    ori_files.update(recv_files)

    for sync_obj in sync_objs:
        ori_files.add(sync_obj["name"])

    # 得到现有的所有文件, 添加到 cur_files 中
    for root, dirs, files in os.walk('./share/'):
        for cur_file in files:
            # add path at the start of filename
            cur_file = os.path.join(root, cur_file)
            cur_files.add(cur_file)


def test1():
    from asysfs import SyncFile
    sync_file = SyncFile("SoftwareTesting.pptx")
    return sync_file.__dict__


if __name__ == "__main__":
  
    # file_scanner()
