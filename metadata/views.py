import time

from django.http import HttpResponse

from django.template import loader

from django.conf import settings

from seq.views import common

from common.util import get_ordered_reseq_queryset, common_context, get_recent_ale_exps

from common.constants import REQUEST_ALE_EXPERIMENT_ID, REQUEST_ALE_ID
from logs.aledb_logger import get_logger, user_extra, join_extras

exception = get_logger("exceptions")
usage = get_logger("usage")
performance = get_logger("performance")
__author__ = 'Patrick Phaneuf'

# TODO: use the template location described within settings.py
META_DATA_TEMPLATE = "metadata/index.html"


# TODO: used by multiple views. Also implemented within ale_exp_filter.py; implement in one location.
if hasattr(settings, "SEQUENCING_URL"):
    reseq_report_url = settings.SEQUENCING_URL
else:
    reseq_report_url = common.DEFAULT_RESEQ_REPORT_URL


def metadata(request):
    usage.info("fixation", extra=user_extra(request))

    try:
        start_time = time.clock()
        ale_experiment_id = request.GET.get(REQUEST_ALE_EXPERIMENT_ID)
        ale_id = request.GET.get(REQUEST_ALE_ID)
        reseq_queryset = get_ordered_reseq_queryset(ale_experiment_id, ale_id)

        # Would rather want to use something like a dictionary since an experiment is
        # unique, though an experiment is currently a structure and an integral type
        # that can be used as a key.

        reseq_info_list = get_reseq_info_list(reseq_queryset)

        template = loader.get_template(META_DATA_TEMPLATE)

        ale_experiment_name = common.get_ale_experiment_name(request)

        context = common_context.copy()
        context.update({"reseq_info_list": reseq_info_list,
                   "reseq_report_url": reseq_report_url,
                   "ale_experiment_name": ale_experiment_name,
                   "recent_experiments": get_recent_ale_exps(int(ale_experiment_id)),
                   "multiple": False,
                   "ale_experiment_id": ale_experiment_id
                   })

        performance.info("metadata performance", extra=join_extras(user_extra(request), {"time taken": time.clock()-start_time}))

        return HttpResponse(template.render(context, request), content_type="text/html")
    except Exception:
        exception.exception("metadata broke", extra=user_extra(request))


def get_reseq_info_list(reseq_queryset):

    reseq_info_list = []

    for reseq in reseq_queryset:

        clonal_or_population = "clonal"
        if reseq.tech_rep.isolate.is_population:
            clonal_or_population = "population"

        experiment_info_tuple = (reseq,
                                 clonal_or_population,
                                 reseq.tech_rep.isolate.flask.media.temperature,
                                 reseq.tech_rep.isolate.flask.media.description,
                                 reseq.tech_rep.isolate.flask.media.substrate,
                                 reseq.tech_rep.isolate.flask.ale_id.strain,
                                 reseq.tech_rep.isolate.flask.ale_id.description,
                                 reseq.tech_rep.isolate.library_prep,
                                 reseq.tech_rep.isolate.reseq_reference,
                                 reseq.tech_rep.isolate.breseq_version,
                                 reseq.tech_rep.isolate.reseq_date,
                                 reseq.tech_rep.isolate.flask.ale_id.ale_experiment.name,
                                 reseq.tech_rep.description)

        reseq_info_list.append(experiment_info_tuple)

    return reseq_info_list
