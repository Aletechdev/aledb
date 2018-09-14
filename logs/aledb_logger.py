import logging
import logging.config
import uuid

__author__ = 'Muyao <3'


class UUIDFilter(logging.Filter):
    def filter(self, record):
        randomid = uuid.uuid1()
        record.uuid = randomid
        return True


LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'filters': {
        'uuidfilter': {
            '()': UUIDFilter,
        }
    },
    'formatters': {
        'standard': {
            'format': "[%(asctime)s] %(uuid)s %(levelname)s [%(name)s] [%(filename)s:%(lineno)s - %(funcName)20s] %(message)s",
            'class': 'pythonjsonlogger.jsonlogger.JsonFormatter'
        },
    },

    'handlers': {
        'file': {
            'formatter': 'standard',
            'level': 'DEBUG',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': 'logs/debug.log',
            'when': 'W0',
            'backupCount': 5,
            'filters': ['uuidfilter'],
        },
        'console': {
            'formatter': 'standard',
            'class': 'logging.StreamHandler',
            'level': 'DEBUG',
            'filters': ['uuidfilter'],

        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'filters': ['uuidfilter'],
        },
    },
    'loggers': {
        'security': {
            'level': 'DEBUG',
            'propagate': True,
        },
        'usage': {
            'level': 'DEBUG',
            'propagate': True,
        },
        'performance': {
            'level': 'DEBUG',
            'propagate': True,
        },
        'exceptions': {
            'level': 'WARNING',
            'propagate': True,
        },
    },
    'root': {
        'level': 'DEBUG',
        'handlers': ['file'],
    }
}


logging.config.dictConfig(LOGGING)


def get_logger(logname=None):
    logger = logging.getLogger(logname)

    return logger


def join_extras(*dict_args):
    """
        Given any number of dicts, shallow copy and merge into a new dict,
        precedence goes to key value pairs in latter dicts.
        """
    result = {}
    for dictionary in dict_args:
        result.update(dictionary)
    return result


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[-1].strip()
    elif request.META.get('HTTP_X_REAL_IP'):
        ip = request.META.get('HTTP_X_REAL_IP')
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def user_extra(request):
    extras = {
        "userinfo": {
            "username": request.user,
            "ip-addr": get_client_ip(request),
            "session-id": request.session.session_key,
        },
        "path": request.path,
    }
    return extras


def everything_extra(request):
    return request.__dict__


def all_get_extra(request):
    if 'GET' in request.__dict__:
        return request.__dict__['GET']
    else:
        return {}


def extra_variables(*variables):
    return locals()
