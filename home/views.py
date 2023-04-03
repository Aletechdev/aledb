from django.http import HttpResponse

from common.util import get_user_context

from django.template import loader
from logs.aledb_logger import user_extra
import logging

from ale.models import AleExperiment


logger = logging.getLogger(__name__)


def get_unique_publication_count():
    return AleExperiment.objects.order_by().values('doi').distinct().count

def home(request):

    # TODO: use the template location described within settings.py

    logger.info("home", extra=user_extra(request))
    context = get_user_context(request.user)
    context.update({"unique_publication_count": get_unique_publication_count})
    try:
        template = loader.get_template("home/index.html")

        return HttpResponse(template.render(context, request), content_type="text/html")
    except Exception:
        logger.exception("home broke", extra=user_extra(request))
