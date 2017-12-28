from django.http import HttpResponse
from django.template import loader
from django.utils.safestring import mark_safe
from common.util import get_all_ale_exps, get_recent_ale_exps
import seq.views.common
from seq.views import mutation_table_builder  # TODO: The mutation table build should use the factory pattern.
from enrichment.models import EnrichmentMutation
from common.util import check_hidden_columns_and_filters
from combine.views.common import get_ordered_reseq_dict_and_obs_mut_queryset, get_ales_from_ale_experiment_list
from common.constants import POSITION_COLUMN_IN_ENRICH_OR_FIXED_MUT_TABLE, TAGS
import json
from django.core.serializers.json import DjangoJSONEncoder

HTML_MUTATION_TABLE_HEADER = """<tr><td></td><td>Position</td><td>Mutation Type</td><td>Sequence Change</td><td>Gene</td><td>Function</td><td>Product</td><td>GO Process</td><td>GO Component</td><td>Details</td>"""

__author__ = 'Patrick Phaneuf, Denny Gosting'


def combined_enrichment_mutations(request):

    ale_no = seq.views.common.get_ale_id(request)

    ale_experiment_string_list = request.GET.get('ale_experiment_id', None).replace(" ", "").replace('[', '').replace(
        ']', '').split(',')

    ale_experiment_list = [int(exp_id) for exp_id in ale_experiment_string_list]

    ordered_reseq_dict, queryset = get_ordered_reseq_dict_and_obs_mut_queryset(ale_experiment_list, ale_no)

    table_header = mutation_table_builder.get_table_header(reseq_dict=ordered_reseq_dict,
                                                           table_type=mutation_table_builder.TableType.ENRICHMENT_MUTATIONS)

    table_body = _get_table_body(request, ordered_reseq_dict, ale_experiment_list, queryset)

    hidden_columns = check_hidden_columns_and_filters(request, None)

    template = loader.get_template('base_table_template.html')
    context = {"ales": get_ales_from_ale_experiment_list(ale_experiment_list),
               "ale_no": ale_no,
               "table_body": mark_safe(json.dumps(table_body, cls=DjangoJSONEncoder)),
               "experiment_id": ale_experiment_list,
               "title": "Enrichment Mutation",
               "table_header": mark_safe(table_header),
               "template_header": "Enrichment Mutations",
               "hidden_columns": hidden_columns,
               "experiments": get_all_ale_exps(),
               "recent_experiments": get_recent_ale_exps(),
               "sorted_column": POSITION_COLUMN_IN_ENRICH_OR_FIXED_MUT_TABLE,
               "tag_dropdown": TAGS
               }

    return HttpResponse(template.render(context, request), content_type="text/html")


def _get_table_body(request, reseq_dict, ale_experiment_list, queryset):

    enrichment_mutation_queryset = EnrichmentMutation.objects.filter(ale_experiment_id__in=ale_experiment_list)

    observed_mutations_queryset = _get_observed_enrichment_mutations(enrichment_mutation_queryset, queryset)

    return mutation_table_builder.get_table_body(request, reseq_dict=reseq_dict,
                                                 observed_mutations_queryset=observed_mutations_queryset,
                                                 table_type=mutation_table_builder.TableType.COMBINE_ENRICHEMENT_MUTATIONS)


# TODO: refactor
def _get_observed_enrichment_mutations(enrichment_mutation_queryset, queryset):

    enrichment_mutation_id_list = []
    for enrichment_mutation in enrichment_mutation_queryset:
        enrichment_mutation_id_list.append(enrichment_mutation.mutation_id)

    enrichment_mutation_observed_mutation_queryset = queryset.filter(mutation_id__in=enrichment_mutation_id_list)

    return enrichment_mutation_observed_mutation_queryset
