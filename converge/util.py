from seq.util import get_all_observed_mutations, get_reseq_ordered_dict
from seq.models import ObservedMutation
from converge.models import ConvergeMutation
from converge import converge
from django.db.models import Q



__author__ = "Patrick Phaneuf"


# TODO optimize by only using ORM for finding converge mutations.
def get_converge_mutation_list(ale_experiment_id):
    reseq_dict = get_reseq_ordered_dict(ale_experiment_id)
    ale_exp_reseq_obs_mut_qryset_list = []
    for reseq_id in reseq_dict:
        ale_exp_reseq_obs_mut_qryset_list.append(get_all_observed_mutations([reseq_id]))
    converge_mutation_list = converge.get_converge_mutation_list(ale_exp_reseq_obs_mut_qryset_list)
    return converge_mutation_list


# TODO optimize by only using ORM for the below query.
# def get_converge_obs_mut_qryset(reseq_dict):
#     exp_id = reseq_dict[next(iter(reseq_dict))].ale_experiment.ale_id
#     obs_mut_qryset = ObservedMutation.objects.filter(sequencing_experiment_id__in=reseq_dict.keys())
#     converge_mut_qryset = ConvergeMutation.objects.filter(ale_experiment_id=exp_id)
#     converge_mut_id_list = []
#     for converge_mut in converge_mut_qryset:
#         converge_mut_id_list.append(converge_mut.mutation_id)
#     converge_mut_obs_mut_qryset = obs_mut_qryset.filter(mutation_id__in=converge_mut_id_list)
#     return converge_mut_obs_mut_qryset


def get_converge_obs_mut_qryset(experiment_id):
    converge_mut_qryset = ConvergeMutation.objects.filter(ale_experiment_id=experiment_id)
    q_query = Q(mutation__id__in=converge_mut_qryset.values('mutation_id'))
    q_query.add(Q(sequencing_experiment__tech_rep__isolate__flask__ale_id__ale_experiment__ale_id=experiment_id), Q.AND)
    return ObservedMutation.objects.filter(q_query)
