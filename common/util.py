from common.constants import REQUEST_ALL
from filter.models import AleExperimentFilter
from filter.util import get_global_filter
from ale.models import TechnicalReplicate
import collections
from seq.models import ResequencingExperiment
from seq.models import Mutation
from ale.models import AleExperiment, RecentExperiments
from django.core.exceptions import ObjectDoesNotExist
from django.core.cache import cache

from logs.aledb_logger import getLogger

__author__ = 'Patrick Phaneuf, Denny Gosting'

log = getLogger("aledbLogger")
usage = getLogger("usage")

# TODO: go in seq.util
def get_ordered_reseq_queryset(ale_experiment_id, ale_id=None):
    reseq_qryset = ResequencingExperiment.objects.select_related(
        'tech_rep__isolate__flask__ale_id__ale_experiment'
    ).order_by(
        'tech_rep__isolate__flask__ale_id__ale_experiment__name',
        'tech_rep__isolate__flask__ale_id__ale_id',
        'tech_rep__isolate__flask__flask_number',
        'tech_rep__isolate__isolate_number',
        'tech_rep__tech_rep_number'
    )

    reseq_qryset = filter_for_ale_exp(ale_experiment_id, reseq_qryset)
    reseq_qryset = filter_for_ale(ale_id, reseq_qryset)

    return reseq_qryset


# TODO: go in seq.util
# def get_reseq_dict(ale_experiment_id):
#     reseq_queryset = get_ordered_reseq_queryset(ale_experiment_id, None)
#     reseq_dict = collections.OrderedDict((reseq.id, reseq) for reseq in reseq_queryset)
#     return reseq_dict


# TODO: go in seq.util
def get_reseq_ordered_dict(ale_experiment_id, ale_no=None, request=None):
    """
    Args:
        ale_experiment_id:
        ale_no:

    Returns:
        reseq_ordered_dict: a ordered dictionary of reseq values and their ID's as keys.
        The reseq values within the dictionary will be ordered according to that
        defined within RESEQ_QUERY
        :param request:

    """
    reseq_queryset = get_ordered_reseq_queryset(ale_experiment_id, ale_no)
    if request and request.GET.get('tag_select'):
        tag = request.GET.get('tag_select').split(':')
        if tag[0] == 'Hide Tag':
            reseq_queryset = reseq_queryset.exclude(tech_rep__tags__contains=tag[1].replace(' ', ''))
        elif tag[0] == 'Show Tag':
            reseq_queryset = reseq_queryset.filter(tech_rep__tags__contains=tag[1].replace(' ', ''))
    reseq_ordered_dict = collections.OrderedDict((reseq.id, reseq) for reseq in reseq_queryset)
    return reseq_ordered_dict


# TODO: go in seq.util
def get_mut_queryset_from_obs_mut_queryset(observed_mutations_queryset):
    return Mutation.objects.filter(pk__in=observed_mutations_queryset.values_list("mutation", flat=True))


# TODO: go in ale.util
def get_all_ale_exps():

    usage.info("get_all_ale_exps called from %s", str(get_client_ip(request)))

    return AleExperiment.objects.all().order_by('name')


# TODO: go in ale.util
def get_recent_ale_exps(ale_experiment_id=None):

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

    cache.delete('dashboard_bar_chart_gene_dict')



def filter_for_ale_exp(ale_experiment_id, reseq_query):
    if ale_experiment_id is None or ale_experiment_id == REQUEST_ALL:
        return reseq_query
    else:
        return reseq_query.filter(tech_rep__isolate__flask__ale_id__ale_experiment__ale_id=ale_experiment_id)


def filter_for_ale(ale_id, reseq_query):
    if ale_id is None or ale_id == REQUEST_ALL:
        return reseq_query
    else:
        return reseq_query.filter(tech_rep__isolate__flask__ale_id__ale_id=ale_id)


# TODO: This should probably be refactored and split into separate functions
# TODO: The hidden columns functionality no longer seems to be used.
def check_hidden_columns_and_filters(request, ale_experiment_id):
    if request.method == "GET":
        hidden_columns = request.GET.get('hidden_columns', "")
    else:
        hidden_columns = ""
        save_method = request.POST.get('save_method')
        mut_id = request.POST.get('mut_id')

        if save_method == 'global':
            global_filter = get_global_filter()
            global_filter_ignored_mutations = global_filter.ignored_mutations
            global_filter_ignored_mutations += "," + mut_id
            global_filter.ignored_mutations = global_filter_ignored_mutations
            global_filter.save()

        elif save_method == 'experiment' and ale_experiment_id is not None:
            ale_exp_filter, created = AleExperimentFilter.objects.get_or_create(ale_experiment_id=ale_experiment_id)
            ignored_mutations = ale_exp_filter.ignored_mutations
            ignored_mutations += "," + mut_id
            ale_exp_filter.ignored_mutations = ignored_mutations
            ale_exp_filter.save()

        elif save_method == 'tag_mut':
            mutation = Mutation.objects.get(id=mut_id)
            if mutation.tags:
                selected_tag = request.POST.get('tag_name')
                tag_list = mutation.tags.split(',')
                if selected_tag in tag_list:
                    tag_list.remove(selected_tag)
                else:
                    tag_list.append(selected_tag)
                mutation.tags = ','.join(tag_list)
            else:
                mutation.tags = request.POST.get('tag_name')
            mutation.save()

        elif save_method == 'tag_rep':
            rep_id = request.POST.get('rep_id')
            replicate = TechnicalReplicate.objects.get(id=rep_id)
            if replicate.tags:
                selected_tag = request.POST.get('tag_name')
                tag_list = replicate.tags.split(',')
                if selected_tag in tag_list:
                    tag_list.remove(selected_tag)
                else:
                    tag_list.append(selected_tag)
                replicate.tags = ','.join(tag_list)
            else:
                replicate.tags = request.POST.get('tag_name')
            replicate.save()

    return hidden_columns
