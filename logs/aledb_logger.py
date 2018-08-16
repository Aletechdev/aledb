import logging
import logging.config




LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'standard': {
            'format' : "logging things [%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
            'datefmt' : "%d/%b/%Y %H:%M:%S"
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

# A simple string logged at the "warning" level
log.warning("Your log message is here")

# A string with a variable at the "info" level
log.info("The value of var is %s", "hi")
