import ale.common

import seq.models

import collections

from filter import mutation_filter


__author__ = "Patrick Phaneuf"


def get_key_mutation_list(ale_experiment_id):

    reseq_dict = _get_reseq_dict(ale_experiment_id)

    ale_experiment_mutation_list = _get_ale_experiment_mutation_list(reseq_dict)

    filter_settings = mutation_filter.get_filter_settings(ale_experiment_id)

    mutation_gene_count_dict = _get_mutation_gene_count_dict(ale_experiment_mutation_list, filter_settings)

    key_mutation_list = _get_key_mutation_list(ale_experiment_mutation_list, filter_settings, mutation_gene_count_dict)

    return key_mutation_list


def _get_mutation_gene_count_dict(ale_experiment_mutation_list, filter_settings):

    mutation_gene_count_dict = collections.defaultdict(int)

    for mutation_list in ale_experiment_mutation_list:

        for mutation in mutation_list:

            if not _is_mutation_excluded(filter_settings, mutation):

                mutation_gene_count_dict[mutation.gene] += 1

    return mutation_gene_count_dict


def _get_key_mutation_list(ale_experiment_mutation_list, filter_settings, mutation_gene_count_dict):

    key_mutation_list = []

    for mutation_list in ale_experiment_mutation_list:

        for mutation in mutation_list:

            if not _is_mutation_excluded(filter_settings, mutation) \
                    and mutation_gene_count_dict[mutation.gene] > 1:

                key_mutation_list.append(mutation)

    return key_mutation_list


def _is_mutation_excluded(filter_settings, mutation):

    filter_mutation = False

    if mutation_filter.is_excluded_on_gene(mutation, filter_settings) \
            or mutation_filter.is_excluded_on_mutation(mutation, filter_settings):

        filter_mutation = True

    return filter_mutation


def _get_ale_experiment_mutation_list(reseq_dict):

    ale_experiment_mutation_list = []

    mutations_to_remove_list = []

    for reseq_id in reseq_dict:

        reseq = reseq_dict[reseq_id]

        if reseq.ale_id == ale.common.STARTING_STRAIN_ALE_ID:

            mutations_to_remove_list = _get_reseq_mutations_list(reseq_id)

        else:

            ale_experiment_mutation_list.append(_get_reseq_mutations_list(reseq_id))

    filtered_ale_experiment_mutation_list = []

    for reseq_mutation_list in ale_experiment_mutation_list:

        filtered_reseq_mutation_list = [mutation for mutation in reseq_mutation_list if mutation not in mutations_to_remove_list]

        filtered_ale_experiment_mutation_list.append(filtered_reseq_mutation_list)

    return filtered_ale_experiment_mutation_list


def _get_reseq_mutations_list(reseq_id):

    mutations_list = []

    observed_mutations_query_set = seq.models.ObservedMutation.objects.filter(sequencing_experiment_id=reseq_id)

    for observed_mutation in observed_mutations_query_set:

        mutations_list.append(observed_mutation.mutation)

    return mutations_list


def _get_reseq_dict(experiment_id):

    ale_experiment_selector = "AND experiment_id = "

    ale_experiment_selector += str(experiment_id)

    ale_number_selector = ""

    sql_query = """SELECT reseq_id AS id FROM id_mapping WHERE reseq_id IS NOT NULL %s %s ORDER BY ale_no, flask_no, isolate_no ASC;""" % (ale_experiment_selector, ale_number_selector)

    reseq_raw_query_set = seq.models.ResequencingExperiment.objects.raw(sql_query)

    reseq_dict = collections.OrderedDict((reseq.id, reseq) for reseq in reseq_raw_query_set)

    return reseq_dict
