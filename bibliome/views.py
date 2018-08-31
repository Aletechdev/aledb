from django.shortcuts import render

from common.util import common_context
from logs.aledb_logger import get_logger,user_extra

exception = get_logger("exceptions")
usage = get_logger("usage")

def bibliome(request):

    # TODO: use the template location described within settings.py

    return render(request, "bibliome/index.html", common_context, content_type="text/html")
