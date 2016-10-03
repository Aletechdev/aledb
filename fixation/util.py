from common.db_util import get_reseq_ordered_dict
from filter.util import get_filter_settings
from fixation import fixation


__author__ = "Patrick Phaneuf"


def get_fixated_mutation_list(ale_experiment_id):
    filter_settings = get_filter_settings(ale_experiment_id)
    ordered_reseq_dict = get_reseq_ordered_dict(ale_experiment_id)  # Want to include WT so as to get mutations to remove.
    fixating_mutation_list = fixation.get_ale_exp_fixated_mutation_list(ordered_reseq_dict, filter_settings)
    return fixating_mutation_list