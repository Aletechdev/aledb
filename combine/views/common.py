import collections
from filter.util import get_filtered_observed_mutations_queryset
from seq.models import ObservedMutation, ResequencingExperiment
from ale.models import AleExperiment
from filter.models import AleExperimentFilter


__author__ = 'dgosting, pphaneuf'


def get_ordered_reseq_dict_and_obs_mut_queryset(ale_experiment_id_list, ale_no=None):
    raw_obs_mut_qryset = ObservedMutation.objects.exclude(
        mutation__gene=''
    ).filter(
        sequencing_experiment__tech_rep__isolate__flask__ale_id__ale_experiment__ale_id__in=ale_experiment_id_list
    ).select_related(
        'sequencing_experiment__tech_rep__isolate__flask__ale_id__ale_experiment',
        'mutation'
    )
    obs_mut_qryset = get_filtered_observed_mutations_queryset(raw_obs_mut_qryset)
    if ale_no:
        obs_mut_qryset = obs_mut_qryset.filter(sequencing_experiment__tech_rep__isolate__flask__ale_id__ale_id=ale_no)
    ordered_reseq_dict = _get_ordered_reseq_dict(obs_mut_qryset)
    return ordered_reseq_dict, obs_mut_qryset


def get_exp_ordered_reseq_dict_and_obs_mut_queryset(exp_id):
    raw_obs_mut_qryset = ObservedMutation.objects.exclude(
        mutation__gene=''
    ).filter(
        sequencing_experiment__tech_rep__isolate__flask__ale_id__ale_experiment__ale_id=exp_id
    )
    exp_filter = AleExperimentFilter.objects.filter(ale_experiment__ale_id=exp_id).first()
    obs_mut_qryset = get_filtered_observed_mutations_queryset(raw_obs_mut_qryset, exp_filter).select_related(
        'sequencing_experiment__tech_rep__isolate__flask__ale_id__ale_experiment',
        'mutation'
    )
    ordered_reseq_dict = _get_ordered_reseq_dict(obs_mut_qryset)
    return ordered_reseq_dict, obs_mut_qryset


def _get_ordered_reseq_dict(filtered_obs_mut_queryset):
    seq_experiment_ordered_dict = collections.OrderedDict()
    for observed_mutation in filtered_obs_mut_queryset:
        seq_experiment_ordered_dict[observed_mutation.sequencing_experiment.id] = observed_mutation.sequencing_experiment
    return seq_experiment_ordered_dict


def get_ales_from_ale_experiment_list(ale_experiment_list):
    experiment_queryset = []
    for ale_id in ale_experiment_list:
        experiment = AleExperiment.objects.get(ale_id=ale_id)
        experiment_queryset += experiment.aleid_set.only("ale_id")
    experiment_queryset = set([exp.ale_id for exp in experiment_queryset])
    return experiment_queryset
