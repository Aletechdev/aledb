import logging
import logging.config

# In a view or a middleware where the `request` object is available

from ipware import get_client_ip

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'standard': {
            'format': "[%(asctime)s] %(levelname)s [%(name)s] %(message)s",
        },

    },
    'handlers': {
        'file': {
            'formatter': 'standard',
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'debug.log',
            'mode': 'a',
            'maxBytes': 10485760,
            'backupCount': 10,
        },
        'console':{
            'formatter': 'standard',
            'class': 'logging.StreamHandler',
            'level': 'DEBUG',
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
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
            'handlers': ['file']
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

def get_user_ip(request):
    ip, is_routable = get_client_ip(request)
    if ip is None:
        return "Unknown IP"
    else:
        return ip

def getLogger(logname = None):
    logger = logging.getLogger(logname)
    return logger

class UserLoggingAdaptor(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        return '[%s] %s' % (self.extra['connid'], msg), kwargs

log = logging.getLogger("aledbLogger")


try:
    1/0
except ZeroDivisionError as e:
    log.exception("this is what an exception look like. The full trace should be genreated")