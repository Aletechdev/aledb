import logging
import logging.config




LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'standard': {
            'format' : "[%(asctime)s] %(levelname)s [%(name)s] %(message)s",
        },
    },
    'handlers': {
        'file': {
            'formatter': 'standard',
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'debug.log',
        },
        'console':{
            'formatter': 'standard',
            'class': 'logging.StreamHandler',
            'level': 'DEBUG',
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
        }
    },
    'loggers': {
        'aledbLogger': {

            'level': 'DEBUG',
            'propagate': True,

        },
        'security': {
            'level': 'WARNING',
            'propagate': True,
        },
        'performance': {
            'level': 'INFO',
            'propagate': True,
        },
        'usage': {
            'level': 'INFO',
            'propagate': True,
        },

    },
    'root':{
        'level': 'INFO',
        'handlers': ['file', 'console', 'mail_admins'],
    }
}

logging.config.dictConfig(LOGGING)

def getLogger(logname = None):
    return logging.getLogger(logname)


log = logging.getLogger("aledbLogger")

try:
    1/0
except ZeroDivisionError as e:
    log.error("this is what an exception look like")