from .defaults import *

DEBUG = True

# secret key for local development can be shared
SECRET_KEY = '<DJANGO_KEY_REDACTED>'

# perhaps this should be set only for server deployed in private mode
MIDDLEWARE_CLASSES += (
    'accounts.login_middleware.LoginRequiredMiddleware',
)

INSTALLED_APPS += (
    'debug_toolbar',
)
