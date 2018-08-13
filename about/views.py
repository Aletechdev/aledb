from django.http import HttpResponse

from common.util import common_context

from django.template import loader


def about(request):

    # TODO: use the template location described within settings.py
    template = loader.get_template("about/index.html")

    return HttpResponse(template.render(common_context, request), content_type="text/html")
