# TODO: Had to implement this separate from common.util since can't currently run unit tests on modules that refer to models. Fix this

from common.constants import RESEQ_QUERY
from seq.models import ResequencingExperiment
from common.util import get_ale_experiment_selector
from common.util import get_ale_number_selector
import collections
import ale.common
import seq.models

__author__ = 'Patrick Phaneuf'


def get_reseq_queryset(ale_experiment_id, ale_id):
    ale_experiment_selector = get_ale_experiment_selector(ale_experiment_id)
    ale_id_selector = get_ale_number_selector(ale_id)
    sql_query = RESEQ_QUERY % (ale_experiment_selector, ale_id_selector)
    reseq_raw_queryset = ResequencingExperiment.objects.raw(sql_query)
    return reseq_raw_queryset


def get_ordered_reseq_dict(ale_experiment_id):
    """
    Args:
        ale_experiment_id:

    Returns:
        reseq_dict: a ordered dictionary of reseq values and their ID's as keys.
        The reseq values within the dictionary will be ordered according to that
        defined within RESEQ_QUERY

    """
    reseq_queryset = get_reseq_queryset(ale_experiment_id, None)
    reseq_dict = collections.OrderedDict((reseq.id, reseq) for reseq in reseq_queryset)
    return reseq_dict


def get_ale_experiment_reseq_mutation_lists(reseq_dict):
    ale_experiment_mutation_list = []
    mutations_to_exclude_list = []

    for reseq_id in reseq_dict:
        reseq = reseq_dict[reseq_id]
        if reseq.ale_id == ale.common.STARTING_STRAIN_ALE_ID:
            mutations_to_exclude_list = get_reseq_mutations_list(reseq_id)
        else:
            ale_experiment_mutation_list.append(get_reseq_mutations_list(reseq_id))

    filtered_ale_experiment_mutation_list = []
    for reseq_mutation_list in ale_experiment_mutation_list:
        filtered_reseq_mutation_list = [mutation for mutation in reseq_mutation_list if mutation not in mutations_to_exclude_list]
        filtered_ale_experiment_mutation_list.append(filtered_reseq_mutation_list)

    return filtered_ale_experiment_mutation_list


def get_reseq_mutations_list(reseq_id):
    mutations_list = []
    observed_mutations_query_set = seq.models.ObservedMutation.objects.filter(sequencing_experiment_id=reseq_id)
    for observed_mutation in observed_mutations_query_set:
        mutations_list.append(observed_mutation.mutation)
    return mutations_list
