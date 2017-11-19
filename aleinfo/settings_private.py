# noinspection PyUnresolvedReferences
from .defaults import *

MIDDLEWARE_CLASSES += (
    'accounts.login_middleware.LoginRequiredMiddleware',
)
