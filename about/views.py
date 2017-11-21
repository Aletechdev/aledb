from django.http import HttpResponse

from common.util import get_all_ale_exps, get_recent_ale_exps

from django.template import loader


def about(request):

    # TODO: use the template location described within settings.py
    template = loader.get_template("about/index.html")

    context = {"experiments": get_all_ale_exps(),
               "recent_experiments": get_recent_ale_exps()}

    return HttpResponse(template.render(context, request), content_type="text/html")
