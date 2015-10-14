echo "DROP VIEW IF EXISTS id_mapping;" | python ../manage.py dbshell
python ../manage.py sqlclear seq | python manage.py dbshell
python ../manage.py sqlclear ale | python manage.py dbshell
python ../manage.py sqlall ale | python manage.py dbshell
python ../manage.py sqlall seq | python manage.py dbshell
