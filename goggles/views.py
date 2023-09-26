import json

from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse

from common.util import get_user_context

from django.template import loader
from logs.aledb_logger import user_extra
import logging

import random

logger = logging.getLogger(__name__)

ALE_MACHINES = [['ACTIVE', 'PROJECTS'],
                ['ALE 3.0', 'UCSD'],
                ['ALE 3.0', 'DTU']]


def generate_projects():
    from string import ascii_lowercase as alc
    projects = ["queue"]
    alc = [0,1,2]
    for i in alc:
        projects.append(f"PROJECT-{i}")
    return projects


def generate_ales():
    from string import ascii_uppercase as auc
    ales = []
    for i in auc:
        chars = '0123456789ABCDEF'
        ale = [f"ALE-{i}", [f"ale-{i}", '#'+''.join(random.sample(chars,6))]]
        ales.append(ale)
    return ales


def goggles(request):
    logger.info("goggles usage", extra=user_extra(request))

    try:
        context = get_user_context(request.user)
        context.update(
            {'text': 'hello', 'machines': ALE_MACHINES, 'projects': generate_projects(), 'ales': generate_ales()})
        template = loader.get_template("goggles/goggles.html")
        return HttpResponse(template.render(context, request), content_type="text/html")
    except Exception as e:
        logger.exception("goggles broke", extra=user_extra(request))
        template = loader.get_template("500.html")
        context = {'err_message': str(e)}
        return HttpResponse(template.render(context, request), content_type="text/html")
