import collections

from filter.mutation_filter import dashboard_filter

from seq.models import ObservedMutation, ResequencingExperiment

__author__ = 'dgosting'


def get_ordered_reseq_dict_and_queryset(ale_experiment_list):

    observed_mutation_queryset = ObservedMutation.objects.exclude(mutation__gene='').filter(
        sequencing_experiment__tech_rep__isolate__flask__ale_id__ale_experiment__ale_id__in=ale_experiment_list)

    filtered_queryset = dashboard_filter(observed_mutation_queryset, ale_experiment_list=ale_experiment_list)

    ordered_reseq_dict = _get_ordered_reseq_dict(filtered_queryset)

    return ordered_reseq_dict, filtered_queryset


def _get_ordered_reseq_dict(filtered_queryset):

    reseq_exp_id_set = set([observed_mutation.sequencing_experiment_id for observed_mutation in filtered_queryset])

    queryset = ResequencingExperiment.objects.filter(id__in=reseq_exp_id_set)

    seq_experiment_ordered_dict = collections.OrderedDict()

    for reseq in queryset:
        seq_experiment_ordered_dict[reseq.id] = reseq

    return seq_experiment_ordered_dict
