from django.contrib.auth.decorators import login_required

from django.template import loader

from django.http import HttpResponse

from seq.views import common

import seq.models

from django.db.models import Count

from django.utils.safestring import mark_safe

from filter.mutation_filter import filter_ignored_genes_and_mutations

DEFAULT_IGNORED_MUTATIONS = "[]"

DASHBOARD_TEMPLATE = "dashboard.html"

__author__ = 'pphaneuf'


@login_required
def dashboard(request):
    mutation_type_count_dict = {}
    for mutation_type in common.MUTATION_TYPE_LIST:
        mutation_type_count = seq.models.Mutation.objects.filter(mutation_type=mutation_type).count()
        mutation_type_count_dict[mutation_type] = mutation_type_count

    protein_change_type_count_dict = {}
    for protein_change_type in common.PROTEIN_CHANGE_TYPE_LIST:
        protein_change_count = seq.models.Mutation.objects.filter(protein_change__contains=protein_change_type).count()
        protein_change_type_count_dict[protein_change_type] = protein_change_count

    gene_query = seq.models.ObservedMutation.objects.exclude(mutation__gene='').values('mutation__gene', 'mutation__mutation_type')\
        .annotate(the_count=Count('mutation__gene')).order_by('-the_count')
    sequence_change_query = seq.models.ObservedMutation.objects.exclude(mutation__gene='').values('mutation__gene', 'mutation__protein_change')\
        .annotate(the_count=Count('mutation__gene')).order_by('-the_count')

    # genes, sequence_changes = filter_global_ignored_genes_and_mutations(gene_query, sequence_change_query)

    genes = filter_ignored_genes_and_mutations(gene_query, "", DEFAULT_IGNORED_MUTATIONS)

    sequence_changes = filter_ignored_genes_and_mutations(sequence_change_query, "", DEFAULT_IGNORED_MUTATIONS)

    genes = common.set_gene_bar_chart_colors(genes)

    sequence_changes = common.set_sequence_change_bar_chart_colors(sequence_changes)

    genes_to_show, sequence_changes_to_show, number_of_genes_to_show = common.get_genes_to_show(request, genes,
                                                                                                sequence_changes)
    context = {"protein_change_type_count_dict": protein_change_type_count_dict,
               "mutation_type_count_dict": mutation_type_count_dict,
               "genes": mark_safe(genes_to_show),
               "sequence_changes": mark_safe(sequence_changes_to_show),
               "gene_color_set": mark_safe(common.GENE_COLORS),
               "seq_color_set": mark_safe(common.SEQ_COLORS),
               "mutation_types": mark_safe(common.MUTATION_TYPE_LIST),
               "protein_types": mark_safe(common.PROTEIN_CHANGE_TYPE_LIST),
               "number_of_genes_to_show": number_of_genes_to_show}

    template = loader.get_template(DASHBOARD_TEMPLATE)

    return HttpResponse(template.render(context))
