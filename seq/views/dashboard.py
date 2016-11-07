from django.contrib.auth.decorators import login_required

from django.template import loader

from django.http import HttpResponse

from seq.views import common

import seq.models

from django.db.models import Count

from django.utils.safestring import mark_safe

from filter.util import dashboard_filter

from common.db_util import get_all_ale_experiments, get_recent_experiments

from django.core.cache import cache

from ale.models import AleExperiment
from ale.models import AleId
from ale.models import Flask
from ale.models import Isolate

DEFAULT_IGNORED_MUTATIONS = "[]"

DASHBOARD_TEMPLATE = "dashboard.html"

__author__ = 'pphaneuf'


@login_required
def dashboard(request):
    mutation_query_set, observed_mutation_queryset = _get_cached_dashboard_query()

    count_dict = {}
    count_dict['observed'] = observed_mutation_queryset.count()
    count_dict['unique'] = mutation_query_set.count()
    count_dict['ale_exp'] = AleExperiment.objects.count()
    count_dict['ale'] = AleId.objects.count()
    count_dict['isolate'] = Isolate.objects.count()

    mutation_type_count_dict = {}
    mutation_type_count_dict['observed'] = {}
    mutation_type_count_dict['unique'] = {}
    for mutation_type in common.MUTATION_TYPE_LIST:
        observed_mutation_type_count = observed_mutation_queryset.filter(mutation__mutation_type=mutation_type).count()
        mutation_type_count_dict['observed'][mutation_type] = observed_mutation_type_count
        mutation_type_count = mutation_query_set.filter(mutation_type=mutation_type).count()
        mutation_type_count_dict['unique'][mutation_type] = mutation_type_count

    protein_change_type_count_dict = {}
    protein_change_type_count_dict['observed'] = {}
    protein_change_type_count_dict['unique'] = {}
    for protein_change_type in common.PROTEIN_CHANGE_TYPE_LIST:
        protein_change_count = observed_mutation_queryset.filter(mutation__protein_change__contains=protein_change_type).count()
        protein_change_type_count_dict['observed'][protein_change_type] = protein_change_count
        protein_change_count = mutation_query_set.filter(protein_change__contains=protein_change_type).count()
        protein_change_type_count_dict['unique'][protein_change_type] = protein_change_count

    gene_bar_chart_dict = common.get_gene_bar_chart_dict(observed_mutation_queryset, 'dashboard')

    sequence_changes = observed_mutation_queryset.values('mutation__gene', 'mutation__protein_change')\
        .annotate(the_count=Count('mutation__gene')).order_by('-the_count')

    genes = common.set_gene_bar_chart_colors(gene_bar_chart_dict)

    sequence_changes = common.set_sequence_change_bar_chart_colors(sequence_changes)

    genes_to_show, sequence_changes_to_show, number_of_genes_to_show = common.get_genes_to_show(request, genes,
                                                                                                sequence_changes)
    context = {"protein_change_type_count_dict": protein_change_type_count_dict,
               "count_dict": count_dict,
               "mutation_type_count_dict": mutation_type_count_dict,
               "genes": mark_safe(genes_to_show),
               "sequence_changes": mark_safe(sequence_changes_to_show),
               "gene_color_set": mark_safe(common.GENE_COLORS),
               "seq_color_set": mark_safe(common.SEQ_COLORS),
               "mutation_types": mark_safe(common.MUTATION_TYPE_LIST),
               "protein_types": mark_safe(common.PROTEIN_CHANGE_TYPE_LIST),
               "number_of_genes_to_show": number_of_genes_to_show,
               "experiments": get_all_ale_experiments(),
               "recent_experiments": get_recent_experiments()}

    template = loader.get_template(DASHBOARD_TEMPLATE)

    return HttpResponse(template.render(context))


def get_filtered_mutation_queryset(gene_query):

    mut_id_list = gene_query.values_list('mutation_id').distinct()

    filtered_mut_id_list = [mut_id[0] for mut_id in mut_id_list]

    mutation_queryset = seq.models.Mutation.objects.filter(id__in=filtered_mut_id_list)

    return mutation_queryset


def _get_cached_dashboard_query():

    cached_mutation_queryset = cache.get('dashboard_mutation')

    cached_observed_mutation_queryset = cache.get('dashboard_observed_mutation')

    if cached_mutation_queryset is None or cached_observed_mutation_queryset is None:

        # TODO: only filter out mutations without genes for the barcharts. The
        # mutations count tables above bar charts don't care if a mutation
        # doesn't have a gene.
        # initial_query = seq.models.ObservedMutation.objects.exclude(mutation__gene='')
        initial_query = seq.models.ObservedMutation.objects.exclude()

        observed_mutation_queryset = dashboard_filter(initial_query)

        mutation_query_set = get_filtered_mutation_queryset(observed_mutation_queryset)

        cache.set('dashboard_mutation', mutation_query_set, None)

        cache.set('dashboard_observed_mutation', observed_mutation_queryset, None)

        return mutation_query_set, observed_mutation_queryset

    else:

        return cached_mutation_queryset, cached_observed_mutation_queryset
