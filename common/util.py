import subprocess

from filter.models import AleExperimentFilter
import filter.util, logging
from ale.utils import get_all_ale_exps, get_recent_ale_exps
from ale.models import TechnicalReplicate
from seq.models import Mutation
from django.core.cache import cache

__author__ = 'Patrick Phaneuf, Denny Gosting'

logger = logging.getLogger(__name__)

def clear_dashboard_cache():

    cache.delete('dashboard_mutation')

    cache.delete('dashboard_observed_mutation')

    cache.delete('dashboard_bar_chart_gene_dict')


# TODO: This should probably be refactored and split into separate functions
# TODO: The hidden columns functionality no longer seems to be used.
def check_hidden_columns_and_filters(request, ale_experiment_id):
    if request.method == "GET":
        hidden_columns = request.GET.get('hidden_columns', "")
    else:
        hidden_columns = ""
        save_method = request.POST.get('save_method')
        mut_id = request.POST.get('mut_id')

        if save_method == 'global':
            global_filter = filter.util.get_global_filter()
            global_filter_ignored_mutations = global_filter.ignored_mutations
            global_filter_ignored_mutations += "," + mut_id
            global_filter.ignored_mutations = global_filter_ignored_mutations
            global_filter.save()

        elif save_method == 'experiment' and ale_experiment_id is not None:
            ale_exp_filter, created = AleExperimentFilter.objects.get_or_create(ale_experiment_id=ale_experiment_id)
            ignored_mutations = ale_exp_filter.ignored_mutations
            ignored_mutations += "," + mut_id
            ale_exp_filter.ignored_mutations = ignored_mutations
            ale_exp_filter.save()

        elif save_method == 'tag_mut':
            mutation = Mutation.objects.get(id=mut_id)
            if mutation.tags:
                selected_tag = request.POST.get('tag_name')
                tag_list = mutation.tags.split(',')
                if selected_tag in tag_list:
                    tag_list.remove(selected_tag)
                else:
                    tag_list.append(selected_tag)
                mutation.tags = ','.join(tag_list)
            else:
                mutation.tags = request.POST.get('tag_name')
            mutation.save()

        elif save_method == 'tag_rep':
            rep_id = request.POST.get('rep_id')
            replicate = TechnicalReplicate.objects.get(id=rep_id)
            if replicate.tags:
                selected_tag = request.POST.get('tag_name')
                tag_list = replicate.tags.split(',')
                if selected_tag in tag_list:
                    tag_list.remove(selected_tag)
                else:
                    tag_list.append(selected_tag)
                replicate.tags = ','.join(tag_list)
            else:
                replicate.tags = request.POST.get('tag_name')
            replicate.save()
            replicate.save()

    return hidden_columns


def get_git_hash():
    return subprocess.check_output(['git', 'rev-parse', 'HEAD'])

try:
    common_context = {"recent_experiments": get_recent_ale_exps,
                      "git_hash": get_git_hash()}
except Exception:
    logger.exception("common_context broke")


def get_user_context(user):
    context = common_context.copy()
    context.update({"experiments": get_all_ale_exps(user)})
    return context

