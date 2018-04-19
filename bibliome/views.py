from django.shortcuts import render

from common.util import get_all_ale_exps, get_recent_ale_exps


def bibliome(request):

    # TODO: use the template location described within settings.py

    context = {"experiments": get_all_ale_exps(),
               "recent_experiments": get_recent_ale_exps()}

    return render(request, "bibliome/index.html", context, content_type="text/html")
