import json
import subprocess


def get_shared_directories():
    lsjson_cmd = ['ssh', '-i', '/root/.ssh/aledb', 'muyao@aledb.org', 'rclone', 'lsjson', '--dirs-only',
              '--drive-shared-with-me', 'ALE:']
    lsjson_out = json.loads(subprocess.check_output(lsjson_cmd).decode("utf-8"))
    return lsjson_out


def get_files_from_directory(dir):
    ls_json_cmd = ['ssh', '-i', '/root/.ssh/aledb', 'muyao@aledb.org', 'rclone', 'lsjson', '--dirs-only',
                   '--drive-shared-with-me', 'ALE:']
