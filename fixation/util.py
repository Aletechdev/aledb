from common.util import get_reseq_ordered_dict
from filter.util import get_filter_settings
from fixation import fixation


__author__ = "Patrick Phaneuf"


def get_fixed_mut_dict(ale_experiment_id):
    ale_reseq_ordered_dict = get_reseq_ordered_dict(ale_experiment_id)
    ale_exp_fixed_mut_dict = fixation.get_ale_exp_fixed_mut_dict(ale_reseq_ordered_dict)
    return ale_exp_fixed_mut_dict