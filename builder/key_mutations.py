# from ale.models import AleExperiment

from seq.models import ResequencingExperiment

from seq.models import ObservedMutation

# from seq.models import Mutation

import collections


__author__ = 'pphaneuf'

STARTING_STRAIN_ALE_ID = 0


def _get_common_mutation_set(seq_experiment_dict):

    mutation_set_list = []

    for seq_experiment_id in seq_experiment_dict:

        mutations_set = set()

        seq_experiment = seq_experiment_dict[seq_experiment_id]

        if seq_experiment.ale_id != STARTING_STRAIN_ALE_ID:

            mutations_set.update(_get_seq_experiment_mutations_set(seq_experiment_id))

            mutation_set_list.append(mutations_set)

    common_mutation_set = mutation_set_list[0]

    for mutation_set in mutation_set_list:

        common_mutation_set = common_mutation_set & mutation_set

    return common_mutation_set


def _get_starting_strain_mutation_set(seq_experiment_dict):

    starting_strain_mutation_set = set()

    for seq_experiment_id in seq_experiment_dict:

        seq_experiment = seq_experiment_dict[seq_experiment_id]

        if seq_experiment.ale_id == STARTING_STRAIN_ALE_ID:

            starting_strain_mutation_set.update(_get_seq_experiment_mutations_set(seq_experiment_id))

            break;  # Only 1 starting strain, therefore don't need to parse remaining experiments.

    return starting_strain_mutation_set



def get_key_mutations(ale_experiment_id):

    seq_experiment_dict = _get_seq_experiment_dict(ale_experiment_id)

    common_mutation_set = _get_common_mutation_set(seq_experiment_dict)

    starting_strain_mutation_set = _get_starting_strain_mutation_set(seq_experiment_dict)

    common_mutation_set_no_starting_strain = common_mutation_set - starting_strain_mutation_set

    return common_mutation_set_no_starting_strain


def _get_seq_experiment_dict(experiment_id):

    ale_experiment_selector = "AND experiment_id = "

    ale_experiment_selector += str(experiment_id)

    ale_number_selector = ""

    sql_query = """SELECT reseq_id AS id FROM id_mapping WHERE reseq_id IS NOT NULL %s %s ORDER BY ale_no, flask_no, isolate_no ASC;""" % (ale_experiment_selector, ale_number_selector)

    seq_experiments_raw_query_set = ResequencingExperiment.objects.raw(sql_query)

    seq_experiment_dict = collections.OrderedDict((seq_experiment.id, seq_experiment) for seq_experiment in seq_experiments_raw_query_set)

    return seq_experiment_dict


def _get_seq_experiment_mutations_set(seq_experiment_id):

    mutations_set = set()

    observed_mutations = ObservedMutation.objects.filter(sequencing_experiment_id=seq_experiment_id)

    for observed_mutation in observed_mutations:
        mutations_set.add(observed_mutation.mutation)

    return mutations_set