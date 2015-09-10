from django.http import HttpResponse

from django.contrib.auth.decorators import login_required


__author__ = 'pphaneuf'


@login_required
def key_mutations(request):

    return HttpResponse("output")