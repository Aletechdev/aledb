from django.http import HttpResponse
from django.template import loader
from django.utils.safestring import mark_safe
import seq.views.common
from seq.views import mutation_table_builder
from common.constants import \
    REQUEST_MUTATION_ID, \
    POSITION_COLUMN_IN_ENRICH_OR_FIXED_MUT_TABLE
from common.util import get_reseq_ordered_dict,\
    get_all_ale_exps,\
    get_recent_ale_exps,\
    check_hidden_columns_and_filters
from fixation.util import get_exp_fixed_obs_mut_qryset
import common.constants


__author__ = 'Patrick Phaneuf'


def fixating_mutations(request):
    exp_name = seq.views.common.get_ale_experiment_name(request)
    ale_experiment_id = seq.views.common.get_ale_experiment_id(request)
    ale_number = seq.views.common.get_ale_id(request)
    ale_qryset = seq.views.common.get_ales(ale_experiment_id, True)

    reseq_ordered_dict = get_reseq_ordered_dict(ale_experiment_id, ale_number, request)

    table_header = mutation_table_builder.get_table_header(reseq_ordered_dict,
                                                           mutation_table_builder.TableType.FIXATING_MUTATIONS)

    obs_mut_qryset = get_exp_fixed_obs_mut_qryset(reseq_ordered_dict)

    table_body = mutation_table_builder.get_table_body(request, reseq_dict=reseq_ordered_dict,
                                                       observed_mutations_queryset=obs_mut_qryset,
                                                       ale_experiment_id=int(ale_experiment_id),
                                                       table_type=mutation_table_builder.TableType.FIXATING_MUTATIONS)

    hidden_columns = check_hidden_columns_and_filters(request, ale_experiment_id)

    template = loader.get_template("base_table_template.html")

    context = {"ales": ale_qryset,
               "ale_experiment_name": exp_name,
               "ale_no": ale_number,
               "ale_experiment_id": ale_experiment_id,
               "table_body": mark_safe(table_body),
               "title": exp_name + " Fixed Mutations",
               "table_header": mark_safe(table_header),
               "template_header": "Fixating Mutations",
               "hidden_columns": hidden_columns,
               "experiments": get_all_ale_exps(),
               "recent_experiments": get_recent_ale_exps(int(ale_experiment_id)),
               "sorted_column": POSITION_COLUMN_IN_ENRICH_OR_FIXED_MUT_TABLE,
               "tag_dropdown": common.constants.TAGS}

    return HttpResponse(template.render(context, request), content_type="text/html")