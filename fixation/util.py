from common.db_util import get_ordered_reseq_dict, get_all_observed_mutations, get_mutation_queryset_from_observed_mutation_queryset
import seq.models

__author__ = "Patrick Phaneuf"


def get_fixated_mutation_list(ale_experiment_id):
    ordered_reseq_dict = get_ordered_reseq_dict(ale_experiment_id)  # Want to include WT so as to get mutations to remove.
    fixating_mutation_queryset = get_ale_experiment_fixated_mutation_queryset(ordered_reseq_dict)
    return list(fixating_mutation_queryset)


def get_ale_experiment_fixated_mutation_queryset(ordered_reseq_dict):

    ale_id_reseq_dict = _get_ale_id_reseq_dict(ordered_reseq_dict)

    ale_experiment_fixated_mutation_queryset = seq.models.Mutation.objects.none()

    for id_reseq_list in ale_id_reseq_dict.values():

        flask_isolate_mutation_dict = {}
        for id_reseq_tuple in id_reseq_list:
            reseq_id = id_reseq_tuple[0]
            flask_number = id_reseq_tuple[1].flask_number
            isolate_number = id_reseq_tuple[1].isolate.isolate_number

            observed_mutation_queryset = get_all_observed_mutations([reseq_id])
            mutation_queryset = get_mutation_queryset_from_observed_mutation_queryset(observed_mutation_queryset)
            flask_isolate_mutation_dict[(flask_number, isolate_number)] = mutation_queryset

        flask_mutation_dict = _get_flask_mutation_dict(flask_isolate_mutation_dict)

        ale_fixated_mutation_queryset = _get_ale_fixated_mutation_queryset(flask_mutation_dict)
        ale_experiment_fixated_mutation_queryset = ale_experiment_fixated_mutation_queryset | ale_fixated_mutation_queryset

    return ale_experiment_fixated_mutation_queryset



def _get_flask_mutation_dict(flask_isolate_mutation_dict):
    """
    Combines all of the isolate mutations of one flask into a single queryset representing the mutations of the flask.
    Args:
        flask_isolate_mutation_dict:

    Returns: flask_mutation_dict
    """

    flask_mutation_dict = {}

    for flask_isolate_id, mutation_queryset in flask_isolate_mutation_dict.items():

        flask_id = flask_isolate_id[0]
        if flask_id not in flask_mutation_dict.keys():
            flask_mutation_dict[flask_id] = mutation_queryset
        else:
            flask_mutation_dict[flask_id] = flask_mutation_dict[flask_id] | mutation_queryset

    return flask_mutation_dict


def _get_ale_id_reseq_dict(reseq_dict):
    ale_reseq_dict = {}
    for reseq_id, reseq in reseq_dict.items():
        if reseq.ale_id in ale_reseq_dict.keys():
            ale_reseq_dict[reseq.ale_id].append((reseq_id, reseq))
        else:
            ale_reseq_dict[reseq.ale_id] = [(reseq_id, reseq)]
    return ale_reseq_dict



def _get_ale_fixated_mutation_queryset(flask_mutation_dict):

    ordered_flask_number_list = sorted(flask_mutation_dict.keys())

    first_flask_number = ordered_flask_number_list[0]
    last_flask_number = ordered_flask_number_list[-1]

    fixated_mutation_queryset = flask_mutation_dict[first_flask_number]

    for flask_number in ordered_flask_number_list:

        flask_mutation_queryset = flask_mutation_dict[flask_number]

        if flask_number == last_flask_number:
            fixated_mutation_queryset = _get_common_mutations(fixated_mutation_queryset, flask_mutation_queryset)
        else:
            fixated_mutation_queryset = _get_new_and_fixated_mutation_queryset(fixated_mutation_queryset, flask_mutation_queryset)

    return fixated_mutation_queryset


def _get_new_and_fixated_mutation_queryset(fixated_mutation_queryset, flask_mutation_queryset):
    new_mutation_queryset = _get_combined_mutations(fixated_mutation_queryset, flask_mutation_queryset)
    new_mutation_queryset = _get_common_mutations(new_mutation_queryset, flask_mutation_queryset)
    return new_mutation_queryset


def _get_common_mutations(fixated_mutation_queryset, flask_mutation_queryset):
    return fixated_mutation_queryset & flask_mutation_queryset


def _get_combined_mutations(fixated_mutation_queryset, flask_mutation_queryset):
    return fixated_mutation_queryset | flask_mutation_queryset
