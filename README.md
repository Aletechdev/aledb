# ALEdb
Platform for analyzing ALE mutational data.  
A complete draft of a Master of Science in Computer Science and Engineering thesis describing this platform and its scope can be found at the following:  
https://github.com/pvphaneuf/cse-ms-thesis/blob/master/patrick-phaneuf-cse.pdf  
Please refer to the wiki contained within this github project for technical documentation.
## Docker Launch
### Required docker packages installed on host  
1. docker (version 17.09.0-ce)
2. docker-compose (version 1.17.0)

### Quick-start steps for ALEdb docker deployment
1. `docker-compose up`
2. `docker-compose run web python manage.py createsuperuser`; this will be the user and password to log into a live instance of ALEdb.
