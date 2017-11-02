#!/usr/bin/env bash
set -e
BASEDIR=$(dirname "${BASH_SOURCE}")/..
python3 "${BASEDIR}/manage.py" runserver localhost:8000 --settings=aleinfo.settings.local
