import collections
from filter.util import get_filtered_observed_mutations_queryset
from seq.models import ObservedMutation, ResequencingExperiment
from ale.models import AleExperiment


__author__ = 'dgosting, pphaneuf'


def get_ordered_reseq_dict_and_obs_mut_queryset(ale_experiment_list, ale_no=None):
    raw_obs_mut_qryset = ObservedMutation.objects.exclude(mutation__gene='').filter(
        sequencing_experiment__tech_rep__isolate__flask__ale_id__ale_experiment__ale_id__in=ale_experiment_list)
    obs_mut_qryset = get_filtered_observed_mutations_queryset(raw_obs_mut_qryset)
    if ale_no:
        obs_mut_qryset = obs_mut_qryset.filter(sequencing_experiment__tech_rep__isolate__flask__ale_id__ale_id=ale_no)
    ordered_reseq_dict = _get_ordered_reseq_dict(obs_mut_qryset)
    return ordered_reseq_dict, obs_mut_qryset


def _get_ordered_reseq_dict(filtered_queryset):
    reseq_exp_id_set = set([observed_mutation.sequencing_experiment_id for observed_mutation in filtered_queryset])
    queryset = ResequencingExperiment.objects.filter(id__in=reseq_exp_id_set)
    seq_experiment_ordered_dict = collections.OrderedDict()
    for reseq in queryset:
        seq_experiment_ordered_dict[reseq.id] = reseq
    return seq_experiment_ordered_dict


def get_ales_from_ale_experiment_list(ale_experiment_list):
    experiment_queryset = []
    for ale_id in ale_experiment_list:
        experiment = AleExperiment.objects.get(ale_id=ale_id)
        experiment_queryset += experiment.aleid_set.only("ale_id")
    experiment_queryset = set([exp.ale_id for exp in experiment_queryset])
    return experiment_queryset
