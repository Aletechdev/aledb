from seq.models import ObservedMutation

from django.core.cache import cache

from genes.util import get_gene_list

from itertools import groupby


def get_all_observed_mutations(reseq_id_list):
    return ObservedMutation.objects.filter(sequencing_experiment_id__in=reseq_id_list)

