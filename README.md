# ALEdb
# General development
Every bug fix is a revision change in the version number!
## Docker Launch
### Required docker packages installed on host  
1. docker (version 17.09.0-ce)
2. docker-compose (version 1.17.0)

### Quick-start steps for ALEdb docker deployment
1. `docker-compose up`
2. Load database backup (dump) file to db container:
  a) copy aledb database dump file (e.g. aledb_dump.sql) to /tmp/docker
  b) login to db container and load data
    `docker-compose exec db bash`
    `mysql -u root -p`
    `use ale-db`
    'source /tmp/shared/aledb_dump.sql';  
3. `docker-compose run web python manage.py createsuperuser`; this will be the user and password to log into a live instance of ALEdb.
