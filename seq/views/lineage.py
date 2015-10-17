from django.contrib.auth.decorators import login_required

from django.template import Context, loader

from django.utils.safestring import mark_safe

from django.http import HttpResponse

from seq.views import common


__author__ = 'Patrick'


@login_required
def lineage(request):

    ale_experiment_id = common.get_ale_experiment_id(request)

    ale_number = common.get_ale_number(request)

    seq_experiment_queryset = common.get_seq_experiment_queryset(ale_experiment_id)

    seq_experiment_ordered_dict = common.get_experiment_ordered_dict(request=request, include_starting_straing=True)

    seq_experiment_ordered_dict = common.filter_checked_flasks(request, seq_experiment_ordered_dict)

    table_header = common.get_table_header(seq_experiment_ordered_dict)

    table_body = _get_table_body(seq_experiment_ordered_dict, request)

    template = loader.get_template("table_template.html")

    context = Context({"experiments": seq_experiment_queryset,
                       "ale_no": ale_number,
                       "experiment_id": ale_experiment_id,
                       "table_body": mark_safe(table_body),
                       "title": "Mutation table",
                       "table_header": mark_safe(table_header)})

    return HttpResponse(template.render(context))


def _get_table_body(seq_experiment_dict, request):

    observed_mutations_query_set = common.get_observed_mutations(seq_experiment_dict)

    return common.get_table_body(seq_experiment_dict, observed_mutations_query_set, request)

