"""DjangoAPIGuard with AleDB's route decorators registered.

djapi-guard consults the @guard_deco.* route limits only through the
middleware's decorator handler, and Django builds the middleware itself, so
this subclass registers guard_deco when Django creates it. With the stock
middleware the limits on the interop_query and mutations views never apply.
"""
from djangoapi_guard.middleware import DjangoAPIGuard

from aleinfo.guard import guard_deco


class AleDBGuardMiddleware(DjangoAPIGuard):
    def __init__(self, get_response):
        super().__init__(get_response)
        self.set_decorator_handler(guard_deco)
