from django.http import HttpResponse

from django.contrib.auth.decorators import login_required


__author__ = 'Patrick Phaneuf'


@login_required
def fixation(request):
    return HttpResponse()
