from seq.views import common

from django.http import HttpResponse

from django.contrib.auth.decorators import login_required

from builder.key_mutations import get_key_mutations


__author__ = 'pphaneuf'


@login_required
def key_mutations(request):

    ale_experiment_ids = common.get_ale_experiment_id(request)

    key_mutations_set = get_key_mutations(ale_experiment_ids)

    seq_experiment_ordered_dict = common.get_experiment_ordered_dict(request)

    seq_experiment_ordered_dict = common.filter_checked_flasks(request, seq_experiment_ordered_dict)

    return HttpResponse(key_mutations_set)