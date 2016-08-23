from django.contrib.auth.decorators import login_required

from django.template import loader

from django.utils.safestring import mark_safe

from django.http import HttpResponse

from seq.views import common

from seq.views import mutation_table_builder

from filter import mutation_filter


__author__ = 'Patrick Phaneuf'


@login_required
def lineage(request):

    ale_experiment_id = common.get_ale_experiment_id(request)

    ale_experiment_name = common.get_ale_experiment_name(request)

    ale_number = common.get_ale_number(request)
    ale_queryset = common.get_ales(ale_experiment_id)
    ordered_reseq_dict = common.get_ordered_reseq_dict(request=request, include_starting_strain=True)
    ordered_reseq_dict = mutation_table_builder.filter_checked_flasks(request, ordered_reseq_dict)

    table_header = mutation_table_builder.get_table_header(ordered_reseq_dict)

    table_body = _get_table_body(ordered_reseq_dict, request)

    template = loader.get_template("table_template.html")

    context = {"ale_experiment_name": ale_experiment_name,
               "ales": ale_queryset,
               "ale_no": ale_number,
               "experiment_id": ale_experiment_id,
               "table_body": mark_safe(table_body),
               "title": "Mutation table",
               "table_header": mark_safe(table_header),
               "template_header": "Lineage Mutations"}

    return HttpResponse(template.render(context))


def _get_table_body(seq_experiment_dict, request):

    observed_mutations_query_set = common.get_all_observed_mutations(list(seq_experiment_dict.keys()))

    ale_experiment_id = common.get_ale_experiment_id(request)

    filter_settings = mutation_filter.get_filter_settings(ale_experiment_id)

    return mutation_table_builder.get_table_body(seq_experiment_dict, observed_mutations_query_set, filter_settings)

