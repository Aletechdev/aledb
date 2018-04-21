#!/bin/bash

source ./config.sh
python3 manage.py makemigrations
python3 manage.py migrate 
