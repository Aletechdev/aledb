import collections
from filter.util import filter_observed_mutations
from genes.util import get_gene_list

__author__ = "Patrick Phaneuf"


def get_converge_mutation_list(reseq_obs_mut_queryset_list):
    mut_gene_ale_count_dict = _get_mut_gene_ale_dict(reseq_obs_mut_queryset_list)
    return _get_converge_mut_list(reseq_obs_mut_queryset_list, mut_gene_ale_count_dict)


def _get_mut_gene_ale_dict(reseq_obs_mut_queryset_list):
    mut_gene_ale_dict = collections.defaultdict(set)
    for reseq_obs_mut_qryset in reseq_obs_mut_queryset_list:
        obs_mutations = filter_observed_mutations(reseq_obs_mut_qryset)
        for obs_mut in obs_mutations:
            mut_gene_list = get_gene_list(obs_mut.mutation.gene)
            for gene in mut_gene_list:
                mut_gene_ale_dict[gene].add(obs_mut.sequencing_experiment.ale_id)
    return mut_gene_ale_dict


def _get_converge_mut_list(reseq_obs_mut_queryset_list,
                           mutation_gene_ale_dict):
    converge_mut_list = []
    for reseq_obs_mut_queryset in reseq_obs_mut_queryset_list:
        reseq_obs_mutions = filter_observed_mutations(reseq_obs_mut_queryset)
        for observed_mutation in reseq_obs_mutions:
            mutation_gene_list = get_gene_list(observed_mutation.mutation.gene)
            for gene in mutation_gene_list:
                # This condition will keep intergenic mutations from being added twice since
                # they consider two genes which may both already have an observed_mutation;
                # with this condition, the intergenic observed_mutation will only be added once.
                if len(mutation_gene_ale_dict[gene]) > 1 and observed_mutation.mutation not in converge_mut_list:
                    converge_mut_list.append(observed_mutation.mutation)
    return converge_mut_list
