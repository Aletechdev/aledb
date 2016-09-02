import collections
from filter.mutation_filter import get_filter_settings, clean_ignored_mutation_id_list
from common.db_util import get_ordered_reseq_dict, get_ale_exp_reseq_mutation_lists
from filter.models import GlobalFilter

INTERGENIC_SPLIT_CHAR = '/'

__author__ = "Patrick Phaneuf"


def get_enrichment_mutation_list(ale_experiment_id):
    reseq_dict = get_ordered_reseq_dict(ale_experiment_id)
    ale_exp_reseq_mutation_lists = get_ale_exp_reseq_mutation_lists(reseq_dict)  # Will remove starting strain mutations.
    filter_settings = get_filter_settings(ale_experiment_id)  #TODO: may not matter since the experiment isn't yet established on the website.
    ignored_mutation_id_list = _get_ignored_mutation_id_list(filter_settings)
    mutation_gene_count_dict = _get_mutation_gene_count_dict(ale_exp_reseq_mutation_lists, ignored_mutation_id_list)
    enrichment_mutation_list = _get_enrichment_mutation_list(ale_exp_reseq_mutation_lists, ignored_mutation_id_list, mutation_gene_count_dict)
    return enrichment_mutation_list


# Expects the mutation lists from each reseq.
def _get_mutation_gene_count_dict(ale_experiment_mutation_list, ignored_mutation_id_list):

    mutation_gene_count_dict = collections.defaultdict(int)

    for mutation_list in ale_experiment_mutation_list:

        for mutation in mutation_list:

            if mutation.id not in ignored_mutation_id_list:

                if INTERGENIC_SPLIT_CHAR in mutation.gene:
                    _process_intergenic_mutation_gene_count(mutation.gene, mutation_gene_count_dict)
                else:
                    mutation_gene_count_dict[mutation.gene] += 1

    return mutation_gene_count_dict


# TODO: this can be unit tested.
def _process_intergenic_mutation_gene_count(mutation_gene_str, mutation_gene_count_dict):
    flanking_gene_list = mutation_gene_str.split(INTERGENIC_SPLIT_CHAR)
    for flanking_gene in flanking_gene_list:
        mutation_gene_count_dict[flanking_gene] += 1


def _get_enrichment_mutation_list(ale_experiment_reseq_mutation_lists,
                                  ignored_mutation_id_list,
                                  mutation_gene_count_dict):

    enrichment_mutation_list = []

    for reseq_mutation_list in ale_experiment_reseq_mutation_lists:

        for mutation in reseq_mutation_list:

            if mutation.id not in ignored_mutation_id_list\
                    and mutation_gene_count_dict[mutation.gene] > 1\
                    and mutation not in enrichment_mutation_list:

                enrichment_mutation_list.append(mutation)

    return enrichment_mutation_list


def _get_ignored_mutation_id_list(filter_settings):

    global_ignored_mutation_ids = clean_ignored_mutation_id_list(GlobalFilter.objects.get(id=1).ignored_mutations)

    experiment_ignored_mutation_ids = clean_ignored_mutation_id_list(filter_settings.ignored_mutations)

    return global_ignored_mutation_ids + experiment_ignored_mutation_ids
