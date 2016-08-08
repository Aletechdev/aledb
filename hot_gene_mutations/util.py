import collections
from filter import mutation_filter
from common.db_util import get_ordered_reseq_dict, get_ale_experiment_reseq_mutation_lists

__author__ = "Patrick Phaneuf"


def get_hot_gene_mutation_list(ale_experiment_id):
    reseq_dict = get_ordered_reseq_dict(ale_experiment_id)
    ale_experiment_reseq_mutation_lists = get_ale_experiment_reseq_mutation_lists(reseq_dict)
    filter_settings = mutation_filter.get_filter_settings(ale_experiment_id)  #TODO: may not matter since the experiment isn't yet establised on the website.
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
