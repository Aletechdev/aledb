# TODO: Had to implement this separate from common.util since can't currently run unit tests on modules that refer to models. Fix this

from common.constants import RESEQ_QUERY
from seq.models import ResequencingExperiment
from common.util import get_ale_experiment_selector
from common.util import get_ale_number_selector
import collections

__author__ = 'Patrick Phaneuf'


def get_reseq_queryset(ale_experiment_id, ale_id):
    ale_experiment_selector = get_ale_experiment_selector(ale_experiment_id)
    ale_id_selector = get_ale_number_selector(ale_id)
    sql_query = RESEQ_QUERY % (ale_experiment_selector, ale_id_selector)
    reseq_raw_queryset = ResequencingExperiment.objects.raw(sql_query)
    return reseq_raw_queryset


def get_reseq_dict(ale_experiment_id):
    reseq_queryset = get_reseq_queryset(ale_experiment_id, None)
    reseq_dict = collections.OrderedDict((reseq.id, reseq) for reseq in reseq_queryset)
    return reseq_dict