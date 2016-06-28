__author__ = 'pphaneuf'


from django.contrib.auth.decorators import login_required

from django.template import Context, loader

from django.http import HttpResponse

from seq.views import common

import seq.models

from django.db.models import Count

from django.utils.safestring import mark_safe


DASHBOARD_TEMPLATE = "dashboard.html"


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

    genes = seq.models.ObservedMutation.objects.values('mutation__gene').annotate(the_count=Count('mutation__gene')).order_by('-the_count')
    sequence_changes = seq.models.ObservedMutation.objects.values('mutation__sequence_change', 'mutation__gene').annotate(the_count=Count('mutation__gene')).order_by('-the_count')

    if 'number_of_top_genes' in request.GET:

        gene_query = request.GET['number_of_top_genes']

        if _is_query_empty(gene_query):
            genes_to_show = list(genes[:20])
            sequence_changes_to_show = list(sequence_changes[:20])

        else:
            genes_to_show = list(genes[:int(request.GET['number_of_top_genes'])])
            sequence_changes_to_show = list(sequence_changes[:int(request.GET['number_of_top_genes'])])

        context = Context({"protein_change_type_count_dict": protein_change_type_count_dict,
                           "mutation_type_count_dict": mutation_type_count_dict,
                           "genes": mark_safe(genes_to_show),
                           "sequence_changes": mark_safe(sequence_changes_to_show)})

    else:
        genes_to_show = list(genes[:20])
        sequence_changes_to_show = list(sequence_changes[:20])
        context = Context({"protein_change_type_count_dict": protein_change_type_count_dict,
                           "mutation_type_count_dict": mutation_type_count_dict,
                           "genes": mark_safe(genes_to_show),
                           "sequence_changes": mark_safe(sequence_changes_to_show)})

    template = loader.get_template(DASHBOARD_TEMPLATE)
    return HttpResponse(template.render(context))


def _is_query_empty(query):

    is_query_empty = False

    if not query:

        is_query_empty = True

    return is_query_empty

