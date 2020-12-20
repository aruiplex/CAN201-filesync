# THIS CODE IS ONLY USED FOR RUNNING PYTHON CODES REMOTELY
# YOU CANNOT USE PARAMIKO FOR YOUR PROJECT !!!
from os.path import join
from paramiko import SSHClient
from paramiko import AutoAddPolicy
import threading

# Settings
py_files = ['aruixsync.logo', 'aserver.py', 'asys.py', 'asysfs.py', 'asysio.py', 'asystp.py',
            'config.json', 'db.json', 'devTool.py', 'main.py']
remote_python_interpreter = '/usr/local/bin/python3'
remote_current_working_directory = '/home/tc/data/aruixsync/'
remote_IP = ["192.168.122.3", "192.168.122.5", "192.168.122.6"]
remote_username = 'tc'
remote_password = '123'


def run(remote_ip):

    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    try:
        ssh.connect(remote_ip, username=remote_username,
                    password=remote_password, port=22, timeout=5)

        # mount /mnt/sda1 to home folder as "workplace"
        ssh.exec_command(
            f'if [ ! -d "workplace" ]; then\nmkdir -p workplace\necho {remote_password} | sudo mount /mnt/sda1 ~/workplace\nfi')
        # change the ownership of workplace folder
        ssh.exec_command(
            f'echo {remote_password} | sudo chown tc /home/tc/workplace')
        # make the CWD
        ssh.exec_command(f'mkdir -p {remote_current_working_directory}')

        sftp = ssh.open_sftp()
        for f in py_files:
            components = f.split('/')
            if len(components) > 1:  # Files in folders
                target_dir = join(remote_current_working_directory,
                                  '/'.join(components[:-1])).replace('\\', '/')
                ssh.exec_command(f'mkdir -p {target_dir}')
            else:  # Files in CWD
                target_dir = remote_current_working_directory.replace(
                    '\\', '/')
            print(f'Send {components[-1]} to {remote_ip}:{target_dir}')
            sftp.put(f, join(target_dir, components[-1]).replace('\\', '/'))


    except Exception as ex:
        print(ex)
        sftp.close()
        ssh.close()
        return -1

    sftp.close()
    ssh.close()


run_1 = threading.Thread(target=run, args=(remote_IP[0],))
run_2 = threading.Thread(target=run, args=(remote_IP[1],))
run_3 = threading.Thread(target=run, args=(remote_IP[2],))
run_1.start()
run_2.start()
run_3.start()
run_1.join()
run_2.join()
run_3.join()
