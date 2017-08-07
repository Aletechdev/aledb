import collections
from filter.util import filter_observed_mutations
from genes.util import get_gene_list

__author__ = "Patrick Phaneuf"


def get_enrichment_mutation_list(reseq_obs_mut_queryset_list):
    mutation_gene_count_dict = _populate_mutation_gene_count_dict(reseq_obs_mut_queryset_list)
    return _populate_enrichment_mutation_list(reseq_obs_mut_queryset_list, mutation_gene_count_dict)


def _populate_mutation_gene_count_dict(reseq_obs_mut_queryset_list):
    mutation_gene_count_dict = collections.defaultdict(int)
    for reseq_obs_mut_queryset in reseq_obs_mut_queryset_list:
        reseq_obs_mut_queryset = filter_observed_mutations(reseq_obs_mut_queryset)
        for observed_mutation in reseq_obs_mut_queryset:
            mutation_gene_list = get_gene_list(observed_mutation.mutation.gene)
            for gene in mutation_gene_list:
                mutation_gene_count_dict[gene] += 1
    return mutation_gene_count_dict


def _populate_enrichment_mutation_list(reseq_obs_mut_queryset_list,
                                       mutation_gene_count_dict):
    enrichment_mutation_list = []
    for reseq_obs_mut_queryset in reseq_obs_mut_queryset_list:
        reseq_obs_mut_queryset = filter_observed_mutations(reseq_obs_mut_queryset)
        for observed_mutation in reseq_obs_mut_queryset:
            mutation_gene_list = get_gene_list(observed_mutation.mutation.gene)
            for gene in mutation_gene_list:
                # This condition will keep intergenic mutations from being added twice since
                # they consider two genes which may both already have a observed_mutation;
                # in the case the intergenic observed_mutation will only be added once.
                if mutation_gene_count_dict[
                    gene] > 1 and observed_mutation.mutation not in enrichment_mutation_list:
                    enrichment_mutation_list.append(observed_mutation.mutation)
    return enrichment_mutation_list
