from django.http import HttpResponse
from django.template import loader
from django.utils.safestring import mark_safe
from common.util import get_reseq_ordered_dict, get_all_ale_experiments, get_recent_experiments
import seq.views.common
from seq.views import mutation_table_builder  # TODO: The mutation table build should use the factory pattern.
from seq.models import ObservedMutation
from seq.models import ResequencingExperiment
import metadata.views
from enrichment.models import EnrichmentMutation
from common.constants import \
    REQUEST_MUTATION_ID, \
    REQUEST_ALE_EXPERIMENT_ID, \
    POSITION_COLUMN_IN_SHARED_MUTATION_TABLE, \
    POSITION_COLUMN_IN_ENRICH_OR_FIXED_MUT_TABLE
from common.util import check_hidden_columns_and_filters
from collections import OrderedDict
from django.core.serializers.json import DjangoJSONEncoder
import json
from genes.util import get_gene_list
import operator
from functools import reduce
from django.db.models import Q
import common.constants

HTML_MUTATION_TABLE_HEADER = """<tr><td></td><td>Position</td><td>Mutation Type</td><td>Sequence Change</td><td>Gene</td><td>Function</td><td>Product</td><td>GO Process</td><td>GO Component</td><td>Protein change</td>"""

__author__ = 'Patrick Phaneuf'


def enrichment_mutations(request):

    ale_experiment_id = seq.views.common.get_ale_experiment_id(request)

    ale_experiment_name = seq.views.common.get_ale_experiment_name(request)

    ale_number = seq.views.common.get_ale_id(request)

    ale_queryset = seq.views.common.get_ales(ale_experiment_id, True)

    ale_experiment_id = request.GET.get(REQUEST_ALE_EXPERIMENT_ID)
    ordered_reseq_dict = get_reseq_ordered_dict(ale_experiment_id, ale_number, request)
    ordered_reseq_dict = seq.views.common.filter_out_wt_reseq(ordered_reseq_dict)

    table_header = mutation_table_builder.get_table_header(reseq_dict=ordered_reseq_dict,
                                                           table_type=mutation_table_builder.TableType.ENRICHMENT_MUTATIONS)

    table_body = _get_table_body(ordered_reseq_dict, request)

    hidden_columns = check_hidden_columns_and_filters(request, ale_experiment_id)

    template = loader.get_template('base_table_template.html')
    context = {"ales": ale_queryset,
               "ale_experiment_name": ale_experiment_name,
               "ale_no": ale_number,
               "experiment_id": ale_experiment_id,
               "table_body": mark_safe(table_body),
               "title": "Enrichment Mutations",
               "table_header": mark_safe(table_header),
               "template_header": "Enrichment Mutations",
               "hidden_columns": hidden_columns,
               "experiments": get_all_ale_experiments(),
               "recent_experiments": get_recent_experiments(int(ale_experiment_id)),
               "sorted_column": POSITION_COLUMN_IN_ENRICH_OR_FIXED_MUT_TABLE,
               "tag_dropdown": common.constants.TAGS
               }

    return HttpResponse(template.render(context))


def shared_enriched_genes(request):
    mutation_id = request.GET.get(REQUEST_MUTATION_ID)
    selected_enrichment_mutation_queryset = EnrichmentMutation.objects.filter(mutation_id=mutation_id)
    enrichment_mutation = selected_enrichment_mutation_queryset[0]  # Should only be one enrichment mutation per mutation_id
    enriched_gene_str = enrichment_mutation.mutation.gene
    enriched_gene_list = get_gene_list(enriched_gene_str)

    shared_enriched_gene_query = reduce(operator.or_, (Q(mutation__gene__contains=gene) for gene in enriched_gene_list))
    enrichment_mutation_queryset = EnrichmentMutation.objects.filter(shared_enriched_gene_query)

    enrichment_mutation_ale_experiment_list = []
    for en_mut in enrichment_mutation_queryset:
        enrichment_mutation_ale_experiment_list.append(en_mut.ale_experiment)

    observed_mutation_queryset = ObservedMutation.objects.filter(mutation__in=enrichment_mutation_queryset.values('mutation'))
    observed_mutation_queryset = observed_mutation_queryset.filter(sequencing_experiment__tech_rep__isolate__flask__ale_id__ale_experiment__in=enrichment_mutation_ale_experiment_list)

    ordered_reseq_queryset = ResequencingExperiment.objects.all().order_by(
        'tech_rep__isolate__flask__ale_id__ale_experiment__name',
        'tech_rep__isolate__flask__ale_id__ale_id',
        'tech_rep__isolate__flask__flask_number',
        'tech_rep__isolate__isolate_number')

    ordered_reseq_queryset = ordered_reseq_queryset.filter(id__in=observed_mutation_queryset.values('sequencing_experiment'))

    ordered_reseq_dict = OrderedDict((reseq.id, reseq) for reseq in ordered_reseq_queryset)
    table_header = mutation_table_builder.get_table_header(ordered_reseq_dict)

    table_body = mutation_table_builder.get_table_body(ordered_reseq_dict,
                                                       observed_mutation_queryset,
                                                       table_type=mutation_table_builder.TableType.SHARED)

    reseq_info_list = metadata.views.get_reseq_info_list(ordered_reseq_queryset)

    check_hidden_columns_and_filters(request, None)

    template = loader.get_template("enrichment/shared_enrichment_mutations.html")
    context = {"title": "Shared Enriched Genes",
               "table_header": mark_safe(table_header),
               "table_body": mark_safe(json.dumps(table_body, cls=DjangoJSONEncoder)),
               "reseq_info_list": reseq_info_list,
               "experiments": get_all_ale_experiments(),
               "recent_experiments": get_recent_experiments(),
               "sorted_column": POSITION_COLUMN_IN_SHARED_MUTATION_TABLE}

    return HttpResponse(template.render(context))


def _get_table_body(reseq_dict, request):

    ale_experiment_id = seq.views.common.get_ale_experiment_id(request)

    enrichment_mutation_queryset = EnrichmentMutation.objects.filter(ale_experiment_id=ale_experiment_id)

    observed_mutations_queryset = _get_observed_enrichment_mutations(reseq_dict, enrichment_mutation_queryset)

    return mutation_table_builder.get_table_body(reseq_dict=reseq_dict,
                                                 observed_mutations_queryset=observed_mutations_queryset,
                                                 ale_experiment_id=ale_experiment_id,
                                                 table_type=mutation_table_builder.TableType.ENRICHMENT_MUTATIONS)


# TODO: refactor
def _get_observed_enrichment_mutations(reseq_dict, enrichment_mutation_queryset):

    observed_mutation_queryset = ObservedMutation.objects.filter(sequencing_experiment_id__in=reseq_dict.keys())

    enrichment_mutation_id_list = []
    for enrichment_mutation in enrichment_mutation_queryset:
        enrichment_mutation_id_list.append(enrichment_mutation.mutation_id)

    enrichment_mutation_observed_mutation_queryset = observed_mutation_queryset.filter(mutation_id__in=enrichment_mutation_id_list)

    return enrichment_mutation_observed_mutation_queryset
