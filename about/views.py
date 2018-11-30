from django.http import HttpResponse

from common.util import get_user_context

from django.template import loader
from logs.aledb_logger import get_logger,user_extra

exception_lgr = get_logger("exceptions")
usage_lgr = get_logger("usage")


def about(request):

    # TODO: use the template location described within settings.py

    usage_lgr.info("about", extra=user_extra(request))

    try:
        template = loader.get_template("about/index.html")

        return HttpResponse(template.render(get_user_context(request.user), request), content_type="text/html")
    except Exception:
        exception_lgr.exception("about broke", extra=user_extra(request))
