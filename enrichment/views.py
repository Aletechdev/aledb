from django.http import HttpResponse

from django.contrib.auth.decorators import login_required

from django.template import loader

from django.utils.safestring import mark_safe

import seq.models

import seq.views.common

from common.db_util import get_ordered_reseq_dict

# TODO: The mutation table build should use the factory pattern.
from seq.views import mutation_table_builder

import metadata.views

from enrichment.models import EnrichmentMutation

from common.constants import REQUEST_MUTATION_ID

__author__ = 'Patrick Phaneuf'


@login_required
def enrichment_mutations(request):

    ale_experiment_id = seq.views.common.get_ale_experiment_id(request)

    ale_experiment_name = seq.views.common.get_ale_experiment_name(request)

    ale_number = seq.views.common.get_ale_number(request)

    ale_queryset = seq.views.common.get_ales(ale_experiment_id, True)

    ordered_reseq_dict = get_ordered_reseq_dict(request)
    ordered_reseq_dict = seq.views.common.filter_out_wt_reseq(ordered_reseq_dict)
    ordered_reseq_dict = mutation_table_builder.filter_checked_flasks(request, ordered_reseq_dict)

    table_header = mutation_table_builder.get_table_header(reseq_dict=ordered_reseq_dict,
                                                           table_type=mutation_table_builder.TableType.ENRICHMENT_MUTATIONS)

    table_body = _get_table_body(ordered_reseq_dict, request)

    template = loader.get_template("enrichment/enrichment_mutations.html")
    context = {"ales": ale_queryset,
                       "ale_experiment_name": ale_experiment_name,
                       "ale_no": ale_number,
                       "experiment_id": ale_experiment_id,
                       "table_body": mark_safe(table_body),
                       "title": "Frequently Mutated Genes",
                       "table_header": mark_safe(table_header),
                       "template_header": "Frequently Mutated Genes"}

    return HttpResponse(template.render(context))


# TODO: needs to be refactored. Currently has poor performance. Should use queryset to filter instead of for loops.
@login_required
def shared_enrichment_mutations(request):

    mutation_id = request.GET.get(REQUEST_MUTATION_ID)

    enrichment_mutation_queryset = EnrichmentMutation.objects.filter(mutation_id=mutation_id)
    # mutation_id_list = [enrichment_mutation.mutation_id for enrichment_mutation in enrichment_mutation_queryset]
    # mutation_queryset = seq.models.Mutation.objects.filter(id__in=mutation_id_list)
    enrichment_mutation_list = [enrichment_mutation.mutation for enrichment_mutation in enrichment_mutation_queryset]

    table_header = mutation_table_builder.HTML_MUTATION_TABLE_HEADER
    enrichment_mutation = enrichment_mutation_list[0]  # Should only be 1 enrichment mutation
    table_body = "<tr>"
    table_body += mutation_table_builder.HTML_MUTATION_TABLE_ROW
    table_body += "<td>%s</td>" % enrichment_mutation.position
    table_body += "<td>%s</td>" % enrichment_mutation.mutation_type
    table_body += "<td>%s</td>" % enrichment_mutation.sequence_change
    table_body += "<td><a href=/ale_analytics/gene?g=%s>%s</a></td>" % (enrichment_mutation.gene, enrichment_mutation.gene)
    table_body += "<td>%s</td>" % ("" if enrichment_mutation.function is None else enrichment_mutation.function)
    table_body += "<td>%s</td>" % ("" if enrichment_mutation.product is None else enrichment_mutation.product)
    table_body += "<td>%s</td>" % ("" if enrichment_mutation.go_process is None else enrichment_mutation.go_process)
    table_body += "<td>%s</td>" % ("" if enrichment_mutation.go_component is None else enrichment_mutation.go_component)
    table_body += "<td>%s</td>" % enrichment_mutation.protein_change
    table_body += "</tr>"

    # Get the reseq's that are part of the ALE experiments from the enrichment_mutation_queryset
    enrichment_mutation_ale_exp_list = [enrichment_mutation.ale_experiment for enrichment_mutation in enrichment_mutation_queryset]
    all_reseq_queryset = seq.models.ResequencingExperiment.objects.all()
    ale_experiment_reseq_list = []
    for reseq in all_reseq_queryset:
        if reseq.ale_experiment in enrichment_mutation_ale_exp_list:
            ale_experiment_reseq_list.append(reseq)

    # filter reseq for only those that contain key mutation
    observed_mutation_queryset = seq.models.ObservedMutation.objects.filter(sequencing_experiment__in=ale_experiment_reseq_list)
    enrichment_mutation_reseq_list = []
    for observed_mutation in observed_mutation_queryset:
        if observed_mutation.mutation in enrichment_mutation_list:
            enrichment_mutation_reseq_list.append(observed_mutation.sequencing_experiment)

    reseq_info_list = metadata.views.get_reseq_info_list(enrichment_mutation_reseq_list)

    template = loader.get_template("enrichment/shared_enrichment_mutations.html")
    context = {"title": "Shared Enrichment Mutations",
                       "table_header": mark_safe(table_header),
                       "table_body": mark_safe(table_body),
                       "reseq_info_list": reseq_info_list}

    return HttpResponse(template.render(context))


def _get_table_body(reseq_dict, request):

    ale_experiment_id = seq.views.common.get_ale_experiment_id(request)

    enrichment_mutation_queryset = EnrichmentMutation.objects.filter(ale_experiment_id=ale_experiment_id)

    observed_mutations_queryset = _get_observed_enrichment_mutations(reseq_dict, enrichment_mutation_queryset)

    return mutation_table_builder.get_table_body(reseq_dict=reseq_dict,
                                                 observed_mutations_queryset=observed_mutations_queryset,
                                                 table_type=mutation_table_builder.TableType.ENRICHMENT_MUTATIONS)


# TODO: refactor
def _get_observed_enrichment_mutations(reseq_dict, enrichment_mutation_queryset):

    observed_mutation_queryset = seq.models.ObservedMutation.objects.filter(sequencing_experiment_id__in=reseq_dict.keys())

    enrichment_mutation_id_list = []
    for enrichment_mutation in enrichment_mutation_queryset:
        enrichment_mutation_id_list.append(enrichment_mutation.mutation_id)

    enrichment_mutation_observed_mutation_queryset = observed_mutation_queryset.filter(mutation_id__in=enrichment_mutation_id_list)

    return enrichment_mutation_observed_mutation_queryset
