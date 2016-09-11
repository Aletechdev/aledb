import collections
from filter.util import get_filter_settings, filter
from common.db_util import get_ordered_reseq_dict, get_ale_exp_reseq_obs_mut_lists
from genes.util import get_gene_list

__author__ = "Patrick Phaneuf"


class Enrichment:
    def __init__(self, reseq_obs_mut_list, filter_settings=None):
        self._reseq_obs_mut_list = reseq_obs_mut_list
        self._filter_settings = filter_settings
        self._mutation_gene_count_dict = self._populate_mutation_gene_count_dict()
        self.enrichment_mutation_list = self._populate_enrichment_mutation_list()

    def _populate_mutation_gene_count_dict(self):
        mutation_gene_count_dict = collections.defaultdict(int)
        for reseq_obs_mut_queryset in self._reseq_obs_mut_list:
            if self._filter_settings is not None:  # TODO: shouldn't have to do this; filter_mutations should handle filter_settings=None gracefully
                reseq_obs_mut_queryset = filter(reseq_obs_mut_queryset, self._filter_settings)
            for observed_mutation in reseq_obs_mut_queryset:
                mutation_gene_list = get_gene_list(observed_mutation.mutation.gene)
                for gene in mutation_gene_list:
                    mutation_gene_count_dict[gene] += 1
        return mutation_gene_count_dict

    def _populate_enrichment_mutation_list(self):
        enrichment_mutation_list = []
        for reseq_obs_mut_queryset in self._reseq_obs_mut_list:
            if self._filter_settings is not None:  # TODO: shouldn't have to do this; filter_mutations should handle filter_settings=None gracefully
                reseq_obs_mut_queryset = filter(reseq_obs_mut_queryset, self._filter_settings)
            for observed_mutation in reseq_obs_mut_queryset:
                mutation_gene_list = get_gene_list(observed_mutation.mutation.gene)
                for gene in mutation_gene_list:
                    if self._mutation_gene_count_dict[gene] > 1 and observed_mutation.mutation not in enrichment_mutation_list:  # This condition will keep intergenic mutations from being added twice since they consider two genes which may both already have a observed_mutation; in the case the intergenic observed_mutation will only be added once.
                        enrichment_mutation_list.append(observed_mutation.mutation)
        return enrichment_mutation_list


def get_enrichment_mutation_list(ale_experiment_id):
    reseq_dict = get_ordered_reseq_dict(ale_experiment_id)
    ale_exp_reseq_obs_mut_lists = get_ale_exp_reseq_obs_mut_lists(reseq_dict)  # Will remove starting strain mutations.
    filter_settings = get_filter_settings(ale_experiment_id)
    enrichment = Enrichment(ale_exp_reseq_obs_mut_lists, filter_settings)
    return enrichment.enrichment_mutation_list
