from django.http import HttpResponse

from django.contrib.auth.decorators import login_required

from django.template import Context, loader

from django.utils.safestring import mark_safe

import ale.common

import ale.models

import seq.models

import seq.views.common


__author__ = 'Patrick Phaneuf'

EXPERIMENT_MAPPING_FILTERING_SHOW_FLAG = "show"
EXPERIMENT_MAPPING_FILTERING_REMOVE_FLAG = "remove"

# TODO: this implementation shares much with mutations.py; refactored shared implementations into common.py


@login_required
def key_mutations(request):

    ale_experiment_id = seq.views.common.get_ale_experiment_id(request)

    ale_experiment_name = seq.views.common.get_ale_experiment_name(request)

    ale_number = seq.views.common.get_ale_number(request)

    seq_experiment_queryset = seq.views.common.get_seq_experiment_queryset(ale_experiment_id)

    seq_experiment_ordered_dict = seq.views.common.get_experiment_ordered_dict(request)

    seq_experiment_ordered_dict = _filter_out_starting_strain_seq_experiment(seq_experiment_ordered_dict)

    seq_experiment_ordered_dict = seq.views.common.filter_checked_flasks(request, seq_experiment_ordered_dict)

    table_header = seq.views.common.get_table_header(seq_experiment_ordered_dict)

    table_body = _get_table_body(seq_experiment_ordered_dict, request)

    template = loader.get_template("table_template.html")

    context = Context({"experiments": seq_experiment_queryset,
                       "ale_experiment_name": ale_experiment_name,
                       "ale_no": ale_number,
                       "experiment_id": ale_experiment_id,
                       "table_body": mark_safe(table_body),
                       "title": "Mutation table",
                       "table_header": mark_safe(table_header),
                       "template_header": "Key Mutations"})

    return HttpResponse(template.render(context))


def _filter_out_starting_strain_seq_experiment(seq_experiment_ordered_dict):

    key_to_delete_found = False

    key_to_delete = None

    for key, value in seq_experiment_ordered_dict.iteritems():

        if value.ale_id == ale.common.STARTING_STRAIN_ALE_ID:

            key_to_delete = key

            key_to_delete_found = True

    if key_to_delete_found and key_to_delete:

        del seq_experiment_ordered_dict[key_to_delete]

    return seq_experiment_ordered_dict


def _get_table_body(seq_experiment_dict, request):

    ale_experiment_id = seq.views.common.get_ale_experiment_id(request)

    filter_settings = seq.views.common.get_filter_settings(ale_experiment_id)

    key_mutation_queryset = ale.models.KeyMutation.objects.filter(ale_experiment_id=ale_experiment_id)

    observed_mutations_query_set = _get_observed_key_mutations(seq_experiment_dict, key_mutation_queryset)

    return seq.views.common.get_table_body(seq_experiment_dict, observed_mutations_query_set, request, filter_settings)


def _get_observed_key_mutations(seq_experiment_dict, key_mutation_queryset):

    # 2 filters for the queryset:
    # 1) get observed_mutations that are contained within the seq_experiment_dict,
    # 2) get observed_mutations that reference to the key_mutation_queryset
    # TODO: refactor

    seq_experiment_observed_mutation_queryset = seq.models.ObservedMutation.objects.filter(sequencing_experiment_id__in=seq_experiment_dict.keys())

    key_mutation_id_list = []

    for key_mutation in key_mutation_queryset:

        key_mutation_id_list.append(key_mutation.mutation_id)

    key_mutation_observed_mutation_queryset = seq_experiment_observed_mutation_queryset.filter(mutation_id__in=key_mutation_id_list)

    return key_mutation_observed_mutation_queryset
