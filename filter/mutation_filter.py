from filter.models import Filter

import json

from django.utils.html import strip_tags


__author__ = 'Patrick Phaneuf'


NO_BREAK_STRING_CODE = u'\xa0'

MODEL_TO_FILTER_MAPPINGS = {"protein": "protein_change", "type": "mutation_type", "sequence": "sequence_change", "position": "position", "gene": "gene"}


# TODO: Maybe make filtering part of the database query instead of post processing.
# TODO: Could become an issue for large experiments with many filters
def is_excluded_on_mutation(mutation, filter_settings):

    mutation_dict = dict(mutation.__dict__)

    if filter_settings is not None:

        default_ignored_mutations_json_string = "[]"

        if filter_settings.ignored_mutations != "" and len(filter_settings.ignored_mutations) != len(default_ignored_mutations_json_string):

            filter_mutation_list = json.loads(filter_settings.ignored_mutations.replace("'", '"'))

            for filter_mutation in filter_mutation_list:

                for key in filter_mutation:

                    try:
                        mutation_data = strip_tags(mutation_dict[MODEL_TO_FILTER_MAPPINGS[key]]).replace(NO_BREAK_STRING_CODE, u'').replace(" ", "")
                    except:
                        mutation_data = mutation_dict[MODEL_TO_FILTER_MAPPINGS[key]]

                    if filter_mutation[key] is not '':
                        try:
                            if filter_mutation[key] not in mutation_data:
                                break
                        except:
                            try:
                                if int(filter_mutation[key]) != int(mutation_data):
                                    break
                            except:
                                continue
                    else:
                        return False
                else:
                    return True

    return False


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

    if len(filter_queryset) == 0:
        filter_settings = Filter()
    else:
        filter_settings = filter_queryset[0]  # Since there's only one filter setting per experiment.

    return filter_settings
