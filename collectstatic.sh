#!/bin/sh

source ./config.sh
python3 manage.py collectstatic
