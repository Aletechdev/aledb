import collections
from genes.util import get_gene_list

__author__ = "Patrick Phaneuf"


# TODO: also ignore genes from global filter.
class Enrichment:
    def __init__(self, reseq_mutation_list, ignored_mutation_id_list=None):
        self._reseq_mutation_list = reseq_mutation_list
        self._ignored_mutation_id_list = ignored_mutation_id_list

        self._mutation_gene_count_dict = self._populate_mutation_gene_count_dict()
        self.enrichment_mutation_list = self._populate_enrichment_mutation_list()

    # Expects the mutation lists from each reseq.
    def _populate_mutation_gene_count_dict(self):

        mutation_gene_count_dict = collections.defaultdict(int)

        for mutation_list in self._reseq_mutation_list:

            for mutation in mutation_list:

                if mutation.id not in self._ignored_mutation_id_list:

                    mutation_gene_list = get_gene_list(mutation.gene)

                    for gene in mutation_gene_list:
                        mutation_gene_count_dict[gene] += 1

        return mutation_gene_count_dict

    def _populate_enrichment_mutation_list(self):

        enrichment_mutation_list = []
        for reseq_mutation_list in self._reseq_mutation_list:
            for mutation in reseq_mutation_list:
                if mutation.id not in self._ignored_mutation_id_list:

                    gene_list = get_gene_list(mutation.gene)

                    for gene in gene_list:
                        if self._mutation_gene_count_dict[gene] > 1 \
                                and mutation not in enrichment_mutation_list:  # This condition will keep intergenic mutations from being added twice since they consider two genes which may both already have a mutation; in the case the intergenic mutation will only be added once.
                            enrichment_mutation_list.append(mutation)

        return enrichment_mutation_list
