import logging
import logging.config




LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'standard': {
            'format' : "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
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
        'handlers': ['file', 'console'],

    }
}

logging.config.dictConfig(LOGGING)

def getLogger(logname = None):
    return logging.getLogger(logname)


log = logging.getLogger("aledbLogger")
