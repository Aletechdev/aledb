from common.db_util import get_reseq_ordered_dict
from filter.util import get_filter_settings


__author__ = "Patrick Phaneuf"

# TODO: https://github.com/SBRG/ale_analytics/issues/291

def get_fixated_mutation_list(ale_experiment_id):
    filter_settings = get_filter_settings(ale_experiment_id)
    ordered_reseq_dict = get_reseq_ordered_dict(ale_experiment_id)  # Want to include WT so as to get mutations to remove.
    fixation = Fixation(ordered_reseq_dict, filter_settings)
    return fixation.fixating_mutation_list