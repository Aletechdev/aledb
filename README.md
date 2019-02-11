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

add the following to /etc/nginx/sites-enabled:

```
server {
    server_name aledb.org www.aledb.org;
    location / {
        proxy_pass http://127.0.0.1:8000;
    }
    location /aledata {
        alias /var/www/ale_analytics_data;
        autoindex on;
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
PUBLIC: 1 or 0
DEJANGO_SETTINGS_MODULE: aleinfo.settings_public or aleinfo.settings_private
```

Moving forward, default/public settings module should be enough

### Change the database dump file to the desired dump file


### start the webapp with:

Either the quick start:
```
docker-compose up -d
```
 
Or in a tmux session:

```
tmux -s new aledb
docker-compose up
```

### Static files should be collected automatically but in case they weren't, collect existing static files:

```
rm -r static
```

```
docker exec -it aledb-web python3 manage.py collectstatic
```

## Quick-start steps for ALEdb docker deployment
 ```
 docker-compose up -d
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

### Load test data from new database dump file
1. Replace dump file in .docker/data folder. 
2. Remove database image
```
docker rmi mysql:5.7
```
3. Restart 
```
docker-compose up -d
```


### To run scripts within containers

The general syntax is:

```
docker exec -it <name of container> <command(s)>
```

To access the django python shell:

```
docker exec -it aledb-web python3 manage.py shell
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

To browse the database:

```
sudo docker exec -it aledb-database mysql -u ale -p
```
