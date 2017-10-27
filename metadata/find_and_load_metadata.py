import os
import os.path
import sys
from metadata.parser import parse_metadata_post_experiment_upload


METADATA_DIR_NAME = "metadata"
PRIMARY_KEY_FILE_NAME = "primary_key"


def _get_metadata_dir_path(current_path, dir_name_list):
    metadata_dir_path = ""
    if METADATA_DIR_NAME in dir_name_list:
        metadata_dir_path = current_path + '/' + METADATA_DIR_NAME
    return metadata_dir_path


def _get_metadata_dir_path_list(start_abs_path):
    metadata_dir_path_list = []
    if os.path.isdir(start_abs_path):
        for dir_tup in os.walk(start_abs_path):
            dir_list = dir_tup[1]
            metadata_dir_path = _get_metadata_dir_path(dir_tup[0], dir_tup[1])
            if metadata_dir_path != "":
                metadata_dir_path_list.append(metadata_dir_path)
    return(metadata_dir_path_list)


def _get_exp_primary_key(metadata_dir_path):
    exp_primary_key = ""
    file_name_list = [f for f in os.listdir(metadata_dir_path) if os.path.isfile(os.path.join(metadata_dir_path, f))]
    if PRIMARY_KEY_FILE_NAME in file_name_list:
        primary_key_file_path = metadata_dir_path + '/' + PRIMARY_KEY_FILE_NAME
        with open(primary_key_file_path, 'r') as f:
            exp_primary_key = f.readline().strip('\n')
    return exp_primary_key


def _output_metadata_dir_path_to_file(metadata_dir_path_list):
    with open("metadata_dir_paths.txt", 'w') as f:
        for metadata_dir_path in metadata_dir_path_list:
            f.write(metadata_dir_path + '\n')


def _load_metadata(metadata_dir_path_list):
    for metadata_dir_path in metadata_dir_path_list:
        print(metadata_dir_path)
        exp_primary_key = _get_exp_primary_key(metadata_dir_path)
        if exp_primary_key != "":
            parse_metadata_post_experiment_upload(metadata_dir_path, exp_primary_key)


def load_metadata(metadata_dir_path_file):
    metadata_dir_path_list = [line.rstrip('\n') for line in open(metadata_dir_path_file, 'r')]
    if len(metadata_dir_path_list) != 0:
        _load_metadata(metadata_dir_path_list)


def find_and_load_metadata(search_root_path):
    metadata_dir_path_list = _get_metadata_dir_path_list(search_root_path)
    _output_metadata_dir_path_to_file(metadata_dir_path_list)
    _load_metadata(metadata_dir_path_list)
