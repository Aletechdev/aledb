#!/bin/sh

python manage.py migrate
python manage.py createcachetable
python manage.py collectstatic --no-input

gunicorn aleinfo.wsgi -b 0.0.0.0:80
