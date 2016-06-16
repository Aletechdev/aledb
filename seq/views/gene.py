from django.http import HttpResponse

from django.utils.safestring import mark_safe

from django.contrib.auth.decorators import login_required

from django.template import Context, loader

import seq.models

import seq.views.common


@login_required
def gene(request):
    gene_query = request.GET['g']

    seq_experiment_dict, observed_mutations_with_gene_query_set = _get_seq_exp(request, gene_query)

    table_header = seq.views.common.get_table_header(seq_experiment_dict)

    table_body = seq.views.common.get_table_body(seq_experiment_dict, observed_mutations_with_gene_query_set, request)

    template = loader.get_template("gene.html")

    context = Context({"gene_name": gene_query,
                       "table_body": mark_safe(table_body),
                       "title": gene_query + " gene",
                       "table_header": mark_safe(table_header)})

    return HttpResponse(template.render(context))


# TODO: This is the same implementation as found within seq.views.search.py; need to consolidate.
def _get_seq_exp(request, mutated_gene):

    isolates_to_remove_id_list = []
    isolates_to_remove_string = request.GET.get(seq.views.common.EXPERIMENT_MAPPING_FILTERING_REMOVE_FLAG)
    if isolates_to_remove_string is not None:
        isolates_to_remove_ids = isolates_to_remove_string.encode('latin_1').replace("{", "").replace("}", "")
        isolates_to_remove_id_list = [int(i) for i in isolates_to_remove_ids.split(",") if i != ""]

    isolates_to_show_id_list = []
    isolates_to_show_string = request.GET.get(seq.views.common.EXPERIMENT_MAPPING_FILTERING_SHOW_FLAG)
    if isolates_to_show_string is not None:
        isolates_to_show_ids = isolates_to_show_string.encode('latin_1').replace("{", "").replace("}", "")
        isolates_to_show_id_list = [int(i) for i in isolates_to_show_ids.split(",") if i != ""]

    mutations_with_gene = seq.models.Mutation.objects.filter(gene=mutated_gene)

    observed_mutations_with_gene = seq.models.ObservedMutation.objects.filter(mutation=mutations_with_gene)

    seq_experiment_dict = {}

    for observed_mutation in observed_mutations_with_gene:

        if observed_mutation.sequencing_experiment.id not in isolates_to_remove_id_list\
            or observed_mutation.sequencing_experiment.id in isolates_to_remove_id_list\
                and observed_mutation.sequencing_experiment.id in isolates_to_show_id_list:

            seq_experiment_dict[observed_mutation.sequencing_experiment.id] = observed_mutation.sequencing_experiment

    return seq_experiment_dict, observed_mutations_with_gene