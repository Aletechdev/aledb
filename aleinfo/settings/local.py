from .defaults import *

DEBUG = True

# secret key for local development can be shared
SECRET_KEY = 'iv3^9^ccmwlfyeyp5q=%#z14p=p^6f1ujyzk8a3p*buzrg^2or'

# perhaps this should be set only for server deployed in private mode
MIDDLEWARE_CLASSES += (
    'login.login_middleware.LoginRequiredMiddleware',
)

INSTALLED_APPS += (
    'debug_toolbar',
)
