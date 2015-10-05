echo "DROP VIEW id_mapping;" | python manage.py dbshell
python manage.py sqlclear seq | python manage.py dbshell
python manage.py syncdb
