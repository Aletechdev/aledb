# TODO: Had to implement this separate from common.util since can't currently run unit tests on modules that refer to models. Fix this

import collections
import ale.common
from common.util import get_ale_experiment_selector, get_ale_number_selector
from seq.models import ResequencingExperiment
from seq.models import ObservedMutation
from seq.models import Mutation
from ale.models import AleExperiment, RecentExperiments
from django.core.exceptions import ObjectDoesNotExist

__author__ = 'Patrick Phaneuf, Denny Gosting'


def get_reseq_queryset(ale_experiment_id, ale_id=None):
    reseq_queryset = ResequencingExperiment.objects.all().order_by(
        'tech_rep__isolate__flask__ale_id__ale_experiment__name',
        'tech_rep__isolate__flask__ale_id__ale_id',
        'tech_rep__isolate__flask__flask_number',
        'tech_rep__isolate__isolate_number')

    reseq_queryset = get_ale_experiment_selector(ale_experiment_id, reseq_queryset)

    reseq_queryset = get_ale_number_selector(ale_id, reseq_queryset)

    return reseq_queryset


def get_reseq_dict(ale_experiment_id):
    reseq_queryset = get_reseq_queryset(ale_experiment_id, None)
    reseq_dict = collections.OrderedDict((reseq.id, reseq) for reseq in reseq_queryset)
    return reseq_dict


def get_ordered_reseq_dict(ale_experiment_id):
    """
    Args:
        ale_experiment_id:

    Returns:
        reseq_dict: a ordered dictionary of reseq values and their ID's as keys.
        The reseq values within the dictionary will be ordered according to that
        defined within RESEQ_QUERY

    """
    reseq_queryset = get_reseq_queryset(ale_experiment_id, None)
    reseq_dict = collections.OrderedDict((reseq.id, reseq) for reseq in reseq_queryset)
    return reseq_dict


def get_ale_exp_reseq_obs_mut_lists(reseq_dict):
    """
    Be aware that this function removes all stating strain mutations.

    Args:
        reseq_dict:

    Returns:

    """

    ale_exp_obs_mut_list = []
    obs_mut_to_exclude_queryset = []

    # TODO: Don't filter out starting strain mutations here but rather when passing observed mutation queryset into filter.util.filter_mutations
    for reseq_id in reseq_dict:
        reseq = reseq_dict[reseq_id]
        if reseq.ale_id == ale.common.STARTING_STRAIN_ALE_ID:
            obs_mut_to_exclude_queryset = ObservedMutation.objects.filter(sequencing_experiment_id=reseq_id)
        else:
            ale_exp_obs_mut_list.append(ObservedMutation.objects.filter(sequencing_experiment_id=reseq_id))

    filtered_ale_exp_obs_mut_list = []
    for reseq_obs_mut_list in ale_exp_obs_mut_list:
        filtered_reseq_mutation_list = [mutation for mutation in reseq_obs_mut_list if mutation not in obs_mut_to_exclude_queryset]
        filtered_ale_exp_obs_mut_list.append(filtered_reseq_mutation_list)

    return filtered_ale_exp_obs_mut_list


def get_mutation_queryset_from_observed_mutation_queryset(observed_mutations_queryset):
    return Mutation.objects.filter(pk__in=observed_mutations_queryset.values_list("mutation", flat=True))


def get_all_ale_experiments():
    return AleExperiment.objects.all().order_by('name')


def get_recent_experiments(ale_experiment_id=None):

    recent, created = RecentExperiments.objects.get_or_create(id=1)

    if ale_experiment_id is not None:
        recent_list = [recent.first, recent.second, recent.third, recent.fourth, recent.fifth]

        if ale_experiment_id not in recent_list:
            recent.fifth = recent.fourth
            recent.fourth = recent.third
            recent.third = recent.second
            recent.second = recent.first
            recent.first = ale_experiment_id
        else:
            temp = [x for x in recent_list if x != ale_experiment_id]
            recent.fifth = temp[3]
            recent.fourth = temp[2]
            recent.third = temp[1]
            recent.second = temp[0]
            recent.first = ale_experiment_id

        recent.save()

    recent_experiments = []

    if recent.first is not None:
        recent_experiments = experiment_exists(recent.first, recent_experiments)

    if recent.second is not None:
        recent_experiments = experiment_exists(recent.second, recent_experiments)

    if recent.third is not None:
        recent_experiments = experiment_exists(recent.third, recent_experiments)

    if recent.fourth is not None:
        recent_experiments = experiment_exists(recent.fourth, recent_experiments)

    if recent.fifth is not None:
        recent_experiments = experiment_exists(recent.fifth, recent_experiments)

    return recent_experiments


def experiment_exists(ale_id, recent_experiments):

    try:
        recent_experiments.append(AleExperiment.objects.get(ale_id=ale_id))
    except ObjectDoesNotExist:
        pass

    return recent_experiments
