from seq.util import get_all_observed_mutations, get_reseq_ordered_dict
from seq.models import ObservedMutation
from enrichment import enrichment
from enrichment.models import EnrichmentMutation


__author__ = "Patrick Phaneuf"


# TODO optimize by only using ORM for finding enrichment mutations.
def get_enrichment_mutation_list(ale_experiment_id):
    reseq_dict = get_reseq_ordered_dict(ale_experiment_id)
    ale_exp_reseq_obs_mut_qryset_list = []
    for reseq_id in reseq_dict:
        ale_exp_reseq_obs_mut_qryset_list.append(get_all_observed_mutations([reseq_id]))
    enrichment_mutation_list = enrichment.get_enrichment_mutation_list(ale_exp_reseq_obs_mut_qryset_list)
    return enrichment_mutation_list


# TODO optimize by only using ORM for the below query.
def get_enrich_obs_mut_qryset(reseq_dict):
    exp_id = reseq_dict[next(iter(reseq_dict))].ale_experiment.ale_id
    obs_mut_qryset = ObservedMutation.objects.filter(sequencing_experiment_id__in=reseq_dict.keys())
    enrich_mut_qryset = EnrichmentMutation.objects.filter(ale_experiment_id=exp_id)
    enrich_mut_id_list = []
    for enrich_mut in enrich_mut_qryset:
        enrich_mut_id_list.append(enrich_mut.mutation_id)
    enrich_mut_obs_mut_qryset = obs_mut_qryset.filter(mutation_id__in=enrich_mut_id_list)
    return enrich_mut_obs_mut_qryset