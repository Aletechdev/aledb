# ALEdb
# General development
Every bug fix is a revision change in the version number!
## Docker Launch


### clone repo to /var/www/

### Install Docker
```
https://www.docker.com/products/docker-desktop

or for ubuntu systems:

https://docs.docker.com/install/
```

Then docker-compose:

```
https://docs.docker.com/compose/install/
```


### Set up host nginx

To install nginx:

```
sudo apt update
sudo apt install nginx
```

add the following to /etc/nginx/sites-enabled/default:

```
server {
        server_name aledb.org www.aledb.org 4.231.249.59;
    location / {
        proxy_pass http://127.0.0.1:8000;
    }
    location /aledata {
        alias /data/aledata;
        autoindex off;
        satisfy any;
    }
    location /static {
        alias /var/www/aledb/static;
    }
}
```

### Make necessary configuration changes:


#### aleinfo/defaults.py
```
Add IP address to ALLOWED_HOSTS in aleinfo/defaults.py
```
#### .docker/app.env
Key values to modify:
```
DEBUG: 1 or 0
PUBLIC: 1 or 0 # TODO: Obsoleted?
FORCE_SQLITE: 1 or 0
DEJANGO_SETTINGS_MODULE: aleinfo.settings_public or aleinfo.settings_private
```

Moving forward, default/public settings module should be enough


### For local Dev without connecting to SQL

```bash
#add FORCE_SQLITE=1 to e.g., .docker/one.env
# bring up services
docker-compose -f docker-compose-prod-asgi-host-nginx.yml up --build -d
# generate local sqlite3 file
docker-compose -f docker-compose-prod-asgi-host-nginx.yml exec web bash -c "python manage.py makemigrations && python manage.py migrate"
# test django
docker-compose -f docker-compose-prod-asgi-host-nginx.yml exec web bash -c "python manage.py test"
```

### For local Dev connected to local-Docker-SQL service

```bash
# Docker down:
docker-compose -f docker-compose-prod-asgi-host-nginx.yml down
# start a docker container to load the .sql file from ALEdb team
 docker run -d --rm \
  --name mysql-dump-load \
  -e MYSQL_ROOT_PASSWORD=XX \
  -e MYSQL_USER=ale \
  -e MYSQL_PASSWORD=XX \
  -v /local-path/to/dump.sql:/docker-entrypoint-initdb.d/init.sql \
  -e MYSQL_DATABASE=aledb_private \
  -p 3306:3306 \
  mysql:9.3
```
### Change the MYSQL config under .docker/one.env:
```yaml
MYSQL_DATABASE=aledb_private
MYSQL_USER=ale
MYSQL_PASSWORD=XX
MYSQL_PORT=3306
MYSQL_HOST=host.docker.internal
```
### run docker-compose
```bash
docker-compose -f docker-compose-prod-asgi-host-nginx.yml up --build -d
```

## For local Dev / Deployment connected to Azure-SQL service:
```yaml
MYSQL_DATABASE=aledb_private
MYSQL_USER=ale
MYSQL_PASSWORD= #Ask ALEdb team for credentials#
MYSQL_HOST=ale.mysql.database.azure.com
MYSQL_PORT=3306
```


### start the webapp with:

Either the quick start:
```
docker-compose -f docker-compose-prod-asgi-host-nginx.yml up --build -d
```

Or in a tmux session:

```
tmux -s new aledb
docker-compose -f docker-compose-prod-asgi-host-nginx.yml up --build
```

### Static files should be collected automatically but in case they weren't, collect existing static files:

```
rm -r static
```

```
docker exec -it aledb-web python3 manage.py collectstatic
```


### Bring all containers down
```
docker-compose down
```

### See log files
```
docker-compose logs
OR
docker-compse logs <service>
```


### To run scripts within containers

The general syntax is:

```
docker exec -it <name of container> <command>
```

To access the django python shell:

```
docker exec -it aledb-web python3 manage.py shell
```

To upload collections of experiments using root path(s):

```
docker exec -it aledb-web python3 manage.py upload path1 path2 path3...
```

*Remember the paths inside the containers may not be the same as the paths on the host machine!

To delete experiments using their individual ids:

```
docker exec -it aledb-web python3 manage.py delete 4 20 19 96...
```

To add publications for experiments using their ids:

```
docker exec -it aledb-web python3 manage.py add_publication 3 14 159... 


Please enter the publication title: Name of Publication Here
Please enter the publication URL: Full URL of Publication Here.
```

To make migrations and then migrate:

```
docker exec -it aledb-web python3 manage.py makemigrations
```
```
docker exec -it aledb-web python3 manage.py migrate
```

To collect static files for django:

```
docker exec -it aledb-web python3 manage.py collectstatic
```

To run all unit tests:

```
docker exec -it aledb-web bash -c "./manage.py test"
```

To generate coverage data from the containers:

```
docker exec -it aledb-web coverage run manage.py test

docker exec -it aledb-web coverage report

```


