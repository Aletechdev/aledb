# ALEdb
# General development
Every bug fix is a revision change in the version number!
## Docker Launch
### Required docker packages installed on host 
```
Install docker
https://www.docker.com/products/docker-desktop
```
### Quick-start steps for ALEdb docker deployment
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
