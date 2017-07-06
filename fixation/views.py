# TODO: All resources being pulled from seq app could possibly be stored in a common dir.

from django.http import HttpResponse
from django.template import loader
from django.utils.safestring import mark_safe
#TODO: seq.views.common.get_ordered_reseq_dict could likely be refactored into common.db_util.get_reseq_dict
import seq.views.common
from seq.views import mutation_table_builder
from seq.models import ObservedMutation
from seq.models import ResequencingExperiment
from filter import util
from fixation.models import FixatedMutation
from fixation.fixation import filter_for_ascending_freq
import metadata.views
from common.constants import REQUEST_MUTATION_ID, REQUEST_ALE_EXPERIMENT_ID, POSITION_COLUMN_IN_SHARED_MUTATION_TALBE
from common.util import get_reseq_ordered_dict, get_all_ale_experiments, get_recent_experiments, check_hidden_columns_and_filters
from collections import OrderedDict
from genes.util import get_gene_list
import operator
from functools import reduce
from django.db.models import Q
import common.constants
import ast

HTML_MUTATION_TABLE_HEADER = """<tr><td></td><td>Position</td><td>Mutation Type</td><td>Sequence Change</td><td>Gene</td><td>Function</td><td>Product</td><td>GO Process</td><td>GO Component</td><td>Protein change</td>"""

__author__ = 'Patrick Phaneuf'

REQUEST_ASCENDING_FREQ_FILTER = 'asndflt'


# TODO: very similar to common_mutations page workflow. Should consolidate somehow.
def fixating_mutations(request):
    ale_experiment_name = seq.views.common.get_ale_experiment_name(request)
    ale_experiment_id = seq.views.common.get_ale_experiment_id(request)
    ale_number = seq.views.common.get_ale_id(request)
    ale_queryset = seq.views.common.get_ales(ale_experiment_id, True)
    is_ascending_freq_filter = _is_ascending_freq_filter(request)

    ale_experiment_id = request.GET.get(REQUEST_ALE_EXPERIMENT_ID)
    reseq_ordered_dict = get_reseq_ordered_dict(ale_experiment_id, ale_number, request)
    reseq_ordered_dict = seq.views.common.filter_out_wt_reseq(reseq_ordered_dict)

    table_header = mutation_table_builder.get_table_header(reseq_ordered_dict,
                                                           mutation_table_builder.TableType.FIXATING_MUTATIONS)

    filter_settings = util.get_filter_settings(ale_experiment_id)

    observed_mutation_queryset = _get_experiment_fixating_observed_mutation_queryset(ale_experiment_id,
                                                                                     reseq_ordered_dict,
                                                                                     is_ascending_freq_filter)

    table_body = mutation_table_builder.get_table_body(reseq_dict=reseq_ordered_dict,
                                                       observed_mutations_queryset=observed_mutation_queryset,
                                                       ale_experiment_id=int(ale_experiment_id),
                                                       table_type=mutation_table_builder.TableType.FIXATING_MUTATIONS,
                                                       filter_settings=filter_settings)

    hidden_columns = check_hidden_columns_and_filters(request, ale_experiment_id)

    template = loader.get_template("base_table_template.html")

    context = {"ales": ale_queryset,
               "ale_experiment_name": ale_experiment_name,
               "ale_no": ale_number,
               "experiment_id": ale_experiment_id,
               "table_body": mark_safe(table_body),
               "title": "Fixed Mutations",
               "table_header": mark_safe(table_header),
               "is_ascending_freq_filter": is_ascending_freq_filter,
               "template_header": "Fixating Mutations",
               "hidden_columns": hidden_columns,
               "experiments": get_all_ale_experiments(),
               "recent_experiments": get_recent_experiments(int(ale_experiment_id)),
               "sorted_column": POSITION_COLUMN_IN_SHARED_MUTATION_TALBE,
               "tag_dropdown": common.constants.TAGS
               }

    return HttpResponse(template.render(context))


