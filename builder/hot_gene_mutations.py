import ale.common
import seq.models
import collections
from filter import mutation_filter
from common.db_util import get_reseq_dict

__author__ = "Patrick Phaneuf"


def get_hot_gene_mutation_list(ale_experiment_id):
    reseq_dict = get_reseq_dict(ale_experiment_id)
    ale_experiment_reseq_mutation_lists = _get_ale_experiment_reseq_mutation_lists(reseq_dict)
    filter_settings = mutation_filter.get_filter_settings(ale_experiment_id)
    mutation_gene_count_dict = _get_mutation_gene_count_dict(ale_experiment_reseq_mutation_lists, filter_settings)
    hot_gene_mutation_list = _get_hot_gene_mutation_list(ale_experiment_reseq_mutation_lists, filter_settings, mutation_gene_count_dict)
    return hot_gene_mutation_list


# Expects the mutation lists from each reseq.
def _get_mutation_gene_count_dict(ale_experiment_mutation_list, filter_settings):

    mutation_gene_count_dict = collections.defaultdict(int)

    for mutation_list in ale_experiment_mutation_list:

        for mutation in mutation_list:

            if not _is_mutation_excluded(filter_settings, mutation):

                mutation_gene_count_dict[mutation.gene] += 1

    return mutation_gene_count_dict


def _get_hot_gene_mutation_list(ale_experiment_reseq_mutation_lists, filter_settings, mutation_gene_count_dict):

    hot_gene_mutation_list = []

    for reseq_mutation_list in ale_experiment_reseq_mutation_lists:

        for mutation in reseq_mutation_list:

            if not _is_mutation_excluded(filter_settings, mutation)\
                    and mutation_gene_count_dict[mutation.gene] > 1\
                    and mutation not in hot_gene_mutation_list:

                hot_gene_mutation_list.append(mutation)

    return hot_gene_mutation_list


def _is_mutation_excluded(filter_settings, mutation):

    filter_mutation = False

    if mutation_filter.is_excluded_on_gene(mutation, filter_settings) \
            or mutation_filter.is_excluded_on_mutation(mutation, filter_settings):

        filter_mutation = True

    return filter_mutation


def _get_ale_experiment_reseq_mutation_lists(reseq_dict):

    ale_experiment_mutation_list = []

    mutations_to_exclude_list = []

    for reseq_id in reseq_dict:

        reseq = reseq_dict[reseq_id]

        if reseq.ale_id == ale.common.STARTING_STRAIN_ALE_ID:

            mutations_to_exclude_list = _get_reseq_mutations_list(reseq_id)

        else:

            ale_experiment_mutation_list.append(_get_reseq_mutations_list(reseq_id))

    filtered_ale_experiment_mutation_list = []

    for reseq_mutation_list in ale_experiment_mutation_list:

        filtered_reseq_mutation_list = [mutation for mutation in reseq_mutation_list if mutation not in mutations_to_exclude_list]

        filtered_ale_experiment_mutation_list.append(filtered_reseq_mutation_list)

    return filtered_ale_experiment_mutation_list


def _get_reseq_mutations_list(reseq_id):
    mutations_list = []
    observed_mutations_query_set = seq.models.ObservedMutation.objects.filter(sequencing_experiment_id=reseq_id)
    for observed_mutation in observed_mutations_query_set:
        mutations_list.append(observed_mutation.mutation)
    return mutations_list
