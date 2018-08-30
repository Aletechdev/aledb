#!/bin/bash

source ./config.sh
if [ "$DEBUG" = 0 ]
then
  python3 manage.py migrate
  python3 manage.py collectstatic --no-input
  gunicorn aleinfo.wsgi -b 0.0.0.0:8000 --reload
else
  echo "!!!DEBUG!!! DEPLOYMENT"
  python3 manage.py migrate
  python3 manage.py collectstatic --no-input
  python3 manage.py runserver
fi
