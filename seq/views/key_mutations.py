from seq.views import common

from django.http import HttpResponse

from django.contrib.auth.decorators import login_required




__author__ = 'pphaneuf'


@login_required
def key_mutations(request):

    ale_experiment_ids = common.get_ale_experiment_id(request)

    return HttpResponse(ale_experiment_ids)