import logging
import logging.config




LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.RotatingFileHandler',
            'filename': 'debug.log',

        },
        'console':{
            'class': 'logging.StreamHandler',
            'level': 'DEBUG',
        },
    },
    'loggers': {
        'aledbLogger': {
            'handlers': ['file','console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'security': {
            'handlers': ['file', 'console'],
            'level': 'WARNING',
            'propagate': True,
        },
        'performance': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'usage': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

logging.config.dictConfig(LOGGING)

def getLogger(logname = None):
    return logging.getLogger(logname)


log = logging.getLogger("aledbLogger")

log.critical()

# A simple string logged at the "warning" level
log.warning("Your log message is here")

# A string with a variable at the "info" level
log.info("The value of var is %s", "hi")
