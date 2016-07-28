from django.http import HttpResponse

from django.contrib.auth.decorators import login_required

from django.template import Context, loader

from django.utils.safestring import mark_safe

import ale.common

import ale.models

import seq.models

import seq.views.common

from seq.views import mutation_table_builder

from seq.views import meta_data

__author__ = 'Patrick Phaneuf'

REQUEST_MUTATION_ID = "mutation_id"


@login_required
def key_mutations(request):

    ale_experiment_id = seq.views.common.get_ale_experiment_id(request)

    ale_experiment_name = seq.views.common.get_ale_experiment_name(request)

    ale_number = seq.views.common.get_ale_id(request)

    ale_queryset = seq.views.common.get_ales(ale_experiment_id, True)

    ordered_reseq_dict = seq.views.common.get_ordered_reseq_dict(request)
    ordered_reseq_dict = seq.views.common.filter_out_wt_reseq(ordered_reseq_dict)
    ordered_reseq_dict = mutation_table_builder.filter_checked_flasks(request, ordered_reseq_dict)

    table_header = mutation_table_builder.get_table_header(ordered_reseq_dict)

    table_body = _get_table_body(ordered_reseq_dict, request)

    template = loader.get_template("hot_gene_mutations/hot_gene_mutations.html")
    context = Context({"ales": ale_queryset,
                       "ale_experiment_name": ale_experiment_name,
                       "ale_no": ale_number,
                       "experiment_id": ale_experiment_id,
                       "table_body": mark_safe(table_body),
                       "title": "Frequently Mutated Genes",
                       "table_header": mark_safe(table_header),
                       "template_header": "Frequently Mutated Genes"})

    return HttpResponse(template.render(context))


# TODO: needs to be refactored
@login_required
def shared_hot_gene_mutations(request):

    mutation_id = request.GET.get(REQUEST_MUTATION_ID)

    key_mutation_queryset = ale.models.KeyMutation.objects.filter(mutation_id=mutation_id)
    mutation_id_list = [key_mutation.mutation_id for key_mutation in key_mutation_queryset]
    # mutation_queryset = seq.models.Mutation.objects.filter(id__in=mutation_id_list)
    key_mutataion_list = [key_mutation.mutation for key_mutation in key_mutation_queryset]

    table_header = mutation_table_builder.HTML_MUTATION_TABLE_HEADER
    key_mutation = key_mutataion_list[0]  # Should only be 1 key mutation
    table_body = "<tr>"
    table_body += mutation_table_builder.HTML_MUTATION_TABLE_ROW
    table_body += "<td>%s</td>" % key_mutation.position
    table_body += "<td>%s</td>" % key_mutation.mutation_type
    table_body += "<td>%s</td>" % key_mutation.sequence_change
    table_body += "<td><a href=/ale_analytics/gene?g=%s>%s</a></td>" % (key_mutation.gene, key_mutation.gene)
    table_body += "<td>%s</td>" % key_mutation.protein_change
    table_body += "</tr>"

    # Get the reseq's that are part of the ALE experiments from the key_mutation_queryset
    key_mutation_ale_exp_list = [key_mutation.ale_experiment for key_mutation in key_mutation_queryset]
    all_reseq_queryset = seq.models.ResequencingExperiment.objects.all()
    ale_experiment_reseq_list = []
    for reseq in all_reseq_queryset:
        if reseq.ale_experiment in key_mutation_ale_exp_list:
            ale_experiment_reseq_list.append(reseq)

    # filter reseq for only those that contain key mutation
    observed_mutation_queryset = seq.models.ObservedMutation.objects.filter(sequencing_experiment__in=ale_experiment_reseq_list)
    key_mutation_reseq_list = []
    for observed_mutation in observed_mutation_queryset:
        if observed_mutation.mutation in key_mutataion_list:
            key_mutation_reseq_list.append(observed_mutation.sequencing_experiment)

    reseq_info_list = meta_data.get_reseq_info_list(key_mutation_reseq_list)

    template = loader.get_template("hot_gene_mutations/shared_hot_gene_mutations.html")
    context = Context({"title": "Shared Frequently Mutated Genes",
                       "table_header": mark_safe(table_header),
                       "table_body": mark_safe(table_body),
                       "reseq_info_list": reseq_info_list})

    return HttpResponse(template.render(context))


def _get_table_body(reseq_dict, request):

    ale_experiment_id = seq.views.common.get_ale_experiment_id(request)

    key_mutation_queryset = ale.models.KeyMutation.objects.filter(ale_experiment_id=ale_experiment_id)

    observed_mutations_query_set = _get_observed_key_mutations(reseq_dict, key_mutation_queryset)

    return mutation_table_builder.get_table_body(reseq_dict, observed_mutations_query_set)


def _get_observed_key_mutations(reseq_dict, key_mutation_queryset):

    # 2 filters for the queryset:
    # 1) get observed_mutations that are contained within the seq_experiment_dict,
    # 2) get observed_mutations that reference to the key_mutation_queryset
    # TODO: refactor

    observed_mutation_queryset = seq.models.ObservedMutation.objects.filter(sequencing_experiment_id__in=reseq_dict.keys())

    key_mutation_id_list = []
    for key_mutation in key_mutation_queryset:
        key_mutation_id_list.append(key_mutation.mutation_id)

    key_mutation_observed_mutation_queryset = observed_mutation_queryset.filter(mutation_id__in=key_mutation_id_list)

    return key_mutation_observed_mutation_queryset
