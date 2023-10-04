import time
from django.shortcuts import render

from seq.views import common
from django.utils.safestring import mark_safe
from common.util import get_user_context
from ale.models import AleExperiment, Project
from dashboard.models import ObservedMutationCounts, UniqueMutationCounts, SampleCounts
from dashboard.timeline_util import get_timeline
from stats.views import get_histogram_item_count
from dashboard.models import BarCharts
from stats.util import MAX_HISTOGRAM_SIZE
from logs.aledb_logger import user_extra, join_extras
import logging

DEFAULT_IGNORED_MUTATIONS = "[]"
DASHBOARD_TEMPLATE = "dashboard/dashboard.html"
__author__ = 'pphaneuf'

logger = logging.getLogger(__name__)


def dashboard(request):
    logger.info("populating dashboard", extra=user_extra(request))

    try:
        start_time = time.time()
        general_count_dict = get_general_count_dict()
        observed_mutation_counts = ObservedMutationCounts.objects.first()
        unique_mutation_counts = UniqueMutationCounts.objects.first()

        if unique_mutation_counts and observed_mutation_counts:
            general_count_dict['observed'] = observed_mutation_counts.total
            general_count_dict['unique'] = unique_mutation_counts.total

        context = get_user_context(request.user)
        context.update({"count_dict": general_count_dict,
                        "unique_mutation_counts": unique_mutation_counts,
                        "observed_mutation_counts": observed_mutation_counts,
                        "timeline": get_timeline()})
        logger.info("dashboard performance", extra=join_extras(user_extra(request), {"time taken": time.time() - start_time}))

        return render(request, DASHBOARD_TEMPLATE, context, content_type="text/html")

    except Exception as e:
        logger.exception(e, extra = user_extra(request))


def get_general_count_dict():
    count_dict = dict()
    count_dict['ale_exp'] = AleExperiment.objects.count()  # No need to filter experiment count.
    count_dict['project'] = Project.objects.count()

    sample_counts = SampleCounts.objects.first()

    if sample_counts:
        count_dict['ale'] = sample_counts.ale_count
        count_dict['flask'] = sample_counts.flask_count
        count_dict['isolate'] = sample_counts.isolate_count
    return count_dict
