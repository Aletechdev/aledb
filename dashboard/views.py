from django.template import loader
from django.http import HttpResponse
from seq.views import common
from django.utils.safestring import mark_safe
from common.util import get_all_ale_experiments, get_recent_experiments
from ale.models import AleExperiment, AleId, Isolate
from dashboard.models import ObservedMutationCounts, UniqueMutationCounts, SampleCounts
from dashboard.timeline_util import get_timeline
from stats.views import get_histogram_item_count
from dashboard.models import BarCharts
from stats.util import MAX_HISTOGRAM_SIZE


DEFAULT_IGNORED_MUTATIONS = "[]"
DASHBOARD_TEMPLATE = "dashboard.html"
__author__ = 'pphaneuf'


def dashboard(request):
    general_count_dict = _get_general_count_dict()
    observed_mutation_count_queryset = ObservedMutationCounts.objects.all()
    unique_mutation_count_queryset = UniqueMutationCounts.objects.all()
    general_count_dict['observed'] = observed_mutation_count_queryset[0].total
    general_count_dict['unique'] = unique_mutation_count_queryset[0].total
    mutation_type_count_dict = _get_mutation_type_count_dict(observed_mutation_count_queryset,
                                                             unique_mutation_count_queryset)
    functional_change_type_count_dict = _get_functional_change_type_count_dict(observed_mutation_count_queryset,
                                                                               unique_mutation_count_queryset)
    barchart_item_count = get_histogram_item_count(request)
    histogram_data = BarCharts.objects.all()[0]

    gene_histogram_data = histogram_data.mut_gene_json[:barchart_item_count]
    gene_mut_histogram_data = histogram_data.mut_json[:barchart_item_count]

    context = {"functional_change_type_count_dict": functional_change_type_count_dict,
               "count_dict": general_count_dict,
               "mutation_type_count_dict": mutation_type_count_dict,
               "genes": mark_safe(gene_histogram_data),
               "sequence_changes": mark_safe(gene_mut_histogram_data),
               "gene_color_set": mark_safe(common.GENE_COLORS),
               "seq_color_set": mark_safe(common.SEQ_COLORS),
               "mutation_types": mark_safe(common.MUTATION_TYPE_LIST),
               "protein_types": mark_safe(common.FUNCTIONAL_CHANGE_TYPE_LIST),
               "number_of_genes_to_show": barchart_item_count,
               "experiments": get_all_ale_experiments(),
               "recent_experiments": get_recent_experiments(),
               "max_histogram_size": MAX_HISTOGRAM_SIZE,
               "timeline": get_timeline()}

    template = loader.get_template(DASHBOARD_TEMPLATE)

    return HttpResponse(template.render(context))


def _get_general_count_dict():
    count_dict = {}
    count_dict['ale_exp'] = AleExperiment.objects.count()  # No need to filter experiment count.
    sample_counts = SampleCounts.objects.all()[0]
    count_dict['ale'] = sample_counts.ale_count
    count_dict['flask'] = sample_counts.flask_count
    count_dict['isolate'] = sample_counts.isolate_count
    return count_dict


def _get_mutation_type_count_dict(observed_mutation_count_queryset, unique_mutation_count_queryset):

    mutation_type_count_dict = {'observed': {}, 'unique': {}}
    for mutation_type in common.MUTATION_TYPE_LIST:
        observed_mutation_type_count = 0
        unique_mutation_type_count = 0
        if mutation_type == 'SNP':
            observed_mutation_type_count = observed_mutation_count_queryset[0].single_base_substitution
            unique_mutation_type_count = unique_mutation_count_queryset[0].single_base_substitution
        elif mutation_type == 'SUB':
            observed_mutation_type_count = observed_mutation_count_queryset[0].multiple_base_substitution
            unique_mutation_type_count = unique_mutation_count_queryset[0].multiple_base_substitution
        elif mutation_type == 'DEL':
            observed_mutation_type_count = observed_mutation_count_queryset[0].deletion
            unique_mutation_type_count = unique_mutation_count_queryset[0].deletion
        elif mutation_type == 'INS':
            observed_mutation_type_count = observed_mutation_count_queryset[0].insertion
            unique_mutation_type_count = unique_mutation_count_queryset[0].insertion
        elif mutation_type == 'MOB':
            observed_mutation_type_count = observed_mutation_count_queryset[0].mobile_element_insertion
            unique_mutation_type_count = unique_mutation_count_queryset[0].mobile_element_insertion
        elif mutation_type == 'DUP':
            observed_mutation_type_count = observed_mutation_count_queryset[0].duplication
            unique_mutation_type_count = unique_mutation_count_queryset[0].duplication
        elif mutation_type == 'AMP':
            observed_mutation_type_count = observed_mutation_count_queryset[0].amplification
            unique_mutation_type_count = unique_mutation_count_queryset[0].amplification
        elif mutation_type == 'CON':
            observed_mutation_type_count = observed_mutation_count_queryset[0].gene_conversion
            unique_mutation_type_count = unique_mutation_count_queryset[0].gene_conversion
        elif mutation_type == 'INV':
            observed_mutation_type_count = observed_mutation_count_queryset[0].inversion
            unique_mutation_type_count = unique_mutation_count_queryset[0].inversion
        mutation_type_count_dict['observed'][mutation_type] = observed_mutation_type_count
        mutation_type_count_dict['unique'][mutation_type] = unique_mutation_type_count

    return mutation_type_count_dict


def _get_functional_change_type_count_dict(observed_mutation_count_queryset, unique_mutation_count_queryset):
    functional_change_type_count_dict = {'observed': {}, 'unique': {}}
    for functional_change_type in common.FUNCTIONAL_CHANGE_TYPE_LIST:
        observed_function_change_count = 0
        unique_function_change_count = 0
        if functional_change_type == 'intergenic':
            observed_function_change_count = observed_mutation_count_queryset[0].intergenic
            unique_function_change_count = unique_mutation_count_queryset[0].intergenic
        elif functional_change_type == 'noncoding':
            observed_function_change_count = observed_mutation_count_queryset[0].noncoding
            unique_function_change_count = unique_mutation_count_queryset[0].noncoding
        elif functional_change_type == 'pseudogene':
            observed_function_change_count = observed_mutation_count_queryset[0].pseudogene
            unique_function_change_count = unique_mutation_count_queryset[0].pseudogene
        elif functional_change_type == 'snp_type_synonymous':
            observed_function_change_count = observed_mutation_count_queryset[0].synonymous
            unique_function_change_count = unique_mutation_count_queryset[0].synonymous
        elif functional_change_type == 'snp_type_nonsynonymous':
            observed_function_change_count = observed_mutation_count_queryset[0].nonsynonymous
            unique_function_change_count = unique_mutation_count_queryset[0].nonsynonymous
        functional_change_type_count_dict['observed'][functional_change_type] = observed_function_change_count
        functional_change_type_count_dict['unique'][functional_change_type] = unique_function_change_count

    return functional_change_type_count_dict
