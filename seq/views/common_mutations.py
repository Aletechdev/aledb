from django.http import HttpResponse

from django.contrib.auth.decorators import login_required

from django.template import Context, loader

from django.utils.safestring import mark_safe

import seq.views.common

from collections import OrderedDict

from seq.views import mutation_table_builder


__author__ = 'Patrick Phaneuf'


REQUEST_PRIMARY_RESEQ_ID = "primary_reseq_id"

from pprint import pprint

@login_required
def common_mutations(request):

    ale_experiment_id = seq.views.common.get_ale_experiment_id(request)

    ale_experiment_name = seq.views.common.get_ale_experiment_name(request)
 
    ale_queryset = seq.views.common.get_ales(ale_experiment_id, True)

    ordered_reseq_dict = seq.views.common.get_ordered_reseq_dict(request)
    wt_id = seq.views.common.get_wt_reseq_id(ordered_reseq_dict)  # Must happen before filtering out wt reseq.
    ordered_reseq_dict = seq.views.common.filter_out_wt_reseq(ordered_reseq_dict)
    ordered_reseq_dict = mutation_table_builder.filter_checked_flasks(request, ordered_reseq_dict)

    primary_reseq_id = _get_primary_reseq_id(request)
    if primary_reseq_id is None:
        primary_reseq_id = list(ordered_reseq_dict.keys())[0]

    ordered_reseq_dict, observed_mutation_queryset = _get_experiments_and_mutations(ordered_reseq_dict, primary_reseq_id)

    table_header = mutation_table_builder.get_table_header(ordered_reseq_dict)

    filter_settings = seq.views.common.get_filter_settings(ale_experiment_id)

    filter_mutation_list = seq.views.common.get_observed_mutations([wt_id])
    filter_mutation_id_list = [observed_mutation.mutation.id for observed_mutation in filter_mutation_list]

    table_body = mutation_table_builder.get_table_body(ordered_reseq_dict,
                                                       observed_mutation_queryset,
                                                       filter_settings,
                                                       filter_mutation_id_list)

    template = loader.get_template("common_mutations.html")

    reseq_list = sorted(ordered_reseq_dict.values(), key=lambda x: x.ale_id)

    context = Context({"ales": ale_queryset,
                       "ale_experiment_name": ale_experiment_name,
                       "reseq_list": reseq_list,
                       "experiment_id": ale_experiment_id,
                       "table_body": mark_safe(table_body),
                       "title": "Key Mutations",
                       "table_header": mark_safe(table_header),
                       "template_header": "Key Mutations"})

    return HttpResponse(template.render(context))


# TODO: need to refactor
# Will return seq experiment dict ordered according to observed mutation count shared with primary seq experiment.
# Will return all seq experiments observed mutations shared with primary seq experiment.
def _get_experiments_and_mutations(reseq_dict, primary_reseq_id):

    primary_observed_mutations_queryset = seq.views.common.get_observed_mutations([primary_reseq_id])
    total_common_observed_mutations_queryset = primary_observed_mutations_queryset.all()

    reseq_common_mutation_count_list = []

    for reseq_id in reseq_dict.keys():

        if reseq_id != primary_reseq_id:

            observed_mutations_query_set = seq.views.common.get_observed_mutations([reseq_id])
            common_observed_mutation_queryset = _get_common_observed_mutation_queryset(primary_observed_mutations_queryset, observed_mutations_query_set)
            total_common_observed_mutations_queryset = total_common_observed_mutations_queryset.all() | common_observed_mutation_queryset.all()
            reseq_common_mutation_count_list.append((len(common_observed_mutation_queryset), reseq_id))

    sorted_reseq_common_mutation_count_list = sorted(reseq_common_mutation_count_list, reverse=True)

    new_ordered_dict = OrderedDict()
    new_ordered_dict[primary_reseq_id] = reseq_dict[primary_reseq_id]

    for entry in sorted_reseq_common_mutation_count_list:

        reseq_id = entry[1]
        new_ordered_dict[reseq_id] = reseq_dict[reseq_id]

    return new_ordered_dict, total_common_observed_mutations_queryset


def _get_common_observed_mutation_queryset(primary_observed_mutations_query_set, observed_mutations_query_set):

    return observed_mutations_query_set.filter(mutation__in=primary_observed_mutations_query_set.values_list("mutation", flat=True))


def _get_primary_reseq_id(request):

    primary_reseq_id = request.GET.get(REQUEST_PRIMARY_RESEQ_ID)

    primary_reseq_id = None if primary_reseq_id is None else int(primary_reseq_id)

    return primary_reseq_id
