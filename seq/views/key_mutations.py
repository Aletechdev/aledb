from django.http import HttpResponse

from django.contrib.auth.decorators import login_required

from django.template import Context, loader

from django.utils.safestring import mark_safe

import seq.views.common

from collections import OrderedDict

from seq.views import mutation_table_builder


__author__ = 'Patrick Phaneuf'


@login_required
def key_mutations(request):

    ale_experiment_id = seq.views.common.get_ale_experiment_id(request)

    ale_experiment_name = seq.views.common.get_ale_experiment_name(request)

    ale_number = seq.views.common.get_ale_number(request)
 
    ale_queryset = seq.views.common.get_ales(ale_experiment_id, True)

    seq_experiment_ordered_dict = seq.views.common.get_experiment_ordered_dict(request)
    seq_experiment_ordered_dict = seq.views.common.filter_out_starting_strain_seq_experiment(seq_experiment_ordered_dict)
    seq_experiment_ordered_dict = mutation_table_builder.filter_checked_flasks(request, seq_experiment_ordered_dict)

    # TODO: make control for choosing primary seq experiment.
    # TODO: filter out starting starting observed mutations.
    seq_experiment_ordered_dict, observed_mutation_queryset = _get_experiments_and_mutations(seq_experiment_ordered_dict, 7)

    table_header = mutation_table_builder.get_table_header(seq_experiment_ordered_dict)

    table_body = _get_table_body(seq_experiment_ordered_dict, request, observed_mutation_queryset)

    template = loader.get_template("common_mutations.html")

    context = Context({"ales": ale_queryset,
                       "ale_experiment_name": ale_experiment_name,
                       # "sample_name_list": sample_name_list,
                       "ale_no": ale_number,
                       "experiment_id": ale_experiment_id,
                       "table_body": mark_safe(table_body),
                       "title": "Key Mutations",
                       "table_header": mark_safe(table_header),
                       "template_header": "Key Mutations"})

    return HttpResponse(template.render(context))


# TODO: need to refactor
def _get_experiments_and_mutations(seq_experiment_dict, primary_seq_experiment_id):

    primary_observed_mutations_query_set = seq.views.common.get_observed_mutations([primary_seq_experiment_id])
    total_common_observed_mutations_queryset = primary_observed_mutations_query_set.all()

    seq_experiment_common_mutation_count_list = []

    for seq_experiment_id, seq_experiment in seq_experiment_dict.items():

        if seq_experiment_id != primary_seq_experiment_id:

            observed_mutations_query_set = seq.views.common.get_observed_mutations([seq_experiment_id])
            common_observed_mutation_queryset = _get_common_observed_mutation_queryset(primary_observed_mutations_query_set, observed_mutations_query_set)
            total_common_observed_mutations_queryset = total_common_observed_mutations_queryset.all() | common_observed_mutation_queryset.all()
            seq_experiment_common_mutation_count_list.append((len(common_observed_mutation_queryset), seq_experiment_id))

    sorted_seq_experiment_common_mutation_count_list = sorted(seq_experiment_common_mutation_count_list, reverse=True)

    new_ordered_dict = OrderedDict()
    new_ordered_dict[primary_seq_experiment_id] = seq_experiment_dict[primary_seq_experiment_id]

    for entry in sorted_seq_experiment_common_mutation_count_list:

        seq_experiment_id = entry[1]
        new_ordered_dict[seq_experiment_id] = seq_experiment_dict[seq_experiment_id]

    return new_ordered_dict, total_common_observed_mutations_queryset


def _get_common_observed_mutation_queryset(primary_observed_mutations_query_set, observed_mutations_query_set):

    return observed_mutations_query_set.filter(mutation__in=primary_observed_mutations_query_set.values_list("mutation", flat=True))


def _get_table_body(seq_experiment_dict, request, observed_mutations_queryset):
    # observed_mutations_queryset = seq.views.common.get_observed_mutations(list(seq_experiment_dict.keys()))

    ale_experiment_id = seq.views.common.get_ale_experiment_id(request)

    filter_settings = seq.views.common.get_filter_settings(ale_experiment_id)

    return mutation_table_builder.get_table_body(seq_experiment_dict,
                                                 observed_mutations_queryset,
                                                 filter_settings)

