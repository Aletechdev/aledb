import os
import sys

# DEBUG = os.environ.get('DEBUG', '0') == '1'
DEBUG = True

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

SEQUENCING_URL = os.environ.get('SEQUENCING_URL', 'https://aquaticus.ucsd.edu/aledata/')

ADMINS = ()

MANAGERS = ADMINS

'''
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
'''
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': "ale_db",
        'USER': "root",
        'PASSWORD': "m0t0r0l6",
        'HOST': "localhost",
        'PORT': 3306,
        }
    }

# XXX(lyschoening) what does this refer to?
OTHER_USERNAME = os.environ.get('OTHER_DATABASE_USERNAME', 'other_database_username')
OTHER_PASSWORD = os.environ.get('OTHER_DATABASE_', 'other_database_password')

ALE_DATA_ROOT_DIR = os.environ.get('ALE_DATA_ROOT_DIR', 'ale_data_root_dir')

ALLOWED_HOSTS = [os.environ.get('DJANGO_SERVER_HOST', 'localhost')]

USE_X_FORWARDED_PORT = os.environ.get('USE_X_FORWARDED_PORT', '0') == '1'


# Likely has to be after initial DATABASES definition.
# This is used for unit testing of django code.
if 'test' in sys.argv or 'test_coverage' in sys.argv: #Covers regular testing and django-coverage
    DATABASES['default']['ENGINE'] = 'django.db.backends.sqlite3'

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = os.environ.get('TIME_ZONE', 'America/Los_Angeles')

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

# Make this unique, and don't share it with anybody.
SECRET_KEY = os.environ.get('SECRET_KEY', 'iv3^9^ccmwlfyeyp5q=%#z14p=p^6f1ujyzk8a3p*buzrg^2or')

SEQ_TEMPLATE_PATH = os.path.join(BASE_DIR, 'seq/templates')
FILTER_TEMPLATE_PATH = os.path.join(BASE_DIR, 'filter/templates')
FIXATION_TEMPLATE_PATH = os.path.join(BASE_DIR, 'fixation/templates')
LOGIN_TEMPLATE_PATH = os.path.join(BASE_DIR, 'accounts/templates')
EXPORT_TEMPLATE_PATH = os.path.join(BASE_DIR, 'export/templates')
COMPARE_TEMPLATE_PATH = os.path.join(BASE_DIR, 'compare/templates')
COMMON_TEMPLATE_PATH = os.path.join(BASE_DIR, 'common/templates')
DASHBOARD_TEMPLATE_PATH = os.path.join(BASE_DIR, 'dashboard/templates')
SEARCH_TEMPLATE_PATH = os.path.join(BASE_DIR, 'search/templates')
DUPLICATION_TEMPLATE_PATH = os.path.join(BASE_DIR, 'duplications/templates')
GENES_TEMPLATE_PATH = os.path.join(BASE_DIR, 'genes/templates')
METADATA_TEMPLATE_PATH = os.path.join(BASE_DIR, 'metadata/templates')
ABOUT_TEMPLATE_PATH = os.path.join(BASE_DIR, 'about/templates')
BIBLIOME_TEMPLATE_PATH = os.path.join(BASE_DIR, 'bibliome/templates')
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [SEQ_TEMPLATE_PATH,
                 FILTER_TEMPLATE_PATH,
                 FIXATION_TEMPLATE_PATH,
                 LOGIN_TEMPLATE_PATH,
                 COMPARE_TEMPLATE_PATH,
                 EXPORT_TEMPLATE_PATH,
                 COMMON_TEMPLATE_PATH,
                 DASHBOARD_TEMPLATE_PATH,
                 SEARCH_TEMPLATE_PATH,
                 DUPLICATION_TEMPLATE_PATH,
                 GENES_TEMPLATE_PATH,
                 METADATA_TEMPLATE_PATH,
                 ABOUT_TEMPLATE_PATH,
                 BIBLIOME_TEMPLATE_PATH
                 ],
        'OPTIONS': {
            'context_processors': [
                # Insert your TEMPLATE_CONTEXT_PROCESSORS here or use this
                # list if you haven't customized them:
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
            ],
            'debug': DEBUG,
            'loaders': ['django.template.loaders.filesystem.Loader',
                        'django.template.loaders.app_directories.Loader'],
        },
    },
]

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    # 'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

LOGIN_URL = '/accounts/login/'

ROOT_URLCONF = 'aleinfo.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'aleinfo.wsgi.application'

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'ale',
    'seq',
    'filter',
    'fixation',
    'stats',
    'metadata',
    'about',
    'enrichment',
    'accounts',
    'compare',
    'export',
    'common',
    'dashboard',
    'search',
    'duplications',
    'genes',
    'debug_toolbar',
)

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
        },
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'cache_table',
    }
}

PUBLIC = os.environ.get('PUBLIC', '0') == '1'
PUBLIC_USERNAME = os.environ.get('PUBLIC_USERNAME', 'public')
PUBLIC_PASSWORD = os.environ.get('PUBLIC_PASSWORD', 'public_password')
