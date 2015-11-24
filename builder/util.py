from gdparse.gdparse import gdparse


__author__ = 'Patrick Phaneuf'

# BRESEQ_ANALYSIS_POPULATION_FLAG = " -p "

# BRESEQ_LOG_FILE = "log.txt"

# BRESEQ_VERSION_LINE_TAG = "#=AUTHOR"
#
# BRESEQ_VERSION_TAG = "breseq "
#
# BRESEQ_VERSION_STOP_CHAR = " "


class AleName:

    Ale = 0

    Flask = 1


def sanitize_path(path):

    if path[-1] != '/':

        path += '/'

    return path


def parse_ale_name(ale_isolate_name, ale_name_parameter):

    split = ale_isolate_name.split("-")

    ale_parameter = int(split[ale_name_parameter])

    return ale_parameter


def get_ale_name(ale_number, flask_number):

    ale_name = str(ale_number) + "-" + str(flask_number)

    return ale_name


# def is_sample_clonal_or_population(breseq_log_file_path):
#
#     sample_type = gdparse.SampleType.CLONAL
#
#     if BRESEQ_ANALYSIS_POPULATION_FLAG in open(breseq_log_file_path).read():
#
#         return SAMPLE_TYPE.population
#
#     return sample_type

# def get_breseq_version(genomic_diff_file_path):
#
#     breseq_version = ""
#
#     with open(genomic_diff_file_path, 'r') as genomic_diff_file:
#
#         for line in genomic_diff_file:
#
#             if BRESEQ_VERSION_LINE_TAG in line:
#
#                 version_string_index = line.find(BRESEQ_VERSION_TAG) + len(BRESEQ_VERSION_TAG)
#
#                 while line[version_string_index] != BRESEQ_VERSION_STOP_CHAR:
#
#                     breseq_version += line[version_string_index]
#                     line[version_string_index] += 1
#
#                 break
#
#     return breseq_version
