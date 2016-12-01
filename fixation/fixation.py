from common.db_util import get_mutation_queryset_from_obs_mut_queryset
import seq.models
from seq.util import get_all_observed_mutations
from filter.util import filter_observed_mutations

__author__ = "Patrick Phaneuf"


# Currently, assumes that ordered_reseq_dict represents multiple ALEs, such as with an ALE experiment.
# Could reduce to only act on an ALE, since this is the smallest context Fixation operates within.
def get_ale_exp_fixated_mutation_list(ale_reseq_ordered_dict, filter_settings=None):
    # groups all reseq into their ALEs
    ale_id_reseq_dict = _get_ale_id_reseq_dict(ale_reseq_ordered_dict)
    ale_experiment_fixated_mutation_queryset = seq.models.Mutation.objects.none()
    # For each ALE (working only with the reseq's of a particular ALE.
    for id_reseq_list in ale_id_reseq_dict.values():
        flask_isolate_obs_mut_dict = _get_flask_isolate_obs_mut_dict(id_reseq_list)
        flask_obs_mut_dict = _get_flask_obs_mut_dict(flask_isolate_obs_mut_dict)
        ale_fixated_mutation_queryset = _get_ale_fixated_mutation_queryset(flask_obs_mut_dict, filter_settings)
        ale_experiment_fixated_mutation_queryset = ale_experiment_fixated_mutation_queryset | ale_fixated_mutation_queryset

    return list(ale_experiment_fixated_mutation_queryset)


def _get_ale_fixated_mutation_queryset(flask_obs_mut_dict, filter_settings):
    """
    Will convert obs mutation into mutation.
    :param flask_obs_mut_dict:
    :return:
    """
    # TODO: should do filtering out of mutations somewhere in here.
    ordered_flask_number_list = sorted(flask_obs_mut_dict.keys())
    fixated_mutation_queryset = seq.models.Mutation.objects.none()
    if len(flask_obs_mut_dict.keys()) > 1:
        first_flask_number = ordered_flask_number_list[0]
        last_flask_number = ordered_flask_number_list[-1]

        first_flask_obs_mut_queryset = flask_obs_mut_dict[first_flask_number]
        first_flask_obs_mut_queryset = filter_observed_mutations(first_flask_obs_mut_queryset, filter_settings)
        fixated_mutation_queryset = get_mutation_queryset_from_obs_mut_queryset(first_flask_obs_mut_queryset)

        for flask_number in ordered_flask_number_list:
            flask_obs_mut_queryset = flask_obs_mut_dict[flask_number]
            flask_obs_mut_queryset = filter_observed_mutations(flask_obs_mut_queryset, filter_settings)
            flask_mutation_queryset = get_mutation_queryset_from_obs_mut_queryset(flask_obs_mut_queryset)
            if flask_number == last_flask_number:
                fixated_mutation_queryset = _get_common_mutations(fixated_mutation_queryset,
                                                                  flask_mutation_queryset)
            else:
                fixated_mutation_queryset = _get_new_and_fixated_mutation_queryset(fixated_mutation_queryset,
                                                                                   flask_mutation_queryset)
    return fixated_mutation_queryset


def _get_new_and_fixated_mutation_queryset(fixated_mutation_queryset, flask_mutation_queryset):
    new_mutation_queryset = _get_combined_mutations(fixated_mutation_queryset, flask_mutation_queryset)
    new_mutation_queryset = _get_common_mutations(new_mutation_queryset, flask_mutation_queryset)
    return new_mutation_queryset


def _get_common_mutations(fixated_mutation_queryset, flask_mutation_queryset):
    return fixated_mutation_queryset & flask_mutation_queryset


def _get_combined_mutations(fixated_mutation_queryset, flask_mutation_queryset):
    return fixated_mutation_queryset | flask_mutation_queryset


def _get_flask_isolate_obs_mut_dict(id_reseq_list):
    """
    Handles situation where you can have more than one isolate from a flask.
    :param id_reseq_list:
    :return:
    """
    flask_isolate_mutation_dict = {}
    for id_reseq_tuple in id_reseq_list:
        reseq_id = id_reseq_tuple[0]
        flask_number = id_reseq_tuple[1].flask_number
        isolate_number = id_reseq_tuple[1].tech_rep.isolate.isolate_number
        observed_mutation_queryset = get_all_observed_mutations([reseq_id])
        flask_isolate_mutation_dict[(flask_number, isolate_number)] = observed_mutation_queryset
    return flask_isolate_mutation_dict


