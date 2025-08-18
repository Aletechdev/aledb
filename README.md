# ALEdb
> [!WARNING]
>
> ⚠️ Do NOT commit `.env` files to version control. Use `.gitignore` to exclude them.

## Table of Contents

- [ALEdb](#aledb)
  - [Table of Contents](#table-of-contents)
  - [Configuration:](#configuration)
    - [Clone Git repository](#clone-git-repository)
    - [Install Docker](#install-docker)
    - [Set up host NGINX for VM server for networking](#set-up-host-nginx-for-vm-server-for-networking)
    - [For production: connect azure-storage-container as a local folder:](#for-production-connect-azure-storage-container-as-a-local-folder)
    - [Make necessary configuration changes:](#make-necessary-configuration-changes)
      - [aleinfo/defaults.py](#aleinfodefaultspy)
    - [Environment Configuration (`.docker/one.env`)](#environment-configuration-dockeroneenv)
  - [Running services:](#running-services)
    - [Start / attach tmux's persistent sessions](#start--attach-tmuxs-persistent-sessions)
    - [Production / Local dev connected to Azure MySQL](#production--local-dev-connected-to-azure-mysql)
      - [Start the webapp with:](#start-the-webapp-with)
    - [Alternative: Local with MySQL](#alternative-local-with-mysql)
      - [Run docker-compose](#run-docker-compose)
    - [Alternative: Local with SQLite](#alternative-local-with-sqlite)
  - [Maintenance:](#maintenance)
    - [Static files should be collected automatically but in case they weren't, collect existing static files:](#static-files-should-be-collected-automatically-but-in-case-they-werent-collect-existing-static-files)
    - [Bring all containers down](#bring-all-containers-down)
    - [See log files](#see-log-files)
    - [To run scripts within containers](#to-run-scripts-within-containers)

## Configuration:

### Clone Git repository

For VM server: clone repo to /var/www/

For local dev: `git clone git@github.com:Aletechdev/aledb.git`

### Install Docker
```tex
https://www.docker.com/products/docker-desktop

or for ubuntu systems:

https://docs.docker.com/install/
```

Then docker-compose:

```tex
https://docs.docker.com/compose/install/
```


### Set up host NGINX for VM server for networking

To install nginx:

```bash
sudo apt update
sudo apt install nginx
```

add the following to /etc/nginx/sites-enabled/default:

```yaml
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

### For production: connect azure-storage-container as a local folder:

> [!IMPORTANT]
>
> Some results files, e.g, breseq html output, are side loaded from Azure to the Server, blobfuse is used to synchronize account:aledata -> container:aledata to /data folder. For local dev, it is okay to skip this step.
>
> Format og azure config file`cat /cfg/azure_pipeline_out.cfg`: 
>
> ```ini
> # azure_aledata.cfg:
> accountName aledata
> accountKey XXX-from-Azure-portal-Key1
> containerName aledata
> # azure_pipeline_out.cfg:
> accountName aledata
> accountKey XXX
> containerName output
> ```
>
> ```bash
> # Pipeline Output
> sudo blobfuse /output --tmp-path=/mnt/resource/outdirtmp  --config-file=/cfg/azure_pipeline_out.cfg -o attr_timeout=240 -o entry_timeout=240 -o negative_timeout=120
> # Evidence Files and Upload
> sudo blobfuse /data --tmp-path=/mnt/resource/blobfusetmp -o allow_other --config-file=/cfg/azure_aledata.cfg -o attr_timeout=240 -o entry_timeout=240 -o negative_timeout=120
> ```
>

### Make necessary configuration changes:


#### aleinfo/defaults.py
```bash
#Add IP address to ALLOWED_HOSTS in aleinfo/defaults.py
```
### Environment Configuration (`.docker/one.env`)
This file contains sensitive settings (credentials and runtime configuration) and is excluded from version control on GitHub

Key values to modify:
```bash
# ${GitRepo}/.docker/one.env
DEBUG=0 # set 1 for viewing error on browser
PUBLIC=0 # Obsoleted, keep at 1
FORCE_SQLITE=0 # set 1 to launch service with 'empty' SQLite service hosted by Django
DJANGO_SETTINGS_MODULE=aleinfo.settings_public
DJANGO_SERVER_HOST=127.0.0.1

MYSQL_DATABASE=aledb_private #there are two other db aledb_public, ealedb, not called in this code base
MYSQL_USER=ale
MYSQL_PASSWORD= #Ask ALEdb admin
MYSQL_HOST=ale.mysql.database.azure.com
MYSQL_PORT=3306
REDIS_URL=redis://aledb-redis
ALE_DATA_ROOT_DIR=/data/aledata/ #local mount/datafor Azure storage account:aledata -> container:aledata
SEQUENCING_URL=/aledata/ # Used to generate public-facing URLs for results.
```

## Running services:

### Start / attach tmux's persistent sessions

```bash
tmux new -s aledb
# detach with Ctrl-b d
# re-connect:
tmux attach -t aledb
```

### Production / Local dev connected to Azure MySQL

> [!IMPORTANT]
>
> - Add machine's IP for accessing the databases: https://portal.azure.com/#@dtudk.onmicrosoft.com/resource/subscriptions/aee8556f-d2fd-4efd-a6bd-f341a90fa76e/resourceGroups/rg-ALEdb/providers/Microsoft.DBforMySQL/flexibleServers/ale/networking
>
> - Edit MYSQL setting under `.docker/one.env`
>
>   ```bash
>   # related setting in .docker/one.env
>   # ${GitRepo}/.docker/one.env
>   DEBUG=0 # set 1 for viewing error on browser
>   PUBLIC=0 # Obsoleted, keep at 1
>   FORCE_SQLITE=0 # set 1 to launch service with 'empty' SQLite service hosted by Django
>   DJANGO_SETTINGS_MODULE=aleinfo.settings_public
>   DJANGO_SERVER_HOST=127.0.0.1
>   # add your IP to whitelist on:
>   # https://portal.azure.com/#@dtudk.onmicrosoft.com/resource/subscriptions/aee8556f-d2fd-4efd-a6bd-f341a90fa76e/resourceGroups/rg-ALEdb/providers/Microsoft.DBforMySQL/flexibleServers/ale/networking
>   MYSQL_DATABASE=aledb_private
>   MYSQL_USER=ale
>   MYSQL_PASSWORD= #Ask ALEdb team for credentials#
>   MYSQL_HOST=ale.mysql.database.azure.com
>   MYSQL_PORT=3306
>   REDIS_URL=redis://aledb-redis
>   ```

Check if containers are running:

```bash
docker ps
docker-compose -f docker-compose-prod-asgi-host-nginx.yml logs web
```

#### Start the webapp with:

Either the quick start, `-d will run the services in background`:

```bash
docker-compose -f docker-compose-prod-asgi-host-nginx.yml up --build -d
```

Or in a tmux session:

```bash
tmux -s new aledb
docker-compose -f docker-compose-prod-asgi-host-nginx.yml up --build
```

Stop the services:

```bash
docker-compose -f docker-compose-prod-asgi-host-nginx.yml down 
```

### Alternative: Local with MySQL

> [!NOTE]
>
> ⚠️ Ask ALEdb admin for the .sql file, or use `$mysqldump`
>
> ```bash
> docker run --rm -e MYSQL_PWD='#AskAdmin#' -v $PWD:/backup mysql:8 \
>   sh -c 'mysqldump -h ale.mysql.database.azure.com -u ale  \
>   --triggers --routines --events \
>   --set-gtid-purged=OFF \
>   --single-transaction \
>   --databases aledb_private aledb_public ealedb  > /backup/dump_20250422_private_public_ealedb.sql'
> ```
>
> ```bash
> # Launch a SQL container
> # start a docker container to load the .sql file from ALEdb team
>  docker run -d --rm \
>   --name mysql-dump-load \
>   -e MYSQL_ROOT_PASSWORD=XX \
>   -e MYSQL_USER=ale \
>   -e MYSQL_PASSWORD=XX \
>   -v /local-path/to/dump.sql:/docker-entrypoint-initdb.d/init.sql \
>   -e MYSQL_DATABASE=aledb_private \
>   -p 3306:3306 \
>   mysql:9.3
> ```
>
> #### Change the MYSQL config under .docker/one.env:
>
> ```bash
> MYSQL_DATABASE=aledb_private
> MYSQL_USER=ale
> MYSQL_PASSWORD=XX
> MYSQL_PORT=3306
> MYSQL_HOST=host.docker.internal
> ```

#### Run docker-compose
```bash
# Docker down if running:
docker-compose -f docker-compose-prod-asgi-host-nginx.yml down
docker-compose -f docker-compose-prod-asgi-host-nginx.yml up --build -d
```

### Alternative: Local with SQLite

> [!WARNING]
>
> An empty SQLite service will be manged by Django, and will contain no real data (e.g., users, mutations)
>
> Change FORCE_SQLITE=1 in `.docker/one.env`
>
> ```bash
> # Docker down if running:
> docker-compose -f docker-compose-prod-asgi-host-nginx.yml down
> # bring up services
> docker-compose -f docker-compose-prod-asgi-host-nginx.yml up --build -d
> # generate local sqlite3 file
> docker-compose -f docker-compose-prod-asgi-host-nginx.yml exec web bash -c "python manage.py makemigrations && python manage.py migrate"
> # test django
> docker-compose -f docker-compose-prod-asgi-host-nginx.yml exec web bash -c "python manage.py test"
> ```
>
> 



------



## Maintenance:

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

