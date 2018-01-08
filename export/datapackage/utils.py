import json
import os

current_directory = os.path.dirname(__file__)
schemas_directory = os.path.realpath(os.path.join(current_directory, './schemas'))


def get_table_schema(filename):
    schema_filepath = os.path.normpath(os.path.join(schemas_directory, filename))
    with open(schema_filepath) as f:
        schema = json.load(f)

    return schema
