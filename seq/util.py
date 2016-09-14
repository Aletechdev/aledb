from seq.models import ObservedMutation


def get_all_observed_mutations(reseq_id_list):
    return ObservedMutation.objects.filter(sequencing_experiment_id__in=reseq_id_list)