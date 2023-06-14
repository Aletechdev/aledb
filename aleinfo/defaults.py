import os
import sys


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DEBUG = os.environ.get('DEBUG', '0') == '1'

GOOGLE_ANALYTICS_TAG = os.environ.get('GOOGLE_ANALYTICS_TAG', 'no-google-analytics-tag')
SEQUENCING_URL = os.environ.get('SEQUENCING_URL', 'http://sbrg.ucsd.edu/')
ALE_DATA_ROOT_DIR = os.environ.get('ALE_DATA_ROOT_DIR', 'ale_data_root_dir')


ALLOWED_HOSTS = [os.environ.get('DJANGO_SERVER_HOST', 'localhost'), '127.0.0.1', '35.236.92.37', 'ale.ucsd.edu']
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_AGE = 3600  # in seconds, 1hr
SESSION_SAVE_EVERY_REQUEST = True


INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_tables2',
    "django_filters",
    "bootstrap3",
    "bootstrap4",
    'defender',
    'ale',
    'seq',
    'filter',
    'fixation',
    'stats',
    'metadata',
    'about',
    'enrichment',
    'evidence',
    'converge',
    'accounts',
    'export',
    'md_export',
    'common',
    'dashboard',
    'search',
    'genes',
    'bibliome',
    'pipeline',
    'debug_toolbar',
    'guardian',
)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('MYSQL_DATABASE', 'database'),
        'USER': os.environ.get('MYSQL_USER', 'user'),
        'PASSWORD': os.environ.get('MYSQL_PASSWORD', 'password'),
        'HOST': os.environ.get('MYSQL_HOST', 'db'),
        'PORT': int(os.environ.get('MYSQL_PORT', 3306)),
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'cache_table',
    }
}

MIDDLEWARE_CLASSES = (
    'django.middleware.common.BrokenLinkEmailsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'accounts.defender_middleware.FailedLoginMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

AUTHENTICATION_BACKENDS = (
    # 'axes.backends.AxesModelBackend',
    'django.contrib.auth.backends.ModelBackend',
    'guardian.backends.ObjectPermissionBackend',
)


LOGIN_URL = '/accounts/login/'
ROOT_URLCONF = 'aleinfo.urls'
LOGIN_REDIRECT_URL = 'experiments_view'
LOGOUT_REDIRECT_URL = 'experiments_view'
# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'aleinfo.wsgi.application'


# XXX(lyschoening) what does this refer to?
OTHER_USERNAME = os.environ.get('OTHER_DATABASE_USERNAME', 'other_database_username')
OTHER_PASSWORD = os.environ.get('OTHER_DATABASE_', 'other_database_password')

USE_X_FORWARDED_PORT = os.environ.get('USE_X_FORWARDED_PORT', '0') == '1'


# Likely has to be after initial DATABASES definition.
# This is used for unit testing of django code.
if 'test' in sys.argv or 'test_coverage' in sys.argv: #Covers regular testing and django-coverage
    DATABASES['default']['ENGINE'] = 'django.db.backends.sqlite3'

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'America/Los_Angeles'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: '/home/media/media.lawrence.com/media/'
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: 'http://media.lawrence.com/media/', 'http://example.com/media/'
MEDIA_URL = ''

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' 'static/' subdirectories and in STATICFILES_DIRS.
# Example: '/home/media/media.lawrence.com/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATIC_URL = '/static/'
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'common/staticfiles'),
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    #    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

GUARDIAN_RAISE_403 = True

# Make this unique, and don't share it with anybody.
SECRET_KEY = os.environ.get('SECRET_KEY', '<DJANGO_KEY_REDACTED>')

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                # Insert your TEMPLATE_CONTEXT_PROCESSORS here or use this
                # list if you haven't customized them:
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
                'aleinfo.context_processors.global_settings',
            ],
            'debug': DEBUG,
        },
    },
]

###########
# LOGGING #
###########

# Default exception reporter filter class used in case none has been
# specifically assigned to the HttpRequest instance.
DEFAULT_EXCEPTION_REPORTER_FILTER = 'django.views.debug.SafeExceptionReporterFilter'

# Custom logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue'
        },
        'uuidfilter': {
            '()': 'logs.aledb_logger.UUIDFilter'
        }
    },
    'formatters': {
        'simple': {
            'format': '{levelname} {asctime} {name}:{lineno} - {message}',
            'style': '{',
        },
        'standard': {
            'format': "[%(asctime)s] %(uuid)s %(levelname)s [%(name)s:%(lineno)s - %(funcName)20s] %(message)s",
            'class': 'pythonjsonlogger.jsonlogger.JsonFormatter'
        },
    },
    'handlers': {
        'file': {
            'formatter': 'standard',
            'level': 'INFO',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': 'logs/debug.log',
            'when': 'W0',
            'backupCount': 5,
            'filters': ['uuidfilter'],
        },
        'console': {
            'formatter': 'simple',
            'class': 'logging.StreamHandler',
            'level': 'DEBUG',
            'filters': ['uuidfilter', 'require_debug_true'],
        },
        'mail_admins': {
            'level': 'CRITICAL',
            'class': 'django.utils.log.AdminEmailHandler',
            'filters': ['uuidfilter', 'require_debug_false'],
        },
    },
    'loggers': {
        '': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'django': {
            'level': 'ERROR',
            'handlers': ['console', 'file', 'mail_admins'],
            'propagate': False,
        }
    },
}


PUBLIC = os.environ.get('PUBLIC', '0') == '1'
PUBLIC_USERNAME = os.environ.get('PUBLIC_USERNAME', 'public')
PUBLIC_PASSWORD = os.environ.get('PUBLIC_PASSWORD', 'public_password')

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_USE_TLS = True
EMAIL_PORT = 587
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', 'aledbsoftware')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '<GMAIL_PASSPHRASE_REDACTED>')

SERVER_EMAIL = os.environ.get('SERVER_EMAIL', 'aledbsoftware+admin@gmail.com')
DEFAULT_FROM_EMAIL = 'aledbsoftware+default@gmail.com'
MAILER_LIST = ['rcai@eng.ucsd.edu']
ADMINS = [('Robin Cai', 'rcai@ucsd.edu')]

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 9,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# DEFENDER_LOGIN_FAILURE_LIMIT = 3
DEFENDER_LOGIN_FAILURE_LIMIT_USERNAME = int(os.environ.get('DEFENDER_LOGIN_FAILURE_LIMIT_USERNAME', 2))
DEFENDER_LOGIN_FAILURE_LIMIT_IP = int(os.environ.get('DEFENDER_LOGIN_FAILURE_LIMIT_IP', 3))

DEFENDER_COOLOFF_TIME = int(os.environ.get('DEFENDER_COOLOFF_TIME', 30))  # sec
DEFENDER_REDIS_URL = os.environ.get('REDIS_URL', 'redis://:<REDIS_PW_REDACTED>@aledb-redis:6379/1')


# For Bootstrap 3, change error alert to 'danger'
from django.contrib import messages
MESSAGE_TAGS = {
    messages.ERROR: 'danger'
}
