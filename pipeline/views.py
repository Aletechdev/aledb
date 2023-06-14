# Create your views here.
from django.http import HttpResponse

from common.util import get_user_context

from django.template import loader
from logs.aledb_logger import user_extra
from pipeline.util import get_shared_directories
import json
import logging


logger = logging.getLogger(__name__)


def pipeline(request):

    # TODO: use the template location described within settings.py

    logger.info("pipeline", extra=user_extra(request))
    context = get_user_context(request.user)

    shared_directories_list = json.loads(get_shared_directories())
    context.update({"shared_drives": shared_directories_list})

    if request.method == "POST":
        context.update({"reponse_text":request.POST})
        try:
            template = loader.get_template("pipeline/pipeline.html")

            return HttpResponse(template.render(context, request), content_type="text/html")
        except Exception:
            logger.exception("pipeline broke", extra=user_extra(request))
    try:
        template = loader.get_template("pipeline/pipeline.html")

        return HttpResponse(template.render(get_user_context(request.user), request), content_type="text/html")
    except Exception:
        logger.exception("pipeline broke", extra=user_extra(request))