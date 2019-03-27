import time
from django.http import HttpResponse
from django.template import loader
from django.utils.safestring import mark_safe
from common.util import get_user_context
from seq.util import get_reseq_ordered_dict
import seq.views.common
from seq.views import mutation_table_builder  # TODO: The mutation table build should use the factory pattern.
from common.constants import \
    REQUEST_MUTATION_ID, \
    POSITION_COLUMN_IN_ENRICH_OR_FIXED_MUT_TABLE
from common.util import check_hidden_columns_and_filters
import common.constants
from converge.util import get_converge_obs_mut_qryset
from logs.aledb_logger import user_extra, join_extras
import logging

logger = logging.getLogger(__name__)
__author__ = 'Patrick Phaneuf'


def converge_mutations(request):
    logger.info("converge usage", extra = user_extra(request))

    try:
        start_time = time.clock()
        context = get_user_context(request.user)
        experiment = seq.views.common.get_ale_experiment(request)

        exp_name = experiment.project.name + ": " + experiment.name
        ale_experiment_id = experiment.ale_id
        ale_number = seq.views.common.get_ale_id(request)
        ale_qrtset = seq.views.common.get_aleid_ale_id_list(ale_experiment_id, True)

        reseq_ordered_dict = get_reseq_ordered_dict(ale_experiment_id, ale_number, request)

        table_header = mutation_table_builder.get_table_header(request.user, reseq_dict=reseq_ordered_dict)

        table_body = _get_table_body(reseq_ordered_dict, experiment, request.user)

        hidden_columns = check_hidden_columns_and_filters(request, ale_experiment_id)

        template = loader.get_template('base_table_template.html')

        context.update({"ales": ale_qrtset,
                        "ale_experiment_name": exp_name,
                        "ale_no": ale_number,
                        "ale_experiment_id": ale_experiment_id,
                        "table_body": mark_safe(table_body),
                        "table_header": mark_safe(table_header),
                        "template_header": "Converged Mutations",
                        "hidden_columns": hidden_columns,
                        "sorted_column": POSITION_COLUMN_IN_ENRICH_OR_FIXED_MUT_TABLE,
                        "tag_dropdown": common.constants.TAGS
                        })
        logger.info("converge performance",
                             extra=join_extras(user_extra(request), {"time taken": time.clock() - start_time}))

        return HttpResponse(template.render(context, request), content_type="text/html")
    except Exception as e:
        logger.exception("stats broke", extra=user_extra(request))
        template = loader.get_template("500.html")
        context['err_message'] = str(e)
        return HttpResponse(template.render(context, request), content_type="text/html")


# TODO: refactor
def _get_table_body(reseq_dict, experiment, user):
    obs_mut_qryset = get_converge_obs_mut_qryset(experiment.ale_id)
    return mutation_table_builder.get_table_body(user=user,
                                                 reseq_dict=reseq_dict,
                                                 observed_mutations_queryset=obs_mut_qryset,
                                                 ale_experiment=experiment)
