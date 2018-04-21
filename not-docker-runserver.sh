#!/bin/bash

source ./config.sh
if [ "$DEBUG" = 0 ]
then
  gunicorn aleinfo.wsgi -b 0.0.0.0:8000 --reload
else
  echo "!!!DEBUG!!! DEPLOYMENT"
  python3 manage.py runserver
fi
