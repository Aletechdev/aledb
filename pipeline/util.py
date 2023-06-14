import subprocess


def get_shared_directories():
    ls_json_cmd = ['ssh', '-i', '/root/.ssh/aledb', 'muyao@aledb.org', 'rclone', 'lsjson', '--dirs-only',
              '--drive-shared-with-me', 'ALE:']
    return subprocess.run(ls_json_cmd)


def get_files_from_directory(dir):
    ls_json_cmd = ['ssh', '-i', '/root/.ssh/aledb', 'muyao@aledb.org', 'rclone', 'lsjson', '--dirs-only',
                   '--drive-shared-with-me', 'ALE:']
