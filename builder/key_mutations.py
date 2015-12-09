import ale.common

import seq.models

import collections


__author__ = "Patrick Phaneuf"


def get_key_mutation_list_single_experiment(ale_experiment_id):

    seq_experiment_dict = _get_seq_experiment_dict(ale_experiment_id)

    experiment_mutation_list = _get_experiment_mutation_list(seq_experiment_dict)

    mutation_gene_count_dict = collections.defaultdict(int)

    for ale_mutation_list in experiment_mutation_list:

        for mutation in ale_mutation_list:

            mutation_gene_count_dict[mutation.gene] += 1

    key_mutation_list = []

    for ale_mutation_list in experiment_mutation_list:

        for mutation in ale_mutation_list:

            if mutation_gene_count_dict[mutation.gene] > 1:

                key_mutation_list.append(mutation)

    return key_mutation_list


def _get_experiment_mutation_list(seq_experiment_dict):

    mutation_list = []

    for seq_experiment_id in seq_experiment_dict:

        seq_experiment = seq_experiment_dict[seq_experiment_id]

        if seq_experiment.ale_id != ale.common.STARTING_STRAIN_ALE_ID:

            mutation_list.append(_get_seq_experiment_mutations_list(seq_experiment_id))

    return mutation_list


def _get_seq_experiment_mutations_list(seq_experiment_id):

    mutations_list = []

    observed_mutations_query_set = seq.models.ObservedMutation.objects.filter(sequencing_experiment_id=seq_experiment_id)

    for observed_mutation in observed_mutations_query_set:

        mutations_list.append(observed_mutation.mutation)

    return mutations_list


def _get_seq_experiment_dict(experiment_id):

    ale_experiment_selector = "AND experiment_id = "

    ale_experiment_selector += str(experiment_id)

    ale_number_selector = ""

    sql_query = """SELECT reseq_id AS id FROM id_mapping WHERE reseq_id IS NOT NULL %s %s ORDER BY ale_no, flask_no, isolate_no ASC;""" % (ale_experiment_selector, ale_number_selector)

    seq_experiments_raw_query_set = seq.models.ResequencingExperiment.objects.raw(sql_query)

    seq_experiment_dict = collections.OrderedDict((seq_experiment.id, seq_experiment) for seq_experiment in seq_experiments_raw_query_set)

    return seq_experiment_dict
