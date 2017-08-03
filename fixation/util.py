from common.util import get_reseq_ordered_dict
from fixation import fixation
from fixation.models import FixatedMutation
from seq.models import ObservedMutation
import ast


__author__ = "Patrick Phaneuf"


def get_fixed_mut_dict(ale_experiment_id):
    ale_reseq_ordered_dict = get_reseq_ordered_dict(ale_experiment_id)
    ale_exp_fixed_mut_dict = fixation.get_ale_exp_fixed_mut_dict(ale_reseq_ordered_dict)
    return ale_exp_fixed_mut_dict


def get_exp_fixed_obs_mut_qryset(exp_id, reseq_ordered_dict):

    fixed_mut_qryset = FixatedMutation.objects.filter(ale_experiment_id=exp_id)
    fixed_obs_mut_qryset = ObservedMutation.objects.none()
    # TODO: filter out mutations from samples that were removed from table.

    # TODO: the below can likely be optimized using the django ORM.
    for fixed_mut in fixed_mut_qryset:
        fixed_obs_mut_qryset_list = _get_fixed_obs_mut_qryset_list(fixed_mut, reseq_ordered_dict.keys())
        # Could have more than 1 fixing sequence
        for fixed_obs_mut_qryset in fixed_obs_mut_qryset_list:
            fixed_obs_mut_qryset = fixed_obs_mut_qryset | fixed_obs_mut_qryset

    return fixed_obs_mut_qryset


# def _get_fixating_observed_mutation_queryset(fixating_mutation_queryset, reseq_id_list):
#     fixating_mutation_id_list = [fixating_mutation.mutation.id for fixating_mutation in fixating_mutation_queryset]
#     all_observed_mutation_queryset = ObservedMutation.objects.filter(sequencing_experiment_id__in=reseq_id_list)
#     fixating_observed_mutation_queryset = all_observed_mutation_queryset.filter(mutation_id__in=fixating_mutation_id_list)
#     return fixating_observed_mutation_queryset
def _get_fixed_obs_mut_qryset_list(fixating_mutation, reseq_id_list):
    all_observed_mutation_queryset = ObservedMutation.objects.filter(sequencing_experiment_id__in=reseq_id_list)
    fixed_obs_mut_lists = list(ast.literal_eval(fixating_mutation.fixed_observed_mutation_series))
    obs_mut_queryset_list = []
    for fixed_obs_mut_list in fixed_obs_mut_lists:
        obs_mut_queryset = all_observed_mutation_queryset.filter(id__in=fixed_obs_mut_list)
        obs_mut_queryset_list.append(obs_mut_queryset)

    return obs_mut_queryset_list