#TODO now that we can execute unit tests on code that involves django resources, bring all implementations with common.db_util into this file.

from common.constants import REQUEST_ALL

from filter.models import AleExperimentFilter
from filter.util import get_global_filter

import common.db_util


def get_ale_experiment_selector(ale_experiment_id, reseq_query):

    if ale_experiment_id is None or ale_experiment_id == REQUEST_ALL:

        return reseq_query

    else:

        return reseq_query.filter(tech_rep__isolate__flask__ale_id__ale_experiment__ale_id=ale_experiment_id)


def get_ale_number_selector(ale_id, reseq_query):

    if ale_id is None or ale_id == REQUEST_ALL:

        return reseq_query

    else:

        return reseq_query.filter(tech_rep__isolate__flask__ale_id__ale_id=ale_id)


def check_hidden_columns_and_filters(request, ale_experiment_id):

    if request.method == "GET":
        hidden_columns = request.GET.get('hidden_columns', "5,6,7,8")
    else:
        hidden_columns = ""
        save_method = request.POST.get('save_method')
        mut_id = request.POST.get('mut_id')

        if save_method == 'global':

            common.db_util.clear_dashboard_cache()
            global_filter = get_global_filter()

            global_filter_ignored_mutations = global_filter.ignored_mutations

            global_filter_ignored_mutations += "," + mut_id

            global_filter.ignored_mutations = global_filter_ignored_mutations

            global_filter.save()

        elif save_method == 'experiment' and ale_experiment_id is not None:

            common.db_util.clear_dashboard_cache()

            ale_exp_filter, created = AleExperimentFilter.objects.get_or_create(ale_experiment_id=ale_experiment_id)

            ignored_mutations = ale_exp_filter.ignored_mutations

            ignored_mutations += "," + mut_id

            ale_exp_filter.ignored_mutations = ignored_mutations

            ale_exp_filter.save()

    return hidden_columns
