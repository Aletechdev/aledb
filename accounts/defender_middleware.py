try:
    from django.utils.deprecation import MiddlewareMixin as MIDDLEWARE_BASE_CLASS
except ImportError:
    MIDDLEWARE_BASE_CLASS = object
from django.contrib.auth import views as auth_views
from django.utils.decorators import method_decorator
from django.core import mail

from defender import utils
import functools, logging
from logs.aledb_logger import user_extra


logger = logging.getLogger(__name__)


class FailedLoginMiddleware(MIDDLEWARE_BASE_CLASS):
    """ Failed login middleware """
    patched = False

    def __init__(self, *args, **kwargs):
        super(FailedLoginMiddleware, self).__init__(*args, **kwargs)
        # Watch the auth login.
        # Monkey-patch only once - otherwise we would be recording
        # failed attempts multiple times!
        if not FailedLoginMiddleware.patched:
            # Django 1.11 turned the `login` function view into the
            # `LoginView` class-based view
            try:
                from django.contrib.auth.views import LoginView
                our_decorator = watch_login()
                watch_login_method = method_decorator(our_decorator)
                LoginView.dispatch = watch_login_method(LoginView.dispatch)
            except ImportError:  # Django < 1.11
                auth_views.login = watch_login()(auth_views.login)

            FailedLoginMiddleware.patched = True


def watch_login(status_code=302, msg='',
                get_username=utils.get_username_from_request):
    """
    Used to decorate the django.contrib.admin.site.login method or
    any other function you want to protect by brute forcing.
    To make it work on normal functions just pass the status code that should
    indicate a failure and/or a string that will be checked within the
    response body.
    """
    def decorated_login(func):
        @functools.wraps(func)
        def wrapper(request, *args, **kwargs):
            # if the request is currently under lockout, do not proceed to the
            # login function, go directly to lockout url, do not pass go,
            # do not collect messages about this login attempt
            if utils.is_already_locked(request):
                return utils.lockout_response(request)

            # call the login function
            response = func(request, *args, **kwargs)

            if request.method == 'POST':
                # see if the login was successful
                if status_code == 302:  # standard Django login view
                    login_unsuccessful = (
                        response and
                        not response.has_header('location') and
                        response.status_code != status_code
                    )
                else:
                    # If msg is not passed the last condition will be evaluated
                    # always to True so the first 2 will decide the result.
                    login_unsuccessful = (
                        response and response.status_code == status_code
                        and msg in response.content.decode('utf-8')
                    )

                # ideally make this background task, but to keep simple,
                # keeping it inline for now.
                utils.add_login_attempt_to_db(request, not login_unsuccessful,
                                              get_username)

                if utils.check_request(request, login_unsuccessful,
                                       get_username):
                    return response
                send_lockout_email(request)
                return utils.lockout_response(request)

            return response

        return wrapper
    return decorated_login


def send_lockout_email(request):
    message = "User locked out. \n" + "User name: " + utils.get_username_from_request(request) + ", ip: " + utils.get_ip(request)
    logger.warning(message, user_extra(request))
    mail.mail_admins("user locked out", message, connection=mail.get_connection())