def _get_ale_id_reseq_dict(reseq_dict):
    ale_reseq_dict = {}
    for reseq_id, reseq in reseq_dict.items():
        if reseq.ale_id in ale_reseq_dict.keys():
            ale_reseq_dict[reseq.ale_id].append((reseq_id, reseq))
        else:
            ale_reseq_dict[reseq.ale_id] = [(reseq_id, reseq)]
    return ale_reseq_dict


def _get_flask_obs_mut_dict(flask_isolate_obs_mut_dict):
    """
    Combines all of the isolate mutations of one flask into a single queryset representing the mutations of the flask.
    Args:
        flask_isolate_obs_mut_dict:

    Returns: flask_obs_mut_dict
    """
    flask_obs_mut_dict = {}
    for flask_isolate_id, obs_mut_queryset in flask_isolate_obs_mut_dict.items():
        flask_id = flask_isolate_id[0]
        if flask_id not in flask_obs_mut_dict.keys():
            flask_obs_mut_dict[flask_id] = obs_mut_queryset
        else:
            flask_obs_mut_dict[flask_id] = flask_obs_mut_dict[flask_id] | obs_mut_queryset
    return flask_obs_mut_dict


def filter_for_ascending_freq(fixating_observed_mutation_queryset):

    fixated_obs_mut_freq_dict = {}
    for observed_mutation in fixating_observed_mutation_queryset:
        mutation_id = observed_mutation.mutation.id
        if mutation_id in fixated_obs_mut_freq_dict.keys():
            fixated_obs_mut_freq_dict[mutation_id].append(observed_mutation)
        else:
            fixated_obs_mut_freq_dict[mutation_id] = [observed_mutation]

    mutation_id_exclude_list = _get_descending_freq_mutation_id_list(fixated_obs_mut_freq_dict)

    fixating_observed_mutation_queryset = fixating_observed_mutation_queryset.exclude(mutation_id__in=mutation_id_exclude_list)

    return fixating_observed_mutation_queryset


# TODO: this can be unit tested.
def _get_descending_freq_mutation_id_list(fixated_obs_mut_freq_dict):
    mutation_id_exclude_list = []

    for mutation_id, observed_mutation_list in fixated_obs_mut_freq_dict.items():

        observed_mutation_list = _filter_mutations_from_same_flask(observed_mutation_list)

        observed_mutation_list.sort(key=lambda x: x.sequencing_experiment.flask_number)

        current_observed_mutation_frequency = 0
        for observed_mutation in observed_mutation_list:
            if observed_mutation.frequency >= current_observed_mutation_frequency:
                current_observed_mutation_frequency = observed_mutation.frequency
            else:
                mutation_id_exclude_list.append(mutation_id)
                break

    return mutation_id_exclude_list


# TODO: this can be unit tested.
def _filter_mutations_from_same_flask(observed_mutation_list):

    filtered_observed_mutation_list = []

    same_flask_observed_mutation_dict = {}
    for observed_mutation_idx in range(len(observed_mutation_list)):
        flask_number = observed_mutation_list[observed_mutation_idx].sequencing_experiment.flask_number
        if flask_number in same_flask_observed_mutation_dict.keys():
            same_flask_observed_mutation_dict[flask_number].append(observed_mutation_idx)
        else:
            same_flask_observed_mutation_dict[flask_number] = [observed_mutation_idx]

    for observed_mutation_idx_list in same_flask_observed_mutation_dict.values():

        if len(observed_mutation_idx_list) == 1:
            observed_mutation_idx = observed_mutation_idx_list[0]
            filtered_observed_mutation_list.append(observed_mutation_list[observed_mutation_idx])
        else:
            max_freq_idx = observed_mutation_idx_list[0]  # Default
            max_freq = 0
            for observed_mutation_idx in observed_mutation_idx_list:
                current_freq = observed_mutation_list[observed_mutation_idx].frequency
                if current_freq > max_freq:
                    max_freq = current_freq
                    max_freq_idx = observed_mutation_idx
            filtered_observed_mutation_list.append(observed_mutation_list[max_freq_idx])

    return filtered_observed_mutation_list
