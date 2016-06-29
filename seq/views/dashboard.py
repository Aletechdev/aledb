__author__ = 'pphaneuf'


from django.contrib.auth.decorators import login_required

from django.template import Context, loader

from django.http import HttpResponse

from seq.views import common

import seq.models

from django.db.models import Count

from django.utils.safestring import mark_safe

import re

from django import forms


DASHBOARD_TEMPLATE = "dashboard.html"

COLORS = ['red', 'black', 'blue', 'green', 'orange', 'grey', 'purple', 'olive', 'maroon']
DEFAULT_COLOR = 'steelblue'


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

    genes = seq.models.ObservedMutation.objects.values('mutation__gene', 'mutation__mutation_type').annotate(the_count=Count('mutation__gene')).order_by('-the_count')
    sequence_changes = seq.models.ObservedMutation.objects.values('mutation__gene', 'mutation__protein_change').annotate(the_count=Count('mutation__gene')).order_by('-the_count')

    mutation_types = common.MUTATION_TYPE_LIST
    protein_types = common.PROTEIN_CHANGE_TYPE_LIST

    gene_colors = COLORS[:len(mutation_types)]
    seq_colors = COLORS[:len(protein_types)]

    ignored_genes = request.GET.get('ignored_genes')
    gene_list = None
    if ignored_genes is not None:
        ignored_genes = ignored_genes.replace(" ", "").split(',')
        gene_list = ', '.join(ignored_genes)
        if len(ignored_genes) > 0:
            for g in ignored_genes:
                print ("excluding")
                genes = genes.exclude(mutation__gene__contains=g)

    for gene in genes:
        if gene['mutation__mutation_type'] in mutation_types:
            gene['color'] = COLORS[mutation_types.index(gene['mutation__mutation_type'])]
        else:
            gene['color'] = DEFAULT_COLOR

    for seq_change in sequence_changes:
        seq_change['mutation__protein_change'] = re.compile(r'<[^>]+>').sub('', seq_change['mutation__protein_change'])
        has_match = False
        for protein in protein_types:
            if protein in seq_change['mutation__protein_change']:
                seq_change['color'] = COLORS[protein_types.index(protein)]
                has_match = True
                break
        if has_match is False:
            seq_change['color'] = DEFAULT_COLOR

    if 'number_of_top_genes' in request.GET:

        gene_query = request.GET['number_of_top_genes']

        if _is_query_empty(gene_query):
            genes_to_show = list(genes[:20])
            sequence_changes_to_show = list(sequence_changes[:20])

        else:
            genes_to_show = list(genes[:int(request.GET['number_of_top_genes'])])
            sequence_changes_to_show = list(sequence_changes[:int(request.GET['number_of_top_genes'])])

    else:
        genes_to_show = list(genes[:20])
        sequence_changes_to_show = list(sequence_changes[:20])

    context = Context({"protein_change_type_count_dict": protein_change_type_count_dict,
                       "mutation_type_count_dict": mutation_type_count_dict,
                       "genes": mark_safe(genes_to_show),
                       "sequence_changes": mark_safe(sequence_changes_to_show),
                       "gene_color_set": mark_safe(gene_colors),
                       "seq_color_set": mark_safe(seq_colors),
                       "mutation_types": mark_safe(mutation_types),
                       "protein_types": mark_safe(protein_types),
                       "Ignored_Gene_Form": IgnoredGenesForm({"ignored_genes": gene_list})})


    template = loader.get_template(DASHBOARD_TEMPLATE)
    return HttpResponse(template.render(context))


def _is_query_empty(query):

    is_query_empty = False

    if not query:

        is_query_empty = True

    return is_query_empty


class IgnoredGenesForm(forms.Form):
    ignored_genes = forms.CharField(widget=forms.Textarea, required=False)