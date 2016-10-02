# TODO: Had to implement this separate from common.util since can't currently run unit tests on modules that refer to models. Fix this

import collections
import ale.common
from common.util import get_ale_experiment_selector, get_ale_number_selector
from seq.models import ResequencingExperiment
from seq.models import ObservedMutation
from seq.models import Mutation
from ale.models import AleExperiment, RecentExperiments
from django.core.exceptions import ObjectDoesNotExist
from django.core.cache import cache

__author__ = 'Patrick Phaneuf, Denny Gosting'


# TODO: go in seq.util
def get_reseq_queryset(ale_experiment_id, ale_id=None):
    reseq_queryset = ResequencingExperiment.objects.all().order_by(
        'tech_rep__isolate__flask__ale_id__ale_experiment__name',
        'tech_rep__isolate__flask__ale_id__ale_id',
        'tech_rep__isolate__flask__flask_number',
        'tech_rep__isolate__isolate_number')

    reseq_queryset = get_ale_experiment_selector(ale_experiment_id, reseq_queryset)

    reseq_queryset = get_ale_number_selector(ale_id, reseq_queryset)

    return reseq_queryset


# TODO: go in seq.util
def get_reseq_dict(ale_experiment_id):
    reseq_queryset = get_reseq_queryset(ale_experiment_id, None)
    reseq_dict = collections.OrderedDict((reseq.id, reseq) for reseq in reseq_queryset)
    return reseq_dict


# TODO: go in seq.util
def get_ordered_reseq_dict(ale_experiment_id, ale_no=None):
    """
    Args:
        ale_experiment_id:
        ale_no:

    Returns:
        reseq_dict: a ordered dictionary of reseq values and their ID's as keys.
        The reseq values within the dictionary will be ordered according to that
        defined within RESEQ_QUERY

    """
    reseq_queryset = get_reseq_queryset(ale_experiment_id, ale_no)
    reseq_dict = collections.OrderedDict((reseq.id, reseq) for reseq in reseq_queryset)
    return reseq_dict


# TODO: go in seq.util
def get_mutation_queryset_from_obs_mut_queryset(observed_mutations_queryset):
    return Mutation.objects.filter(pk__in=observed_mutations_queryset.values_list("mutation", flat=True))


# TODO: go in ale.util
def get_all_ale_experiments():
    return AleExperiment.objects.all().order_by('name')


# TODO: go in ale.util
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
        recent_experiments = ale_exp_exists(recent.first, recent_experiments)

    if recent.second is not None:
        recent_experiments = ale_exp_exists(recent.second, recent_experiments)

    if recent.third is not None:
        recent_experiments = ale_exp_exists(recent.third, recent_experiments)

    if recent.fourth is not None:
        recent_experiments = ale_exp_exists(recent.fourth, recent_experiments)

    if recent.fifth is not None:
        recent_experiments = ale_exp_exists(recent.fifth, recent_experiments)

    return recent_experiments


def ale_exp_exists(ale_id, recent_experiments):

    try:
        recent_experiments.append(AleExperiment.objects.get(ale_id=ale_id))
    except ObjectDoesNotExist:
        pass

    return recent_experiments


def clear_dashboard_cache():

    cache.delete('dashboard_mutation')

    cache.delete('dashboard_observed_mutation')

    cache.delete('bar_chart_gene_dict')
