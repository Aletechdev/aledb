from common.db_util import get_reseq_query_set_from_ale_experiment_id

__author__ = "Patrick Phaneuf"


def get_fixated_mutation_list(ale_experiment_id):
    reseq_dict = get_reseq_query_set_from_ale_experiment_id(ale_experiment_id)