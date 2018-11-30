from django.shortcuts import render

from common.util import get_user_context
from logs.aledb_logger import get_logger,user_extra

exception_lgr = get_logger("exceptions")
usage_lgr = get_logger("usage")


def bibliome(request):

    # TODO: use the template location described within settings.py

    usage_lgr.info("bibliome", extra = user_extra(request))
    try:

        return render(request, "bibliome/index.html", get_user_context(request.user), content_type="text/html")

    except Exception:
        exception_lgr.exception("bibliome broke", extra = user_extra(request))