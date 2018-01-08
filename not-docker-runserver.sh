#!/bin/sh

export DEBUG=1
export SEQUENCING_URL=http://sbrg.ucsd.edu
export MYSQL_DATABASE=database
export MYSQL_USER=user
export MYSQL_PASSWORD=password
export MYSQL_HOST=db
export MYSQL_PORT=3306
export DJANGO_SETTINGS_MODULE=aleinfo.settings_private
export GOOGLE_ANALYTICS_TAG=UA-111512162-1

if [ "$DEBUG" = 0 ]
then
  gunicorn aleinfo.wsgi -b 0.0.0.0:8000 --reload
else
  echo "!!!DEBUG!!! DEPLOYMENT"
  python3 manage.py runserver localhost:8000
fi
