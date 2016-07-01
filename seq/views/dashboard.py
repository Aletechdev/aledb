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
MUTATION_TYPES = common.MUTATION_TYPE_LIST
PROTEIN_TYPES = common.PROTEIN_CHANGE_TYPE_LIST
GENE_COLORS = COLORS[:len(MUTATION_TYPES)]
SEQ_COLORS = COLORS[:len(PROTEIN_TYPES)]

MUTATION_TYPES.append('Default')
PROTEIN_TYPES.append('Default')
GENE_COLORS.append(DEFAULT_COLOR)
SEQ_COLORS.append(DEFAULT_COLOR)


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

    ignored_genes = request.GET.get('ignored_genes')
    gene_list = None
    if ignored_genes is not None:
        ignored_genes = ignored_genes.replace(" ", "").replace('\n', '').replace('\r', '').split(',')
        gene_list = ', '.join(ignored_genes)
        if len(ignored_genes) > 0 and ignored_genes[0] is not '':
            for g in ignored_genes:
                if str(g).startswith('*'):
                    genes = genes.exclude(mutation__gene__endswith=str(g)[1:])
                    sequence_changes = sequence_changes.exclude(mutation__gene__endswith=str(g)[1:])
                elif str(g).endswith('*'):
                    genes = genes.exclude(mutation__gene__startswith=str(g)[:-1])
                    sequence_changes = sequence_changes.exclude(mutation__gene__startswith=str(g)[:-1])
                else:
                    genes = genes.exclude(mutation__gene__contains=g)
                    sequence_changes = sequence_changes.exclude(mutation__gene__contains=g)

    for gene in genes:
        if gene['mutation__mutation_type'] in MUTATION_TYPES:
            gene['color'] = COLORS[MUTATION_TYPES.index(gene['mutation__mutation_type'])]
        else:
            gene['color'] = DEFAULT_COLOR

    for seq_change in sequence_changes:
        has_match = False
        for protein in PROTEIN_TYPES:
            if protein in seq_change['mutation__protein_change']:
                seq_change['color'] = COLORS[PROTEIN_TYPES.index(protein)]
                has_match = True
                break
        if has_match is False:
            seq_change['color'] = DEFAULT_COLOR
        seq_change['mutation__protein_change'] = re.compile(r'<[^>]+>').sub('', seq_change['mutation__protein_change'])

    number_of_genes_to_show = 20

    if 'number_of_top_genes' in request.GET:

        gene_query = request.GET['number_of_top_genes']

        if _is_query_empty(gene_query):
            genes_to_show = list(genes[:number_of_genes_to_show])
            sequence_changes_to_show = list(sequence_changes[:number_of_genes_to_show])

        else:
            number_of_genes_to_show = request.GET['number_of_top_genes']
            genes_to_show = list(genes[:int(request.GET['number_of_top_genes'])])
            sequence_changes_to_show = list(sequence_changes[:int(request.GET['number_of_top_genes'])])

    else:
        genes_to_show = list(genes[:20])
        sequence_changes_to_show = list(sequence_changes[:20])

    context = Context({"protein_change_type_count_dict": protein_change_type_count_dict,
                       "mutation_type_count_dict": mutation_type_count_dict,
                       "genes": mark_safe(genes_to_show),
                       "sequence_changes": mark_safe(sequence_changes_to_show),
                       "gene_color_set": mark_safe(GENE_COLORS),
                       "seq_color_set": mark_safe(SEQ_COLORS),
                       "mutation_types": mark_safe(MUTATION_TYPES),
                       "protein_types": mark_safe(PROTEIN_TYPES),
                       "Ignored_Gene_Form": IgnoredGenesForm({"ignored_genes": gene_list}),
                       "number_of_genes_to_show": number_of_genes_to_show})

    template = loader.get_template(DASHBOARD_TEMPLATE)

    return HttpResponse(template.render(context))


def _is_query_empty(query):

    is_query_empty = False

    if not query:

        is_query_empty = True

    return is_query_empty


class IgnoredGenesForm(forms.Form):
    ignored_genes = forms.CharField(widget=forms.Textarea, required=False)
