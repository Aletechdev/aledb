from common.db_util import get_reseq_queryset

from common.constants import REQUEST_ALL

import collections

from filter.mutation_filter import dashboard_filter

from seq.models import ObservedMutation

__author__ = 'dgosting'


def get_ordered_reseq_dict_and_queryset(ale_experiment_list):

    ordered_reseq_dict = _get_ordered_reseq_dict(ale_experiment_list)

    gene_query = ObservedMutation.objects.exclude(mutation__gene='').filter(
        sequencing_experiment__tech_rep__isolate__flask__ale_id__ale_experiment__ale_id__in=ale_experiment_list)

    queryset = dashboard_filter(gene_query, ale_experiment_list=ale_experiment_list)

    return ordered_reseq_dict, queryset


def _get_ordered_reseq_dict(ale_experiment_list):

    queryset = get_reseq_queryset(REQUEST_ALL)

    queryset = queryset.filter(tech_rep__isolate__flask__ale_id__ale_experiment__ale_id__in=ale_experiment_list)

    seq_experiment_ordered_dict = collections.OrderedDict()

    for reseq in queryset:
        seq_experiment_ordered_dict[reseq.id] = reseq

    return seq_experiment_ordered_dict
