# from ale.models import AleExperiment

from seq.models import ResequencingExperiment

from seq.models import ObservedMutation

# from seq.models import Mutation

import collections


__author__ = 'pphaneuf'

STARTING_STRAIN_ALE_ID = 0


def get_key_mutations(experiment_id):

    seq_experiment_dict = _get_seq_experiment_dict(experiment_id)

    starting_strain_mutations_set = _get_starting_strain_mutations(seq_experiment_dict)

    all_mutations_set = _get_all_mutations(seq_experiment_dict)

    unique_mutations_set = all_mutations_set - starting_strain_mutations_set

    return unique_mutations_set


def _get_seq_experiment_dict(experiment_id):

    ale_experiment_selector = "AND experiment_id = "

    ale_experiment_selector += str(experiment_id)

    ale_number_selector = ""

    sql_query = """SELECT reseq_id AS id FROM id_mapping WHERE reseq_id IS NOT NULL %s %s ORDER BY ale_no, flask_no, isolate_no ASC;""" % (ale_experiment_selector, ale_number_selector)

    seq_experiments_raw_query_set = ResequencingExperiment.objects.raw(sql_query)

    seq_experiment_dict = collections.OrderedDict((seq_experiment.id, seq_experiment) for seq_experiment in seq_experiments_raw_query_set)

    return seq_experiment_dict


def _get_seq_experiment_mutation(seq_experiment_id):

    mutations_set = set()

    observed_mutations = ObservedMutation.objects.filter(sequencing_experiment_id=seq_experiment_id)

    for observed_mutation in observed_mutations:
        mutations_set.add(observed_mutation.mutation)

    return mutations_set


def _get_mutations(seq_experiment_dict, get_starting_strain_mutations=False):

    mutations_set = set()

    for seq_experiment_id in seq_experiment_dict:

        seq_experiment = seq_experiment_dict[seq_experiment_id]

        if get_starting_strain_mutations:

            if seq_experiment.ale_id == STARTING_STRAIN_ALE_ID:

                mutations_set.update(_get_seq_experiment_mutation(seq_experiment_id))

                break   # Only 1 starting strain, therefore don't need parse remaining experiments.

        else:

            if seq_experiment.ale_id != STARTING_STRAIN_ALE_ID:

                mutations_set.update(_get_seq_experiment_mutation(seq_experiment_id))

    return mutations_set


def _get_starting_strain_mutations(seq_experiment_dict):

    return _get_mutations(seq_experiment_dict, get_starting_strain_mutations=True)


def _get_all_mutations(seq_experiment_dict):

    return _get_mutations(seq_experiment_dict, get_starting_strain_mutations=False)
