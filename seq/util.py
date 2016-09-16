from seq.models import ObservedMutation

from django.core.cache import cache

from genes.util import get_gene_list

from itertools import groupby


def get_all_observed_mutations(reseq_id_list):
    return ObservedMutation.objects.filter(sequencing_experiment_id__in=reseq_id_list)


def get_gene_bar_chart_dict(observed_mutation_queryset):

    cached_bar_chart_gene_dict = cache.get('bar_chart_gene_dict')

    if cached_bar_chart_gene_dict is None:

        gene_list = [gene['mutation__gene'] for gene in observed_mutation_queryset.values('mutation__gene').distinct()]

        gene_set = [get_gene_list(gene_str) for gene_str in gene_list if gene_str is not None]

        flattened_list = sorted([item for sublist in gene_set for item in sublist])

        set_gene_list = set(flattened_list)

        counted_list = [len(list(group)) for key, group in groupby(flattened_list)]

        sorted_gene_dict = []

        print(counted_list)

        # for idx, val in enumerate(counted_list):
        #
        #     sorted_gene_dict.append({set_gene_list[idx]: val})

        print(sorted_gene_dict)

        cache.set('bar_chart_gene_dict', sorted_gene_dict, None)

        return sorted_gene_dict

    return cached_bar_chart_gene_dict
