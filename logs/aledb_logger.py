import logging
import logging.config


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
        'file-security': {
            'formatter': 'security',
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'debug.log',
            'mode': 'a',
            'maxBytes': 10485760,
            'backupCount': 10,
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

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
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