from filter.models import AleExperimentFilter

import json

from django.utils.html import strip_tags

from  filter.models import GlobalFilter

__author__ = 'Patrick Phaneuf'

NO_BREAK_STRING_CODE = u'\xa0'

MODEL_TO_FILTER_MAPPINGS = {"protein": "protein_change",
                            "type": "mutation_type",
                            "sequence": "sequence_change",
                            "position": "position",
                            "gene": "gene"}


# TODO: Maybe make filtering part of the database query instead of post processing.
# TODO: Could become an issue for large experiments with many filters
def is_excluded_on_mutation(mutation, filter_settings):
    mutation_dict = dict(mutation.__dict__)

    if filter_settings is not None:

        default_ignored_mutations_json_string = "[]"

        if filter_settings.ignored_mutations != ""\
                and len(filter_settings.ignored_mutations) != len(default_ignored_mutations_json_string):

            mutation_to_exclude_list = json.loads(filter_settings.ignored_mutations.replace("'", '"'))

            for mutation_to_exclude in mutation_to_exclude_list:

                for key in mutation_to_exclude:

                    mutation_data = _get_sanitized_mutation_data(key, mutation_dict)

                    if mutation_to_exclude[key] is not '':
                        try:
                            if mutation_to_exclude[key] not in mutation_data:
                                break
                        except:
                            try:
                                if int(mutation_to_exclude[key]) != int(mutation_data):
                                    break
                            except:
                                continue
                    else:
                        continue
                else:
                    return True

    return False


def _get_sanitized_mutation_data(key, mutation_dict):
    try:
        mutation_data = strip_tags(mutation_dict[MODEL_TO_FILTER_MAPPINGS[key]]).replace(
            NO_BREAK_STRING_CODE, u'').replace(" ", "")
    except:
        mutation_data = mutation_dict[MODEL_TO_FILTER_MAPPINGS[key]]
    return mutation_data


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
    filter_queryset = AleExperimentFilter.objects.filter(ale_experiment_id=ale_experiment_id)

    if len(filter_queryset) == 0:
        filter_settings = AleExperimentFilter()
    else:
        filter_settings = filter_queryset[0]  # Since there's only one filter setting per experiment.

    filter_settings.ignored_mutations = _append_global_ignored_mutations_json(filter_settings.ignored_mutations)

    filter_settings.ignored_genes = _append_global_ignored_genes(filter_settings.ignored_genes)

    return filter_settings


def _append_global_ignored_mutations_json(ignored_mutations):

    global_filter_settings = GlobalFilter.objects.get_or_create(id=1)[0]

    if global_filter_settings.ignored_mutations is ''\
            or global_filter_settings.ignored_mutations == "[]":  # TODO: define what "[]" means in a CONSTANT string up top.
        return ignored_mutations

    ignored_mutations = ignored_mutations.replace("]", "")

    global_ignored_mutations = global_filter_settings.ignored_mutations.replace("[", "")

    if ignored_mutations != "[":
        ignored_mutations += ", "

    ignored_mutations += global_ignored_mutations

    return ignored_mutations


def _append_global_ignored_genes(ignored_genes):

    global_filter_settings = GlobalFilter.objects.get_or_create(id=1)[0]

    if global_filter_settings.ignored_genes == "":
        return ignored_genes

    if ignored_genes == "":
        ignored_genes = global_filter_settings.ignored_genes
    else:
        ignored_genes += ", " + global_filter_settings.ignored_genes

    return ignored_genes
