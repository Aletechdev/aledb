from django.shortcuts import render

from common.util import common_context


def bibliome(request):

    # TODO: use the template location described within settings.py

    return render(request, "bibliome/index.html", common_context, content_type="text/html")
