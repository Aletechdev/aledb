__author__ = 'Patrick Phaneuf'


class AleName:
    Ale = 0
    Flask = 1


def sanitize_path(path):

    if path[-1] != '/':
        path += '/'

    return path


def parse_ale_name(ale_isloate_name, ale_name_paramter):

    split = ale_isloate_name.split("-")

    ale_parameter = int(split[ale_name_paramter])

    return ale_parameter


def get_ale_name(ale_number, flask_number):

    ale_name = str(ale_number) + "-" + str(flask_number)

    return ale_name
