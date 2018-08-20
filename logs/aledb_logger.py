import logging
import logging.config
import json
from pythonjsonlogger import jsonlogger
# In a view or a middleware where the `request` object is available


LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'standard': {
            'format': "[%(asctime)s] %(levelname)s [%(name)s] [%(filename)s:%(lineno)s - %(funcName)20s] %(message)s",
            'class': 'pythonjsonlogger.jsonlogger.JsonFormatter'
        },
    },
    'handlers': {
        'file': {
            'formatter': 'standard',
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/debug.log',
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

def getLogger(logname = None):
    logger = logging.getLogger(logname)
    return logger

def get_client_ip(request):
    ip = request.META.get('HTTP_CF_CONNECTING_IP')
    if ip is None:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def getUserExtras(request):
    extras = {
        "userinfo":{
            "username": request.user,
            "ip-addr": get_client_ip(request),
        }
    }
    return extras

class UserLoggingAdaptor(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        return '%s %s' % (self.extra['connid'], msg), kwargs

log = logging.getLogger("aledbLogger")


try:
    1/0
except ZeroDivisionError as e:
    log.exception("this is what an exception look like. The full trace should be generated")