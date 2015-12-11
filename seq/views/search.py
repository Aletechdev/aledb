from django.http import HttpResponse

from django.template import loader

from django.views.generic import View


class SearchView(View):

    def get(self, request, *args, **kwargs):

        template = loader.get_template("search.html")

        return HttpResponse(template.render())
