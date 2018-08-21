import logging
import logging.config
import sys

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
        'console': {
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
        'uncaughtexcept': {
            'level': 'WARNING',
            'propagate': True,
        },
    },
    'root': {
        'level': 'INFO',
        'handlers': ['file', 'console', 'mail_admins'],
    }
}

logging.config.dictConfig(LOGGING)


def getLogger(logname=None):
    logger = logging.getLogger(logname)

    return logger


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        print ("returning FORWARDED_FOR")
        ip = x_forwarded_for.split(',')[-1].strip()
    elif request.META.get('HTTP_X_REAL_IP'):
        print ("returning REAL_IP")
        ip = request.META.get('HTTP_X_REAL_IP')
    else:
        print ("returning REMOTE_ADDR")
        ip = request.META.get('REMOTE_ADDR')
    return ip


def getUserExtras(request):
    extras = {
        "userinfo": {
            "username": request.user,
            "ip-addr": get_client_ip(request),
            "session-id": request.session.session_key,
        },
        "path": request.path,
    }
    return extras


class UserLoggingAdaptor(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        return '%s %s' % (self.extra['connid'], msg), kwargs


log = logging.getLogger()



def handle_exception(exc_type, exc_value, exc_traceback):
    uncaughtexcept = logging.getLogger("uncaughtexcept")
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    uncaughtexcept.error("Uncaught exception")


sys.excepthook = handle_exception

try:
    1 / 0
except ZeroDivisionError as e:
    log.exception()
