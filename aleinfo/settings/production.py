from .defaults import *

DEBUG = False

# if we are using os-environ, make sure that we have it set here
# otherwise, we want a KeyError to be thrown, rather than running
# production with what could be an unintentinally-set key
SECRET_KEY = os.environ['SECRET_KEY']
#SECRET_KEY = '<DJANGO_KEY_REDACTED>'
