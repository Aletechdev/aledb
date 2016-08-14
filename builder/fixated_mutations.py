from common.db_util import get_reseq_dict

__author__ = "Patrick Phaneuf"


def get_fixated_mutation_list(ale_experiment_id):
    reseq_dict = get_reseq_dict(ale_experiment_id)