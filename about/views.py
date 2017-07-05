from django.http import HttpResponse

from common.util import get_all_ale_experiments, get_recent_experiments

from django.template import loader


def about(request):

    # TODO: use the template location described within settings.py
    template = loader.get_template("about/index.html")

    context = {"experiments": get_all_ale_experiments(),
               "recent_experiments": get_recent_experiments()}

    return HttpResponse(template.render(context))
