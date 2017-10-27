#!/bin/sh

python manage.py migrate
python manage.py createcachetable

gunicorn aleinfo.wsgi -b 0.0.0.0:80
