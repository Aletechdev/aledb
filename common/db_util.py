# TODO: Had to implement this separate from common.util since can't currently run unit tests on modules that refer to models. Fix this

import collections

from seq.views.common import REQUEST_ALE_EXPERIMENT_ID, REQUEST_ALE_ID

from common.util import get_ale_experiment_selector, get_ale_number_selector

from seq.models import ResequencingExperiment

from ale.common import STARTING_STRAIN_ALE_ID

__author__ = 'Patrick Phaneuf'


def get_reseq_queryset(request):

    ale_id = request.GET.get(REQUEST_ALE_ID)

    ale_experiment_id = request.GET.get(REQUEST_ALE_EXPERIMENT_ID)

    return _get_reseq_queryset(ale_experiment_id, ale_id)


def _get_starting_string_mutation_queryset(request):

    ale_id = STARTING_STRAIN_ALE_ID

    ale_experiment_id = request.GET.get(REQUEST_ALE_EXPERIMENT_ID)

    return _get_reseq_queryset(ale_experiment_id, ale_id)


def _get_reseq_queryset(ale_experiment_id, ale_id):

    reseq_query = ResequencingExperiment.objects.all().order_by('tech_rep__isolate__flask__ale_id__ale_id',
                                                                'tech_rep__isolate__flask__flask_number',
                                                                'tech_rep__isolate__isolate_number')

    reseq_query = get_ale_experiment_selector(ale_experiment_id, reseq_query)

    reseq_query = get_ale_number_selector(ale_id, reseq_query)

    return reseq_query


def get_ordered_reseq_dict(request, include_starting_strain=False):
    seq_experiment_ordered_dict = collections.OrderedDict()
    if include_starting_strain:
        starting_strain_raw_queryset = _get_starting_string_mutation_queryset(request)
        for seq_experiment in starting_strain_raw_queryset:
            seq_experiment_ordered_dict[seq_experiment.id] = seq_experiment
    seq_experiments_raw_queryset = get_reseq_queryset(request)
    for seq_experiment in seq_experiments_raw_queryset:
        seq_experiment_ordered_dict[seq_experiment.id] = seq_experiment

    return seq_experiment_ordered_dict


def get_reseq_query_set_from_ale_experiment_id(ale_experiment_id):
    ale_id = STARTING_STRAIN_ALE_ID

    return _get_reseq_queryset(ale_experiment_id, ale_id)
