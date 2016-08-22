from django.http import HttpResponse

from django.contrib.auth.decorators import login_required

from django.template import loader

from django.utils.safestring import mark_safe

import aleinfo.settings as settings

import seq.views.common

from seq.views import mutation_table_builder

import filter.mutation_filter

from common.db_util import get_all_observed_mutations

import seq.views.common

import json


__author__ = 'pphaneuf'


if hasattr(settings, seq.views.common.SETTINGS_SEQUENCING_URL):
    reseqencing_report_url = settings.sequencing_url
else:
    reseqencing_report_url = seq.views.common.DEFAULT_RESEQ_REPORT_URL


@login_required
def mutation_table(request):

    ale_experiment_id = seq.views.common.get_ale_experiment_id(request)
    ale_experiment_name = seq.views.common.get_ale_experiment_name(request)
    ale_number = seq.views.common.get_ale_number(request)
    is_ref_strain_filtered = seq.views.common.is_ref_strain_filtered(request)
    ale_queryset = seq.views.common.get_ales(ale_experiment_id, is_ref_strain_filtered)

    ordered_reseq_dict = seq.views.common.get_ordered_reseq_dict(request, include_starting_strain=True)

    wt_id = None
    if is_ref_strain_filtered:
        wt_id = seq.views.common.get_wt_reseq_id(ordered_reseq_dict)
        ordered_reseq_dict = seq.views.common.filter_out_wt_reseq(ordered_reseq_dict)

    ordered_reseq_dict = mutation_table_builder.filter_checked_flasks(request, ordered_reseq_dict)

    table_header = mutation_table_builder.get_table_header(ordered_reseq_dict)

    table_body = _get_table_body(ordered_reseq_dict, request, is_ref_strain_filtered, wt_id)

    print(request.GET.get('hidden_columns'))

    hidden_columns = "5678"

    template = loader.get_template("mutation_table_template.html")

    context = {"ales": ale_queryset,
               "ale_experiment_name": ale_experiment_name,
               "ale_no": ale_number,
               "experiment_id": ale_experiment_id,
               "table_body": mark_safe(table_body),
               "title": "Mutation Table",
               "table_header": mark_safe(table_header),
               "template_header": "Mutations",
               "wt_filter": is_ref_strain_filtered,
               "hidden_columns": hidden_columns}

    return HttpResponse(template.render(context))


def _get_table_body(reseq_dict, request, wt_filter, wt_id):

    observed_mutations_query_set = get_all_observed_mutations(list(reseq_dict.keys()))

    ale_experiment_id = seq.views.common.get_ale_experiment_id(request)

    filter_settings = filter.mutation_filter.get_filter_settings(ale_experiment_id)

    ref_strain_mutation_id_list = None

    if wt_filter:
        ref_strain_mutation_list = get_all_observed_mutations([wt_id])
        ref_strain_mutation_id_list = [observed_mutation.mutation.id for observed_mutation in ref_strain_mutation_list]

    return mutation_table_builder.get_table_body(reseq_dict,
                                                 observed_mutations_query_set,
                                                 filter_settings,
                                                 ref_strain_mutation_id_list)
