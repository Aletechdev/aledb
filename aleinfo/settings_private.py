# noinspection PyUnresolvedReferences
from .defaults import *

MIDDLEWARE += (
    'accounts.login_middleware.LoginRequiredMiddleware',
)
