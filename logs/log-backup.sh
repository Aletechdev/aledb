#!/bin/bash


mkdir /tmp/aledblogs
cd /tmp/aledblogs

log_path=/var/www/aledb/logs
current_month=$(date +%B)
mkdir $current_month

cp $log_path/debug.log* $current_month

tar -zcvf $current_month.tar.gz $current_month

gsutil mv $current_month.tar.gz gs://aledb-logs

rm -r $current_month
cd
rm -r /tmp/aledblogs