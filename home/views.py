from django.http import HttpResponse

from common.util import get_user_context

from django.template import loader
from logs.aledb_logger import user_extra
import logging


logger = logging.getLogger(__name__)


def home(request):

    # TODO: use the template location described within settings.py

    logger.info("home", extra=user_extra(request))

    try:
        template = loader.get_template("home/index.html")

        return HttpResponse(template.render(get_user_context(request.user), request), content_type="text/html")
    except Exception:
        logger.exception("home broke", extra=user_extra(request))
