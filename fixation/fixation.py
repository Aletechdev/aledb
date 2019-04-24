from seq.util import get_all_observed_mutations, get_mutations_from_observed_muations
from filter.util import filter_observed_mutations

__author__ = "Patrick Phaneuf"


# Currently, assumes that ordered_reseq_dict represents multiple ALEs, such as with an ALE experiment.
# Could reduce to only act on an ALE, since this is the smallest context Fixation operates within.
def get_ale_exp_fixed_mut_dict(ale_reseq_ordered_dict):
    # groups all reseq into their ALEs
    ale_id_reseq_dict = _get_ale_id_reseq_dict(ale_reseq_ordered_dict)
    # For each ALE (working only with the reseq's of a particular ALE.
    ale_fixed_mut_dict_list = []
    for id_reseq_list in ale_id_reseq_dict.values():
        flask_isolate_obs_mut_dict = _get_flask_isolate_obs_mut_dict(id_reseq_list)
        flask_obs_mut_dict = _get_flask_obs_mut_dict(flask_isolate_obs_mut_dict)
        ale_fixed_mut_dict_list.append(_get_ale_fixed_mut_dict(flask_obs_mut_dict))

    ale_exp_fixed_mut_dict = {}
    for ale_fixed_mut_dict in ale_fixed_mut_dict_list:
        for ale_fixed_mut in ale_fixed_mut_dict.keys():
            if ale_fixed_mut in ale_exp_fixed_mut_dict.keys():
                ale_exp_fixed_mut_dict[ale_fixed_mut].append(ale_fixed_mut_dict[ale_fixed_mut])
            else:
                ale_exp_fixed_mut_dict[ale_fixed_mut] = [ale_fixed_mut_dict[ale_fixed_mut]]

    return ale_exp_fixed_mut_dict


def _get_ale_fixed_mut_dict(flask_obs_mut_dict):
    """
    From flask_obs_mut_dict, extract all fixed mutations
    :param flask_obs_mut_dict:  dict with key = flast_number, and vale = obs_mut_queryset for given flask
    :return: dict with key = fixed_mut, value = list of obs_mut_ids,  and mut_dict (key = mut_id, value = mutation)
    """
    ordered_flask_number_list = sorted(flask_obs_mut_dict.keys())
    if len(flask_obs_mut_dict.keys()) > 1:
        obs_mutations = []
        last_flask_number = ordered_flask_number_list[-1]
        second_last_flask_number = ordered_flask_number_list[-2]

        for flask_number in ordered_flask_number_list:
            flask_obs_mut_queryset = flask_obs_mut_dict[flask_number]
            flask_obs_muts = filter_observed_mutations(flask_obs_mut_queryset)
            obs_mutations += flask_obs_muts
            if flask_number == last_flask_number:
                last_flask_mut_dict = {obs_mut.mutation.id: obs_mut.mutation for obs_mut in flask_obs_muts}
            elif flask_number == second_last_flask_number:
                second_last_flask_mut_dict = {obs_mut.mutation.id: obs_mut.mutation for obs_mut in flask_obs_muts}

        fixed_mut_ids = []
        if len(last_flask_mut_dict) > 0 and len(second_last_flask_mut_dict) > 0:
            fixed_mut_ids = {mut_id for mut_id in last_flask_mut_dict.keys()} & {mut_id for mut_id in
                                                                             second_last_flask_mut_dict.keys()}
        if len(fixed_mut_ids) > 0:
            # associate observed mutation ids with fixed mutation ids
            fixed_mut_obs_mut_list_dict = {mut: [] for mut in last_flask_mut_dict.values() if mut.id in fixed_mut_ids}
            for obs_mut in obs_mutations:
                if obs_mut.mutation.id in fixed_mut_ids:
                    fixed_mut_obs_mut_list_dict[obs_mut.mutation].append(obs_mut.id)
            return fixed_mut_obs_mut_list_dict
    return dict()


def _get_flask_isolate_obs_mut_dict(id_reseq_list):
    """
    Handles situation where you can have more than one isolate from a flask.
    :param id_reseq_list: list of tuples (reseq_id, reseq)
    :return: dict with key = tuple(flask_number, isolate_nume), value = obs_mut_queryset
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
    """
    comment by R. Cai:
    map ale_id to one or multiple reseq.  Since ale_id in ale_aleId is not unique, this method should only be used for
    reseq from single experiment
    :param reseq_dict:
    :return: dict with key = ale_id, value = list of tuple (reseq_id, reseq)
    """
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


def _has_descending_mut_freq(obs_mut_queryset):

    observed_mutation_list = _filter_mutations_from_same_flask(list(obs_mut_queryset))
    observed_mutation_list.sort(key=lambda x: x.sequencing_experiment.flask_number)
    current_observed_mutation_frequency = 0
    for observed_mutation in observed_mutation_list:
        if observed_mutation.frequency >= current_observed_mutation_frequency:
            current_observed_mutation_frequency = observed_mutation.frequency
        else:
            return True
    return False


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
