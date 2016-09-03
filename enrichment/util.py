import collections
from filter.mutation_filter import get_filter_settings, clean_ignored_mutation_id_list
from common.db_util import get_ordered_reseq_dict, get_ale_exp_reseq_mutation_lists
from filter.models import GlobalFilter
from genes.util import get_gene_list
from genes.util import get_clean_gene_list

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

                gene_list = get_gene_list(mutation.gene)
                clean_gene_list = get_clean_gene_list(gene_list)

                for gene in clean_gene_list:
                    mutation_gene_count_dict[gene] += 1

    return mutation_gene_count_dict


def _get_enrichment_mutation_list(ale_experiment_reseq_mutation_lists,
                                  ignored_mutation_id_list,
                                  mutation_gene_count_dict):

    enrichment_mutation_list = []
    for reseq_mutation_list in ale_experiment_reseq_mutation_lists:
        for mutation in reseq_mutation_list:
            if mutation.id not in ignored_mutation_id_list:

                gene_list = get_gene_list(mutation.gene)
                clean_gene_list = get_clean_gene_list(gene_list)

                for gene in clean_gene_list:
                    if mutation_gene_count_dict[gene] > 1 \
                            and mutation not in enrichment_mutation_list:   # This condition will keep intergenic mutations from being added twice since they consider two genes which may both already have a mutation; in the case the intergenic mutation will only be added once.
                        enrichment_mutation_list.append(mutation)

    return enrichment_mutation_list


def _get_ignored_mutation_id_list(filter_settings):

    global_ignored_mutation_ids = clean_ignored_mutation_id_list(GlobalFilter.objects.get(id=1).ignored_mutations)

    experiment_ignored_mutation_ids = clean_ignored_mutation_id_list(filter_settings.ignored_mutations)

    return global_ignored_mutation_ids + experiment_ignored_mutation_ids
