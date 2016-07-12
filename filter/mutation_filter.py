from filter.models import Filter

import json


__author__ = 'Patrick Phaneuf'


NO_BREAK_STRING_CODE = u'\xa0'


def is_excluded_on_mutation(mutation, filter_settings):

    is_mutation_excluded = False

    if filter_settings is not None:

        default_ignored_mutations_json_string = "[{}]"

        if filter_settings.ignored_mutations != "" and len(filter_settings.ignored_mutations) != len(default_ignored_mutations_json_string):

            filter_mutation_list = json.loads(filter_settings.ignored_mutations)

            for filter_mutation in filter_mutation_list:

                if mutation.position == filter_mutation["position"] \
                        and _normalize_sequence_change_string(mutation.sequence_change) == _normalize_sequence_change_string(filter_mutation["sequence"]) \
                        and mutation.mutation_type == filter_mutation["type"]:

                    is_mutation_excluded = True
                    break

    return is_mutation_excluded


def _normalize_sequence_change_string(sequence_change_string):

    return sequence_change_string.replace(NO_BREAK_STRING_CODE, u' ')


def is_excluded_on_gene(mutation, filter_settings):

    is_mutation_excluded = False

    if filter_settings is not None:

        excluded_gene_list = filter_settings.ignored_genes.replace(" ", "").split(',')

        if mutation.gene in excluded_gene_list:
            is_mutation_excluded = True

    return is_mutation_excluded


def is_excluded_on_freq(observed_mutation, filter_settings):

    is_mutation_excluded = True

    # Creating up defaults.
    if filter_settings is not None:
        minimum_mutation_frequency = float(filter_settings.min_cutoff) / 100
        maximum_mutation_frequency = float(filter_settings.max_cutoff) / 100
    else:
        minimum_mutation_frequency = 0.0
        maximum_mutation_frequency = 1.0

    if minimum_mutation_frequency <= observed_mutation.frequency <= maximum_mutation_frequency:
        is_mutation_excluded = False

    return is_mutation_excluded


def get_filter_settings(ale_experiment_id):

    filter_queryset = Filter.objects.filter(ale_experiment_id=ale_experiment_id)

    filter_settings = None

    if len(filter_queryset) != 0:
        filter_settings = filter_queryset[0]  # Since there's only one filter setting per experiment.

    return filter_settings