def shared_fixated_mutations(request):

    mutation_id = request.GET.get(REQUEST_MUTATION_ID)
    selected_fixating_mutation_queryset = FixatedMutation.objects.filter(mutation_id=mutation_id)
    fixating_mutation = selected_fixating_mutation_queryset[0]  # Should only be one fixating mutation per mutation_id
    fixated_gene_str = fixating_mutation.mutation.gene
    fixated_gene_list = get_gene_list(fixated_gene_str)

    shared_fixated_gene_query = reduce(operator.or_, (Q(mutation__gene__contains=gene) for gene in fixated_gene_list))
    fixated_mutation_queryset = FixatedMutation.objects.filter(shared_fixated_gene_query)

    # fixated_mutation_ale_experiment_list = []
    ale_exp_fixed_obs_mut_id_list = []
    for fix_mut in fixated_mutation_queryset:
        # fixated_mutation_ale_experiment_list.append(fix_mut.ale_experiment)
        fixed_obs_mut_id_lists = list(ast.literal_eval(fix_mut.fixed_observed_mutation_series))  # Turns list of string into 2D list of observed mutation id lists.
        for fixed_obs_mut_id_list in fixed_obs_mut_id_lists:
            ale_exp_fixed_obs_mut_id_list = ale_exp_fixed_obs_mut_id_list + fixed_obs_mut_id_list

    observed_mutation_queryset = ObservedMutation.objects.filter(id__in=ale_exp_fixed_obs_mut_id_list)

    # observed_mutation_queryset = ObservedMutation.objects.filter(mutation__in=fixated_mutation_queryset.values('mutation'))
    # observed_mutation_queryset = observed_mutation_queryset.filter(sequencing_experiment__tech_rep__isolate__flask__ale_id__ale_experiment__in=fixated_mutation_ale_experiment_list)

    ordered_reseq_queryset = ResequencingExperiment.objects.all().order_by(
        'tech_rep__isolate__flask__ale_id__ale_experiment__name',
        'tech_rep__isolate__flask__ale_id__ale_id',
        'tech_rep__isolate__flask__flask_number',
        'tech_rep__isolate__isolate_number')
    ordered_reseq_queryset = ordered_reseq_queryset.filter(
        id__in=observed_mutation_queryset.values('sequencing_experiment'))

    ordered_reseq_dict = OrderedDict((reseq.id, reseq) for reseq in ordered_reseq_queryset)
    table_header = mutation_table_builder.get_table_header(ordered_reseq_dict)

    table_body = mutation_table_builder.get_table_body(ordered_reseq_dict,
                                                       observed_mutation_queryset,
                                                       table_type=mutation_table_builder.TableType.SHARED)

    reseq_info_list = metadata.views.get_reseq_info_list(ordered_reseq_queryset)

    check_hidden_columns_and_filters(request, None)

    template = loader.get_template("fixation/shared_fixating_mutations.html")
    context = {"title": "Shared Fixated Genes",
               "table_header": mark_safe(table_header),
               "table_body": mark_safe(table_body),
               "reseq_info_list": reseq_info_list,
               "experiments": get_all_ale_experiments(),
               "recent_experiments": get_recent_experiments()
               }

    return HttpResponse(template.render(context))


def _is_ascending_freq_filter(request):
    ret_val = False
    if request.GET.get(REQUEST_ASCENDING_FREQ_FILTER) is not None:
        ret_val = True
    return ret_val


def _get_experiment_fixating_observed_mutation_queryset(ale_experiment_id, ordered_reseq_dict, is_only_ascending=False):

    fixating_mutation_queryset = FixatedMutation.objects.filter(ale_experiment_id=ale_experiment_id)
    fixating_observed_mutation_queryset = ObservedMutation.objects.none()
    #TODO: filter out mutations from samples that were removed from table.

    #fixating_observed_mutation_queryset = _get_fixating_observed_mutation_queryset(fixating_mutation_queryset, ordered_reseq_dict.keys())
    for fixing_mutation in fixating_mutation_queryset:
        fixating_obs_mut_queryset_list = _get_fixating_obs_mut_queryset_list(fixing_mutation, ordered_reseq_dict.keys())
        if is_only_ascending:
            fixating_obs_mut_queryset_list = filter_for_ascending_freq(fixating_obs_mut_queryset_list)  # TODO: this should return the list of querysets we want to keep.
        # Could have more than 1 fixing sequence
        for fixating_obs_mut_queryset in fixating_obs_mut_queryset_list:
            fixating_observed_mutation_queryset = fixating_observed_mutation_queryset | fixating_obs_mut_queryset

    return fixating_observed_mutation_queryset


# def _get_fixating_observed_mutation_queryset(fixating_mutation_queryset, reseq_id_list):
#     fixating_mutation_id_list = [fixating_mutation.mutation.id for fixating_mutation in fixating_mutation_queryset]
#     all_observed_mutation_queryset = ObservedMutation.objects.filter(sequencing_experiment_id__in=reseq_id_list)
#     fixating_observed_mutation_queryset = all_observed_mutation_queryset.filter(mutation_id__in=fixating_mutation_id_list)
#     return fixating_observed_mutation_queryset
def _get_fixating_obs_mut_queryset_list(fixating_mutation, reseq_id_list):
    all_observed_mutation_queryset = ObservedMutation.objects.filter(sequencing_experiment_id__in=reseq_id_list)
    fixed_obs_mut_lists = list(ast.literal_eval(fixating_mutation.fixed_observed_mutation_series))
    obs_mut_queryset_list = []
    for fixed_obs_mut_list in fixed_obs_mut_lists:
        obs_mut_queryset = all_observed_mutation_queryset.filter(id__in=fixed_obs_mut_list)
        obs_mut_queryset_list.append(obs_mut_queryset)

    # TODO: get mutations back from
    # # obs_mut_queryset_1 = all_observed_mutation_queryset.filter(id__in=[824, 983, 2457])
    # # obs_mut_queryset_2 = all_observed_mutation_queryset.filter(id__in=[1058, 1634, 2426])
    # obs_mut_queryset_list = [obs_mut_queryset_1, obs_mut_queryset_2]

    return obs_mut_queryset_list
