from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse
from ale.permissions import can_view_experiment
from common.util import get_user_context
from django.template import loader
from logs.aledb_logger import user_extra
import logging

logger = logging.getLogger(__name__)


def evidence(request, *args, **kwargs):
    request_details = str(request)

    logger.info("evidence request " + request_details, extra=user_extra(request))

    evidence_location = '/data' + request.GET.get('location') #kwargs['evidence_location']
    evidence_html = open(evidence_location, 'r')
    template = loader.get_template("evidence/evidence.html")
    context = get_user_context(request.user)
    context.update({'evidence_html': evidence_html.read()})

    return HttpResponse(template.render(context, request))
