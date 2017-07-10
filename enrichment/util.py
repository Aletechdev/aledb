from filter.util import get_filter_settings
from common.util import get_reseq_ordered_dict
from seq.util import get_all_observed_mutations
from enrichment import enrichment


__author__ = "Patrick Phaneuf"


def get_enrichment_mutation_list(ale_experiment_id):
    reseq_dict = get_reseq_ordered_dict(ale_experiment_id)
    ale_exp_reseq_obs_mut_qryset_list = []
    for reseq_id in reseq_dict:
        ale_exp_reseq_obs_mut_qryset_list.append(get_all_observed_mutations([reseq_id]))
    enrichment_mutation_list = enrichment.get_enrichment_mutation_list(ale_exp_reseq_obs_mut_qryset_list)
    return enrichment_mutation_list
