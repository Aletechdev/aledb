from django.http import HttpResponse
from django.template import loader
from django.utils.safestring import mark_safe
import seq.views.common
from seq.views import mutation_table_builder
from seq.util import get_all_observed_mutations
from common.util import get_all_ale_exps, get_recent_ale_exps, get_reseq_ordered_dict
from common.util import check_hidden_columns_and_filters
from common.constants import POSITION_COLUMN_IN_REGULAR_MUTATION_TABLE
from django.core.serializers.json import DjangoJSONEncoder
import json
import common.constants


__author__ = 'pphaneuf'


def mutation_table(request):

    ale_experiment_id = seq.views.common.get_ale_experiment_id(request)
    exp_name = seq.views.common.get_ale_experiment_name(request)
    ale_no = seq.views.common.get_ale_id(request)
    ale_queryset = seq.views.common.get_ales(ale_experiment_id, True)

    ordered_reseq_dict = get_reseq_ordered_dict(ale_experiment_id, ale_no, request)
    ordered_reseq_dict = seq.views.common.filter_out_wt_reseq(ordered_reseq_dict)

    table_header = mutation_table_builder.get_table_header(ordered_reseq_dict)

    table_body = _get_table_body(ordered_reseq_dict, request)

    hidden_columns = check_hidden_columns_and_filters(request, ale_experiment_id)

    template = loader.get_template("base_table_template.html")

    context = {"ales": ale_queryset,
               "ale_experiment_name": exp_name,
               "ale_no": ale_no,
               "experiment_id": ale_experiment_id,
               "table_body": mark_safe(json.dumps(table_body, cls=DjangoJSONEncoder)),
               "title": exp_name + " Mutation Table",
               "table_header": table_header,
               "template_header": "Mutations",
               "hidden_columns": hidden_columns,
               "experiments": get_all_ale_exps(),
               "recent_experiments": get_recent_ale_exps(ale_experiment_id),
               "sorted_column": POSITION_COLUMN_IN_REGULAR_MUTATION_TABLE,
               "tag_dropdown": common.constants.TAGS
               }

    return HttpResponse(template.render(context, request), content_type="text/html")


def _get_table_body(reseq_dict, request):
    obs_mut_qryset = get_all_observed_mutations(list(reseq_dict.keys()))
    ale_experiment_id = seq.views.common.get_ale_experiment_id(request)
    return mutation_table_builder.get_table_body(reseq_dict,
                                                 obs_mut_qryset,
                                                 ale_experiment_id)
