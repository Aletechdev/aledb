import time
from django.http import HttpResponse
from django.template import loader
from django.utils.safestring import mark_safe
from common.util import get_user_context
from seq.util import get_reseq_ordered_dict
from ale.utils import get_all_ale_exps, get_recent_ale_exps
import seq.views.common
from seq.views import mutation_table_builder  # TODO: The mutation table build should use the factory pattern.
from common.constants import \
    REQUEST_MUTATION_ID, \
    POSITION_COLUMN_IN_ENRICH_OR_FIXED_MUT_TABLE
from common.util import check_hidden_columns_and_filters
import common.constants
from enrichment.util import get_enrich_obs_mut_qryset
from logs.aledb_logger import get_logger, user_extra, join_extras

exception_lgr = get_logger("exceptions")
usage_lgr = get_logger("usage")
performance_lgr = get_logger("performance")
__author__ = 'Patrick Phaneuf'


def enrichment_mutations(request):
    usage_lgr.info("enrichment", extra = user_extra(request))
    try:
        start_time = time.clock()
        context = get_user_context(request.user)
        experiment = seq.views.common.get_ale_experiment(request)
        exp_name = experiment.name
        ale_experiment_id = experiment.ale_id
        ale_number = seq.views.common.get_ale_id(request)
        ale_qrtset = seq.views.common.get_aleid_ale_id_list(ale_experiment_id, True)

        reseq_ordered_dict = get_reseq_ordered_dict(ale_experiment_id, ale_number, request)

        table_header = mutation_table_builder.get_table_header(request.user,
                                                               reseq_dict=reseq_ordered_dict,
                                                               table_type=mutation_table_builder.TableType.ENRICHMENT_MUTATIONS)

        table_body = _get_table_body(reseq_ordered_dict, experiment, request.user)

        hidden_columns = check_hidden_columns_and_filters(request, ale_experiment_id)

        template = loader.get_template('base_table_template.html')
        context.update({"ales": ale_qrtset,
                        "ale_experiment_name": exp_name,
                        "ale_no": ale_number,
                        "ale_experiment_id": ale_experiment_id,
                        "table_body": mark_safe(table_body),
                        "title": exp_name + " Enrichment Mutations",
                        "table_header": mark_safe(table_header),
                        "template_header": "Enrichment Mutations",
                        "hidden_columns": hidden_columns,
                        "experiments": get_all_ale_exps(request.user),
                        "recent_experiments": get_recent_ale_exps(int(ale_experiment_id)),
                        "sorted_column": POSITION_COLUMN_IN_ENRICH_OR_FIXED_MUT_TABLE,
                        "tag_dropdown": common.constants.TAGS
                        })
        performance_lgr.info("enrichment performance",
                             extra=join_extras(user_extra(request), {"time taken": time.clock() - start_time}))

        return HttpResponse(template.render(context, request), content_type="text/html")
    except Exception as e:
        exception_lgr.exception("stats broke", extra=user_extra(request))
        template = loader.get_template("500.html")
        context['err_message'] = str(e)
        return HttpResponse(template.render(context, request), content_type="text/html")


def _get_table_body(reseq_dict, experiment, user):
    exp_id = experiment.ale_id
    obs_mut_qryset = get_enrich_obs_mut_qryset(reseq_dict)
    return mutation_table_builder.get_table_body(user=user,
                                                 reseq_dict=reseq_dict,
                                                 observed_mutations_queryset=obs_mut_qryset,
                                                 ale_experiment_id=exp_id,
                                                 table_type=mutation_table_builder.TableType.ENRICHMENT_MUTATIONS)
