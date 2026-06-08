# ALEdb

[ALEdb](https://aledb.org) is a Django web application for cataloging
Adaptive Laboratory Evolution (ALE) experiments — tracking experimental
metadata, sequencing data, and genetic mutations across years of
microbial evolution studies conducted by [The Feist Lab](https://feistlab.ucsd.edu)
at UC San Diego.

**Live instance:** https://aledb.org

## Citation

If you use ALEdb in your work, please cite:

> Patrick V Phaneuf, Dennis Gosting, Bernhard O Palsson, Adam M Feist,
> *ALEdb 1.0: a database of mutations from adaptive laboratory evolution
> experimentation*, **Nucleic Acids Research**, Volume 47, Issue D1, 08
> January 2019, Pages D1164–D1171,
> <https://doi.org/10.1093/nar/gky983>

## License

ALEdb is licensed under the **UC Regents Educational / Research
License** — free for educational, research, and non-profit use.
Commercial use requires contacting the UCSD Technology Transfer Office
(<invent@ucsd.edu>). See [LICENSE](LICENSE) for full terms.

## Project history and provenance

This repository preserves contribution history going back to 2015. On
2026-06-08, in preparation for the public release, the following content
was scrubbed from git history:

- Historical database dumps containing `auth_user` password hashes and
  session artifacts.
- Dated application log files containing IP addresses and session
  identifiers.
- Rotated credential literals (all keys / passwords from prior commits
  replaced with redaction markers). The corresponding live credentials
  were rotated in late May / early June 2026 — none of the historical
  values still authenticate.

Researcher names, institutional email addresses, and git author /
committer metadata are **deliberately retained** for academic provenance
and citation purposes.

If you cloned this repository before 2026-06-08, please re-clone or
hard-reset to the new history (commit SHAs from 2015 onwards changed).
The full scrub plan and verification is documented in
[`docs/operations/`](docs/operations/).

## Repository contents

- **Django web application** — UI and REST API for the ALE database
  (`aleinfo/`, `alewebsite/`, `seq/`, etc.).
- **Sequencing pipeline** (`pipeline/`) — variant-calling and analysis
  scripts driven from Azure Batch.
- **Deployment configuration** — Docker Compose stacks for production
  (NGINX + ASGI + MySQL + Redis) and local development.
- **Operations documentation** (`docs/operations/`) — pre-publish secret
  audit, rotation runbook, deferred infrastructure-hardening tasks.

---

# Deployment

The remainder of this README is the operator / maintainer deployment
guide.

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

#### Setup Steps for New VM

**Step 1: Initial HTTP Configuration**

Create `/etc/nginx/sites-available/default` with basic HTTP setup:

```nginx
# WebSocket connection upgrade map
map $http_upgrade $connection_upgrade {
    default upgrade;
    '' close;
}

upstream django {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_request_buffering off;
        proxy_buffering off;
        proxy_read_timeout 3600;
        proxy_send_timeout 3600;
    }

    location /aledata {
        alias /data/aledata;
        autoindex off;
        satisfy any;
    }

    location /static {
        alias /var/www/aledb/static;
    }

    # WebSocket support
    location /ws/ {
        proxy_pass http://django;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade;
        proxy_set_header Host $http_host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Host $server_name;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }
}
```

Enable the site and test configuration:
```bash
sudo ln -s /etc/nginx/sites-available/default /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx
```

**Step 2: Obtain SSL Certificates**

Install Certbot and obtain certificates:
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

Certbot will automatically modify your nginx configuration to add SSL support.

**Step 3: Verify Final Configuration**

After Certbot runs, your configuration should look like the production setup below.

#### Current Production Configuration

The nginx configuration is located at `/etc/nginx/sites-enabled/default` (symlinked from `/etc/nginx/sites-available/default`).

**Port Configuration:**
- **Port 80 (HTTP)**: Redirects all traffic to HTTPS (port 443)
- **Port 443 (HTTPS)**: Main server with SSL certificates from Let's Encrypt

**Docker Port Mapping:**
When using `ports: 8000:80` in docker-compose, the mapping is:
```
External → Host port 8000 → Container port 80 (nginx) → Redirects to port 443 (HTTPS) → Proxies to Django at 127.0.0.1:8000
```

**Note**: For production, consider using `ports: 80:80` and `443:443` to properly expose both HTTP and HTTPS ports.

**Full Production Configuration:**

```nginx
# HTTP Server (Port 80) - Redirects to HTTPS
server {
    listen 80;
    server_name aledb.org www.aledb.org;
    return 301 https://$host$request_uri;
}

# HTTPS Server (Port 443) - Main Application
server {
    listen 443 ssl;
    server_name aledb.org www.aledb.org 4.231.249.59;

    # SSL Configuration (managed by Certbot)
    ssl_certificate /etc/letsencrypt/live/aledb.org/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/aledb.org/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    # Main application proxy
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_request_buffering off;
        proxy_buffering off;
        proxy_read_timeout 3600;
        proxy_send_timeout 3600;
    }

    # Data files
    location /aledata {
        alias /data/aledata;
        autoindex off;
        satisfy any;
    }

    # Static files
    location /static {
        alias /var/www/aledb/static;
    }

    # WebSocket support
    location /ws/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade;
        proxy_set_header Host $http_host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Host $server_name;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }
}

# WebSocket connection upgrade map (defined at top level)
map $http_upgrade $connection_upgrade {
    default upgrade;
    '' close;
}
```

**SSL Certificates:**
Certificates are managed by Certbot (Let's Encrypt) and renew automatically. To manually renew:
```bash
sudo certbot renew
```

### For production: connect azure-storage-container as a local folder:

> [!IMPORTANT]
>
> Some results files, e.g, breseq html output, are side loaded from Azure to the Server, blobfuse is used to synchronize account:aledata -> container:aledata to /data folder. For local dev, it is okay to skip this step.
>
> Format og azure config file `sudo cat /cfg/azure_pipeline_out.cfg`: 
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
> # Input files:
> sudo blobfuse /pipeline_inputs --tmp-path=/mnt/resource/indirtmp -o allow_other --config-file=/cfg/azure_pipeline_in.cfg -o attr_timeout=240 -o entry_tim
eout=240 -o negative_timeout=120
> ```
>
> **Note:** Always mount the Azure Blob storage BEFORE starting Docker containers. If Docker starts first, it will bind to an empty directory and require a restart after mounting: `sudo docker-compose -f docker-compose-prod-asgi-host-nginx.yml restart web`

### Make necessary configuration changes:

Add the VM's IP to MySQL server whitelist: [link](https://portal.azure.com/#@dtudk.onmicrosoft.com/resource/subscriptions/aee8556f-d2fd-4efd-a6bd-f341a90fa76e/resourceGroups/rg-ALEdb/providers/Microsoft.DBforMySQL/flexibleServers/ale/networking)


#### aleinfo/defaults.py
```bash
#Add IP address to ALLOWED_HOSTS in aleinfo/defaults.py
# for direct access like https://20.82.182.70 (VM's IP), the IP need to be added to ALLOWED_HOSTS and CSRF_TRUSTED_ORIGINS, e.g.,:
-ALLOWED_HOSTS = [os.environ.get('DJANGO_SERVER_HOST', 'localhost'), 'localhost', '127.0.0.1', '35.236.92.37', '0.0.0.0',
+ALLOWED_HOSTS = [os.environ.get('DJANGO_SERVER_HOST', 'localhost'), 'localhost', '127.0.0.1', '35.236.92.37', '0.0.0.0', '4.231.249.59'
...
-CSRF_TRUSTED_ORIGINS = ["http://127.0.0.1:8000", "http://localhost:8000", "https://aledb.org", "https://www.aledb.org"]
+CSRF_TRUSTED_ORIGINS = ["http://127.0.0.1:8000", "http://localhost:8000", "https://aledb.org", "https://www.aledb.org", "https://20.82.182.70"]

```
### Environment Configuration (`.docker/one.env`)
This file contains sensitive settings (credentials and runtime configuration) and is excluded from version control on GitHub

Key values to modify:
```bash
# ${GitRepo}/.docker/one.env
DEBUG=0 # set 1 for viewing error on browser
PUBLIC=0 # Obsoleted, keep at 0
FORCE_SQLITE=0 # set 1 to launch service with 'empty' SQLite service hosted by Django
DJANGO_SETTINGS_MODULE=aleinfo.settings_public
DJANGO_SERVER_HOST=127.0.0.1
# add your IP to whitelist on:
# https://portal.azure.com/#@dtudk.onmicrosoft.com/resource/subscriptions/aee8556f-d2fd-4efd-a6bd-f341a90fa76e/resourceGroups/rg-ALEdb/providers/Microsoft.DBforMySQL/flexibleServers/ale/networking
MYSQL_DATABASE=aledb_private #there are two other db aledb_public, ealedb, not called in this code base
MYSQL_USER=ale
MYSQL_PASSWORD= #Ask ALEdb admin #TODO: discuss when to store safely
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
>   # ${GitRepo}/.docker/one.env
>   DEBUG=0 # set 1 for viewing error on browser
>   PUBLIC=0 # Obsoleted, keep at 0
>   FORCE_SQLITE=0 # set 1 to launch service with 'empty' SQLite service hosted by Django
>   DJANGO_SETTINGS_MODULE=aleinfo.settings_public
>   DJANGO_SERVER_HOST=127.0.0.1
>   # add your IP to whitelist on:
>   # https://portal.azure.com/#@dtudk.onmicrosoft.com/resource/subscriptions/aee8556f-d2fd-4efd-a6bd-f341a90fa76e/resourceGroups/rg-ALEdb/providers/Microsoft.DBforMySQL/flexibleServers/ale/networking
>   MYSQL_DATABASE=aledb_private
>   MYSQL_USER=ale
>   MYSQL_PASSWORD= #Ask ALEdb team for credentials#TODO: discuss when to store safely
>   MYSQL_HOST=ale.mysql.database.azure.com
>   MYSQL_PORT=3306
>   REDIS_URL=redis://aledb-redis
>   ALE_DATA_ROOT_DIR=/data/aledata/ #local mount/datafor Azure storage account:aledata -> container:aledata
>   SEQUENCING_URL=/aledata/ # Used to generate public-facing URLs for results.
>   ```

Check if containers are running:

```bash
sudo docker ps
# log of running/previous run
sudo docker-compose -f docker-compose-prod-asgi-host-nginx.yml logs web
```

#### Start the webapp with:

Either the quick start, `add -d will run the services in background`:

```bash
docker-compose -f docker-compose-prod-asgi-host-nginx.yml up --build #-d
```

Or in a tmux session:

```bash
tmux -s new aledb
sudo docker-compose -f docker-compose-prod-asgi-host-nginx.yml up --build
```

Stop the services:

```bash
sudo docker-compose -f docker-compose-prod-asgi-host-nginx.yml down 
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
>   # ${GitRepo}/.docker/one.env
>   DEBUG=0 # set 1 for viewing error on browser
>   PUBLIC=0 # Obsoleted, keep at 0
>   FORCE_SQLITE=0 # set 1 to launch service with 'empty' SQLite service hosted by Django
>   DJANGO_SETTINGS_MODULE=aleinfo.settings_public
>   DJANGO_SERVER_HOST=127.0.0.1
>   # different MYSQL setting:
>   MYSQL_DATABASE=aledb_private
>   MYSQL_USER=ale
>   MYSQL_PASSWORD=XX
>   MYSQL_PORT=3306
>   MYSQL_HOST=host.docker.internal
>   REDIS_URL=redis://aledb-redis
>   SEQUENCING_URL=/aledata/ # Used to generate public-facing URLs for results.
> ```

#### Run docker-compose
```bash
# Docker down if running:
sudo docker-compose -f docker-compose-prod-asgi-host-nginx.yml down
sudo docker-compose -f docker-compose-prod-asgi-host-nginx.yml up --build -d
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

