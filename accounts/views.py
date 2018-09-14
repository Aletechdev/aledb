from django.contrib.auth import authenticate, login, logout
from dashboard.views import dashboard
from django.template import loader
from django.http import HttpResponse
from django.conf import settings
from logs.aledb_logger import get_logger,user_extra

usage_lgr = get_logger("usage")
security_lgr = get_logger("security")
exception_lgr = get_logger("exception")

def login_user(request):
    usage_lgr.info("login", extra = user_extra(request))

    try:
        logout(request)
        if request.POST:
            username = request.POST['username']
            password = request.POST['password']

            security_lgr.info("Log-in attempt from: " + username, extra={'account': username})
            user = authenticate(username=username, password=password)
            if user is not None:
                if user.is_active:
                    login(request, user)
                    security_lgr.info("Log-in success: " + username, extra={'account': username})
                    return dashboard(request)

        if request.method == "GET" and settings.PUBLIC:

            username = settings.PUBLIC_USERNAME
            password = settings.PUBLIC_PASSWORD
            user = authenticate(username=username, password=password)

            if user is not None:
                if user.is_active:
                    login(request, user)
                    security_lgr.info("Log-in success: " + username, extra={'account': username})
                    return dashboard(request)

        template = loader.get_template('login.html')

        return HttpResponse(template.render({"google_analytics_tag": settings.GOOGLE_ANALYTICS_TAG}, request), content_type="text/html")
    except Exception:
        exception_lgr.exception("login broke", extra = user_extra(request))