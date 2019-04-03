import subprocess

from filter.models import AleExperimentFilter
import logging
from ale.models import TechnicalReplicate
import seq.models
from django.core.cache import cache

__author__ = 'Patrick Phaneuf, Denny Gosting'

logger = logging.getLogger(__name__)

def clear_dashboard_cache():

    cache.delete('dashboard_mutation')

    cache.delete('dashboard_observed_mutation')

    cache.delete('dashboard_bar_chart_gene_dict')


def get_git_hash():
    return subprocess.check_output(['git', 'rev-parse', 'HEAD']).rstrip()

try:
    common_context = {"git_hash": get_git_hash()}
except Exception:
    logger.exception("common_context broke")


def get_user_context(user):
    context = common_context.copy()
    # context.update({"experiments": get_all_user_exps(user)})
    return context


def is_int(s):
    try:
        int(s)
        return True
    except ValueError:
        return False
