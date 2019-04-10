
__author__ = 'Patrick Phaneuf'


class AleName:
    Ale = 0
    Flask = 1
    Isolate = 2
    TechnicalReplicate = 3


def sanitize_path(path):
    if path[-1] != '/':
        path += '/'
    return path


def parse_ale_name(ale_isolate_name, ale_name_parameter):
    split = ale_isolate_name.split("-")
    try:
        ale_parameter = int(split[ale_name_parameter])
    except:
        ale_parameter = 1
    return ale_parameter


def get_ale_isolate_name_from_path(breseq_report_path):
    ale_isolate_name_start_index = breseq_report_path.rfind('/')
    if ale_isolate_name_start_index >= len(breseq_report_path) - 1:
        ale_isolate_name_start_index = breseq_report_path[:-2].rfind('/')
    ale_isolate_name = breseq_report_path[ale_isolate_name_start_index:]
    ale_isolate_name = ale_isolate_name.strip('/')
    return ale_isolate_name
