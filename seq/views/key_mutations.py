from django.http import HttpResponse

from django.contrib.auth.decorators import login_required

from django.template import Context, loader

from django.utils.safestring import mark_safe

import ale.common

import ale.models

import seq.models

import seq.views.common

from seq.views import mutation_table_builder


__author__ = 'Patrick Phaneuf'


@login_required
def key_mutations(request):

    ale_experiment_id = seq.views.common.get_ale_experiment_id(request)

    ale_experiment_name = seq.views.common.get_ale_experiment_name(request)

    ale_number = seq.views.common.get_ale_id(request)

    ale_queryset = seq.views.common.get_ales(ale_experiment_id, True)

    ordered_reseq_dict = seq.views.common.get_ordered_reseq_dict(request)
    ordered_reseq_dict = seq.views.common.filter_out_wt_reseq(ordered_reseq_dict)
    ordered_reseq_dict = mutation_table_builder.filter_checked_flasks(request, ordered_reseq_dict)

    table_header = mutation_table_builder.get_table_header(ordered_reseq_dict)

    table_body = _get_table_body(ordered_reseq_dict, request)

    template = loader.get_template("table_template.html")

    context = Context({"ales": ale_queryset,
                       "ale_experiment_name": ale_experiment_name,
                       "ale_no": ale_number,
                       "experiment_id": ale_experiment_id,
                       "table_body": mark_safe(table_body),
                       "title": "Key Mutations",
                       "table_header": mark_safe(table_header),
                       "template_header": "Key Mutations"})

    return HttpResponse(template.render(context))


def _get_table_body(reseq_dict, request):

    ale_experiment_id = seq.views.common.get_ale_experiment_id(request)

    key_mutation_queryset = ale.models.KeyMutation.objects.filter(ale_experiment_id=ale_experiment_id)

    observed_mutations_query_set = _get_observed_key_mutations(reseq_dict, key_mutation_queryset)

    return mutation_table_builder.get_table_body(reseq_dict, observed_mutations_query_set)


def _get_observed_key_mutations(reseq_dict, key_mutation_queryset):

    # 2 filters for the queryset:
    # 1) get observed_mutations that are contained within the seq_experiment_dict,
    # 2) get observed_mutations that reference to the key_mutation_queryset
    # TODO: refactor

    seq_experiment_observed_mutation_queryset = seq.models.ObservedMutation.objects.filter(sequencing_experiment_id__in=reseq_dict.keys())

    key_mutation_id_list = []

    for key_mutation in key_mutation_queryset:

        key_mutation_id_list.append(key_mutation.mutation_id)

    key_mutation_observed_mutation_queryset = seq_experiment_observed_mutation_queryset.filter(mutation_id__in=key_mutation_id_list)

    return key_mutation_observed_mutation_queryset
