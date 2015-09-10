from seq.views import common

from django.http import HttpResponse

from django.contrib.auth.decorators import login_required

from seq_db.key_mutations import get_key_mutations


__author__ = 'pphaneuf'

HTML_MUTATION_TABLE_HEADER = """<tr><td>Mutation</td><td>Gene</td><td>Protein change</td>"""


@login_required
def key_mutations(request):

    ale_experiment_ids = common.get_ale_experiment_id(request)

    key_mutations_set = get_key_mutations(ale_experiment_ids)

    seq_experiment_ordered_dict = common.get_experiment_ordered_dict(request)

    table_header = _get_table_header(seq_experiment_ordered_dict)

    return HttpResponse(key_mutations_set)


def _get_table_header(seq_experiment_dict):

    table_header = HTML_MUTATION_TABLE_HEADER

    experiment_urls = common.get_experiment_urls(seq_experiment_dict)

    for seq_experiment_id in seq_experiment_dict:

        seq_experiment = seq_experiment_dict[seq_experiment_id]

        sample_name = _get_sample_name(seq_experiment)