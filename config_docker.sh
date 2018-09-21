#!/bin/bash

export DEBUG=1
export PUBLIC=0
export DJANGO_SETTINGS_MODULE=aleinfo.settings_private

export SEQUENCING_URL=https://console.cloud.google.com/storage/browser/aledb-data/ale_analytics_data/
export MYSQL_DATABASE=ale-db
export MYSQL_USER=ale
export MYSQL_PASSWORD=ale
export MYSQL_HOST=db
export MYSQL_PORT=3306
export ALE_DATA_ROOT_DIR=/var/www/ale_analytics_data/
export GOOGLE_ANALYTICS_TAG=UA-111512162-1
