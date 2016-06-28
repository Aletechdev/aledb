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

    if wt_filter:
        seq_experiment_ordered_dict = seq.views.common.filter_out_starting_strain_seq_experiment(
            seq_experiment_ordered_dict)

    seq_experiment_ordered_dict = seq.views.common.filter_checked_flasks(request, seq_experiment_ordered_dict)

    table_header = seq.views.common.get_table_header(seq_experiment_ordered_dict)

    table_body = _get_table_body(seq_experiment_ordered_dict, request)

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


def _get_table_body(seq_experiment_dict, request):

    observed_mutations_query_set = seq.views.common.get_observed_mutations(seq_experiment_dict)

    ale_experiment_id = seq.views.common.get_ale_experiment_id(request)

    filter_settings = seq.views.common.get_filter_settings(ale_experiment_id)

    return seq.views.common.get_table_body(seq_experiment_dict, observed_mutations_query_set, request, filter_settings)


def _filter_out_starting_strain_seq_experiment(seq_experiment_ordered_dict):

    key_to_delete_found = False

    key_to_delete = None

    for key, value in seq_experiment_ordered_dict.items():

        if value.ale_id == ale.common.STARTING_STRAIN_ALE_ID:

            key_to_delete = key

            key_to_delete_found = True

    if key_to_delete_found and key_to_delete:

        del seq_experiment_ordered_dict[key_to_delete]

    return seq_experiment_ordered_dict
