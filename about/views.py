from django.http import HttpResponse

from django.template import loader


def about(request):

    # TODO: use the template location described within settings.py
    template = loader.get_template("about/index.html")

    context = {}

    return HttpResponse(template.render(context))
