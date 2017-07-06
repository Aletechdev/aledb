# TODO: All resources being pulled from seq app could possibly be stored in a common dir.
from django.http import HttpResponse
from django.template import loader
from django.utils.safestring import mark_safe
# TODO: seq.views.common.get_ordered_reseq_dict could likely be refactored into common.db_util.get_reseq_dict
import seq.views.common
from seq.views import mutation_table_builder
from fixation.models import FixatedMutation
from common.util import get_all_ale_experiments, get_recent_experiments, check_hidden_columns_and_filters
from compare.views.common import get_ordered_reseq_dict_and_queryset, get_ales_from_ale_experiment_list
from common.constants import POSITION_COLUMN_IN_SHARED_MUTATION_TALBE, TAGS
import json
from django.core.serializers.json import DjangoJSONEncoder

HTML_MUTATION_TABLE_HEADER = """<tr><td></td><td>Position</td><td>Mutation Type</td><td>Sequence Change</td><td>Gene</td><td>Function</td><td>Product</td><td>GO Process</td><td>GO Component</td><td>Protein change</td>"""

__author__ = 'Patrick Phaneuf'

REQUEST_ASCENDING_FREQ_FILTER = 'asndflt'


# TODO: very similar to common_mutations page workflow. Should consolidate somehow.
# TODO: Shares some same functions as fixation.views.py and should be refactored/consolidated
def comparison_fixation(request):

    ale_no = seq.views.common.get_ale_id(request)

    ale_experiment_string_list = request.GET.get('ale_experiment_id', None).replace(" ", "").replace('[', '').replace(
        ']', '').split(',')

    ale_experiment_list = [int(exp_id) for exp_id in ale_experiment_string_list]

    ordered_reseq_dict, queryset = get_ordered_reseq_dict_and_queryset(ale_experiment_list, ale_no)

    is_ascending_freq_filter = _is_ascending_freq_filter(request)

    table_header = mutation_table_builder.get_table_header(ordered_reseq_dict,
                                                           mutation_table_builder.TableType.FIXATING_MUTATIONS)

    observed_mutation_queryset = _get_experiment_fixating_observed_mutation_queryset(ale_experiment_list,
                                                                                     queryset,
                                                                                     is_ascending_freq_filter)

    table_body = mutation_table_builder.get_table_body(reseq_dict=ordered_reseq_dict,
                                                       observed_mutations_queryset=observed_mutation_queryset,
                                                       table_type=mutation_table_builder.TableType.COMPARE_FIXATION_MUTATIONS)

    hidden_columns = check_hidden_columns_and_filters(request, None)

    template = loader.get_template("base_table_template.html")

    context = {"ales": get_ales_from_ale_experiment_list(ale_experiment_list),
               "ale_no": ale_no,
               "experiment_id": ale_experiment_list,
               "table_body": mark_safe(json.dumps(table_body, cls=DjangoJSONEncoder)),
               "title": "Fixating Mutations",
               "table_header": mark_safe(table_header),
               "is_ascending_freq_filter": is_ascending_freq_filter,
               "template_header": "Fixating Mutations",
               "hidden_columns": hidden_columns,
               "experiments": get_all_ale_experiments(),
               "recent_experiments": get_recent_experiments(None),
               "sorted_column": POSITION_COLUMN_IN_SHARED_MUTATION_TALBE,
               "tag_dropdown": TAGS}

    return HttpResponse(template.render(context))


def _is_ascending_freq_filter(request):
    ret_val = False
    if request.GET.get(REQUEST_ASCENDING_FREQ_FILTER) is not None:
        ret_val = True
    return ret_val


def _get_experiment_fixating_observed_mutation_queryset(ale_experiment_list, queryset, is_only_ascending=False):

    fixating_mutation_queryset = FixatedMutation.objects.filter(ale_experiment_id__in=ale_experiment_list)

    # TODO: filter out mutations from samples that were removed from table.

    fixating_observed_mutation_queryset = _get_fixating_observed_mutation_queryset(fixating_mutation_queryset,
                                                                                   queryset)

    if is_only_ascending:
        fixating_observed_mutation_queryset = _filter_for_ascending_freq(fixating_observed_mutation_queryset)

    return fixating_observed_mutation_queryset


def _filter_for_ascending_freq(fixating_observed_mutation_queryset):

    fixated_mutation_freq_dict = {}
    for observed_mutation in fixating_observed_mutation_queryset:
        mutation_id = observed_mutation.mutation.id
        if mutation_id in fixated_mutation_freq_dict.keys():
            fixated_mutation_freq_dict[mutation_id].append(observed_mutation)
        else:
            fixated_mutation_freq_dict[mutation_id] = [observed_mutation]

    mutation_id_exclude_list = _get_descending_freq_mutation_id_list(fixated_mutation_freq_dict)

    fixating_observed_mutation_queryset = fixating_observed_mutation_queryset.exclude(mutation_id__in=mutation_id_exclude_list)

    return fixating_observed_mutation_queryset


# TODO: this can be unit tested.
def _get_descending_freq_mutation_id_list(fixated_mutation_freq_dict):
    mutation_id_exclude_list = []

    for mutation_id, observed_mutation_list in fixated_mutation_freq_dict.items():

        observed_mutation_list = _filter_mutations_from_same_flask(observed_mutation_list)

        observed_mutation_list.sort(key=lambda x: x.sequencing_experiment.flask_number)

        current_observed_mutation_frequency = 0
        for observed_mutation in observed_mutation_list:
            if observed_mutation.frequency >= current_observed_mutation_frequency:
                current_observed_mutation_frequency = observed_mutation.frequency
            else:
                mutation_id_exclude_list.append(mutation_id)
                break

    return mutation_id_exclude_list


# TODO: this can be unit tested.
def _filter_mutations_from_same_flask(observed_mutation_list):

    filtered_observed_mutation_list = []

    same_flask_observed_mutation_dict = {}
    for observed_mutation_idx in range(len(observed_mutation_list)):
        flask_number = observed_mutation_list[observed_mutation_idx].sequencing_experiment.flask_number
        if flask_number in same_flask_observed_mutation_dict.keys():
            same_flask_observed_mutation_dict[flask_number].append(observed_mutation_idx)
        else:
            same_flask_observed_mutation_dict[flask_number] = [observed_mutation_idx]

    for observed_mutation_idx_list in same_flask_observed_mutation_dict.values():

        if len(observed_mutation_idx_list) == 1:
            observed_mutation_idx = observed_mutation_idx_list[0]
            filtered_observed_mutation_list.append(observed_mutation_list[observed_mutation_idx])
        else:
            max_freq_idx = observed_mutation_idx_list[0]  # Default
            max_freq = 0
            for observed_mutation_idx in observed_mutation_idx_list:
                current_freq = observed_mutation_list[observed_mutation_idx].frequency
                if current_freq > max_freq:
                    max_freq = current_freq
                    max_freq_idx = observed_mutation_idx
            filtered_observed_mutation_list.append(observed_mutation_list[max_freq_idx])

    return filtered_observed_mutation_list


def _get_fixating_observed_mutation_queryset(fixating_mutation_queryset, queryset):
    fixating_mutation_id_list = [fixating_mutation.mutation.id for fixating_mutation in fixating_mutation_queryset]
    fixating_observed_mutation_queryset = queryset.filter(mutation_id__in=fixating_mutation_id_list)

    return fixating_observed_mutation_queryset
