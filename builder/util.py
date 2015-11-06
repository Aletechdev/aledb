from enum import Enum


__author__ = 'Patrick Phaneuf'

SAMPLE_TYPE = Enum('SAMPLE_TYPE', 'clonal population')

BRESEQ_ANALYSIS_POPULATION_FLAG = " -p "

BRESEQ_LOG_FILE = "log.txt"


class AleName:
    Ale = 0
    Flask = 1


def sanitize_path(path):

    if path[-1] != '/':
        path += '/'

    return path


def parse_ale_name(ale_isolate_name, ale_name_paramter):

    split = ale_isolate_name.split("-")

    ale_parameter = int(split[ale_name_paramter])

    return ale_parameter


def get_ale_name(ale_number, flask_number):

    ale_name = str(ale_number) + "-" + str(flask_number)

    return ale_name


def is_sample_clonal_or_popuation(breseq_log_file_path):

    sample_type = SAMPLE_TYPE.clonal

    if BRESEQ_ANALYSIS_POPULATION_FLAG in open(breseq_log_file_path).read():

        return SAMPLE_TYPE.population

    return sample_type
