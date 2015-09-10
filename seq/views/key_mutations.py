from seq.views import common

from django.http import HttpResponse

from django.contrib.auth.decorators import login_required

from seq_db.key_mutations import get_key_mutations


__author__ = 'pphaneuf'


@login_required
def key_mutations(request):

    ale_experiment_ids = common.get_ale_experiment_id(request)

    key_mutations = get_key_mutations(ale_experiment_ids)

    return HttpResponse(key_mutations)
