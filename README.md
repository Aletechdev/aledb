# ALE Analytics
Platform for analyzing ALE mutational data.  
A complete draft of a Master of Science in Computer Science and Engineering thesis describing this platform and its scope can be found at the following:  
https://github.com/pvphaneuf/cse-ms-thesis/blob/master/patrick-phaneuf-cse.pdf  
Please refer to the wiki contained within this github project for technical documentation.
## Docker Launch
### Required docker packages installed on host  
1. docker
2. docker-compose

### Quick-start steps for ALE Analytics docker deployment
1. `docker-compose up`
2. `docker-compose run web python manage.py collectstatis`
3. `docker-compose run web python manage.py migrate`
4. `docker-compose run web python manage.py createsuperuser`; this will be the user and password to log into a live instance of ALE Analytics.
5. `docker-compose run web python manage.py createcachetable`

## TODOs:  
* Describe the workflow for integrating ALE experiments within the wiki.
* cite: https://github.com/bbglab/muts-needle-plot  
* cite" PV Viewer
