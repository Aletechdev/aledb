import subprocess

LSJSON = ['ssh', '-i', '/root/.ssh/aledb', 'muyao@aledb.org', 'rclone', 'lsjson', '--dirs-only', '--drive-shared-with-me', 'ALE:']


def get_shared_directories():
    return subprocess.run(LSJSON)


get_shared_directories()


