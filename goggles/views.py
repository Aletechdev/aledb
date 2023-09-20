from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse

from common.util import get_user_context

from django.template import loader
from logs.aledb_logger import user_extra
import logging

logger = logging.getLogger(__name__)


def goggles(request):
    logger.info("goggles usage", extra = user_extra(request))

    try:
        context=get_user_context(request.user)
        context.update({'text':'hello'})
        template = loader.get_template("goggles/goggles.html")
        return HttpResponse(template.render(context, request), content_type="text/html")
    except Exception as e:
        logger.exception("goggles broke", extra=user_extra(request))
        template = loader.get_template("500.html")
        context = {'err_message': str(e)}
        return HttpResponse(template.render(context, request), content_type="text/html")
