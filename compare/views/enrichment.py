from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.template import loader
from django.utils.safestring import mark_safe
from common.db_util import get_all_ale_experiments, get_recent_experiments
import seq.views.common
from seq.views import mutation_table_builder  # TODO: The mutation table build should use the factory pattern.
from enrichment.models import EnrichmentMutation
from common.util import check_hidden_columns_and_filters
from ale.models import AleExperiment
from compare.views.common import get_ordered_reseq_dict_and_queryset
from itertools import chain

HTML_MUTATION_TABLE_HEADER = """<tr><td></td><td>Position</td><td>Mutation Type</td><td>Sequence Change</td><td>Gene</td><td>Function</td><td>Product</td><td>GO Process</td><td>GO Component</td><td>Protein change</td>"""

__author__ = 'Patrick Phaneuf, Denny Gosting'


@login_required
def compared_enrichment_mutations(request):

    first_exp_name = request.GET.get('first_exp', None)

    second_exp_name = request.GET.get('second_exp', None)

    first_exp = AleExperiment.objects.get(name=first_exp_name)

    second_exp = AleExperiment.objects.get(name=second_exp_name)

    ale_experiment_list = [first_exp.ale_id, second_exp.ale_id]

    ordered_reseq_dict, queryset = get_ordered_reseq_dict_and_queryset(ale_experiment_list)

    first_ale_queryset = AleExperiment.objects.get(ale_id=first_exp.ale_id).aleid_set.only("ale_id")

    second_ale_queryset = AleExperiment.objects.get(ale_id=second_exp.ale_id).aleid_set.only("ale_id")

    ale_queryset = list(chain(first_ale_queryset, second_ale_queryset))

    ale_number = seq.views.common.get_ale_number(request)

    table_header = mutation_table_builder.get_table_header(reseq_dict=ordered_reseq_dict,
                                                           table_type=mutation_table_builder.TableType.ENRICHMENT_MUTATIONS)

    table_body = _get_table_body(ordered_reseq_dict, ale_experiment_list, queryset)

    hidden_columns = check_hidden_columns_and_filters(request, None)

    name = "%s and %s" % (first_exp_name, second_exp_name)

    title = "Enrichment Mutation Comparison of %s" % name

    template = loader.get_template('shared_table_template.html')
    context = {"ales": ale_queryset,
               "ale_experiment_name": name,
               "ale_no": ale_number,
               "experiment_id": "%s,%s" % (first_exp.ale_id, second_exp.ale_id),
               "table_body": mark_safe(table_body),
               "title": title,
               "table_header": mark_safe(table_header),
               "template_header": "Enrichment Mutations",
               "hidden_columns": hidden_columns,
               "experiments": get_all_ale_experiments(),
               "recent_experiments": get_recent_experiments()
               }

    return HttpResponse(template.render(context))


def _get_table_body(reseq_dict, ale_experiment_list, queryset):

    enrichment_mutation_queryset = EnrichmentMutation.objects.filter(ale_experiment_id__in=ale_experiment_list)

    observed_mutations_queryset = _get_observed_enrichment_mutations(enrichment_mutation_queryset, queryset)

    return mutation_table_builder.get_table_body(reseq_dict=reseq_dict,
                                                 observed_mutations_queryset=observed_mutations_queryset,
                                                 table_type=mutation_table_builder.TableType.COMPARE_ENRICHEMENT_MUTATIONS)


# TODO: refactor
def _get_observed_enrichment_mutations(enrichment_mutation_queryset, queryset):

    enrichment_mutation_id_list = []
    for enrichment_mutation in enrichment_mutation_queryset:
        enrichment_mutation_id_list.append(enrichment_mutation.mutation_id)

    enrichment_mutation_observed_mutation_queryset = queryset.filter(mutation_id__in=enrichment_mutation_id_list)

    return enrichment_mutation_observed_mutation_queryset
