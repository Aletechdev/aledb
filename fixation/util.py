from seq.util import get_reseq_ordered_dict
from fixation import fixation
from fixation.models import FixatedMutation
from seq.models import ObservedMutation
import ast


__author__ = "Patrick Phaneuf"


def get_fixed_mut_dict(ale_experiment_id):
    ale_reseq_ordered_dict = get_reseq_ordered_dict(ale_experiment_id)
    ale_exp_fixed_mut_dict = fixation.get_ale_exp_fixed_mut_dict(ale_reseq_ordered_dict)
    return ale_exp_fixed_mut_dict


def get_fixed_obs_mut_qryset(experiment_id):
    fixed_mut_qryset = FixatedMutation.objects.filter(ale_experiment_id=experiment_id)
    fixed_obs_mut_qryset = ObservedMutation.objects.none()
    # TODO: filter out mutations from samples that were removed from table.
    for fixed_mut in fixed_mut_qryset:
        fixed_obs_mut_id_2d_list = list(ast.literal_eval(fixed_mut.fixed_observed_mutation_series))
        # Just need to get all observed mutations; don't care their about their grouping.
        fixed_obs_mut_id_list = [item for sublist in fixed_obs_mut_id_2d_list for item in sublist]
        fixed_obs_mut_qryset = fixed_obs_mut_qryset | ObservedMutation.objects.filter(id__in=fixed_obs_mut_id_list)
    return fixed_obs_mut_qryset
