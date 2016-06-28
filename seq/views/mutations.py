from django.http import HttpResponse

from django.contrib.auth.decorators import login_required

from django.template import Context, loader

from django.utils.safestring import mark_safe

import aleinfo.settings as settings

import seq.views.common

import ale.common


__author__ = 'pphaneuf'


EXPERIMENT_MAPPING_FILTERING_SHOW_FLAG = "show"
EXPERIMENT_MAPPING_FILTERING_REMOVE_FLAG = "remove"


if hasattr(settings, seq.views.common.SETTINGS_SEQUENCING_URL):
    reseqencing_report_url = settings.sequencing_url
else:
    reseqencing_report_url = seq.views.common.DEFAULT_RESEQ_REPORT_URL


@login_required
def mutation_table(request):

    ale_experiment_id = seq.views.common.get_ale_experiment_id(request)

    ale_experiment_name = seq.views.common.get_ale_experiment_name(request)

    ale_number = seq.views.common.get_ale_number(request)

    wt_filter = seq.views.common.get_wt_filter(request)

    seq_experiment_queryset = seq.views.common.get_seq_experiment_queryset(ale_experiment_id, wt_filter)

    seq_experiment_ordered_dict = seq.views.common.get_experiment_ordered_dict(request, include_starting_strain=True)

    wt_id = None

    if wt_filter:
        
        wt_id = _get_wt_seq_experiment_id(seq_experiment_ordered_dict) 

        seq_experiment_ordered_dict = seq.views.common.filter_out_starting_strain_seq_experiment(
            seq_experiment_ordered_dict)

    seq_experiment_ordered_dict = seq.views.common.filter_checked_flasks(request, seq_experiment_ordered_dict)

    table_header = seq.views.common.get_table_header(seq_experiment_ordered_dict)

    table_body = _get_table_body(seq_experiment_ordered_dict, request, wt_filter, wt_id)

    template = loader.get_template("table_template.html")

    context = Context({"experiments": seq_experiment_queryset,
                       "ale_experiment_name": ale_experiment_name,
                       "ale_no": ale_number,
                       "experiment_id": ale_experiment_id,
                       "table_body": mark_safe(table_body),
                       "title": "Mutation Table",
                       "table_header": mark_safe(table_header),
                       "template_header": "Mutations",
                       "wt_filter": wt_filter})

    return HttpResponse(template.render(context))


def _get_table_body(seq_experiment_dict, request, wt_filter, wt_id):

    observed_mutations_query_set = seq.views.common.get_observed_mutations(list(seq_experiment_dict.keys()))

    ale_experiment_id = seq.views.common.get_ale_experiment_id(request)

    filter_settings = seq.views.common.get_filter_settings(ale_experiment_id)

    filter_mutation_id_list = None

    if wt_filter:
        filter_mutation_list = seq.views.common.get_observed_mutations([wt_id])
        filter_mutation_id_list = [observed_mutation.mutation.id for observed_mutation in filter_mutation_list]

    return seq.views.common.get_table_body(seq_experiment_dict,
                                           observed_mutations_query_set,
                                           request,
                                           filter_settings,
                                           filter_mutation_id_list)


def _get_wt_seq_experiment_id(seq_experiment_ordered_dict):

    wt_id = None

    for key, value in seq_experiment_ordered_dict.items():

        if value.ale_id == ale.common.STARTING_STRAIN_ALE_ID:

            wt_id = key

    return wt_id
