__author__ = 'Patrick Phaneuf'


class AleName:

    Ale = 0

    Flask = 1

    Isolate = 2


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
