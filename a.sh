#!/bin/sh

export DEBUG=1
export SEQUENCING_URL=http://sbrg.ucsd.edu
export MYSQL_DATABASE=ale_db
export MYSQL_USER=root
export MYSQL_PASSWORD=m0t0r0l6
export MYSQL_HOST=localhost
export MYSQL_PORT=3306
export DJANGO_SETTINGS_MODULE=aleinfo.settings_private
export GOOGLE_ANALYTICS_TAG=XXXX
export PUBLIC=1

if [ "$DEBUG" = 0 ]
then
  gunicorn aleinfo.wsgi -b 0.0.0.0:8000 --reload
else
  echo "!!!DEBUG!!! DEPLOYMENT"
  python3 manage.py shell
fi
