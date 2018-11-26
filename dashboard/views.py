import time
from django.shortcuts import render

from django.http import HttpResponse
from seq.views import common
from django.utils.safestring import mark_safe
from common.util import common_context
from ale.utils import get_all_ale_exps
from ale.models import AleExperiment, AleId, Isolate
from dashboard.models import ObservedMutationCounts, UniqueMutationCounts, SampleCounts
from dashboard.timeline_util import get_timeline
from stats.views import get_histogram_item_count
from dashboard.models import BarCharts
from stats.util import MAX_HISTOGRAM_SIZE
from logs.aledb_logger import get_logger, user_extra, join_extras

DEFAULT_IGNORED_MUTATIONS = "[]"
DASHBOARD_TEMPLATE = "dashboard.html"
__author__ = 'pphaneuf'

usage_lgr = get_logger("usage")
exception_lgr = get_logger("exceptions")
performance_lgr = get_logger("performance")


def dashboard(request):
    usage_lgr.info("populating dashboard", extra=user_extra(request))

    try:
        start_time = time.clock()
        general_count_dict = _get_general_count_dict()
        observed_mutation_counts = ObservedMutationCounts.objects.first()
        unique_mutation_counts = UniqueMutationCounts.objects.first()

        if unique_mutation_counts and observed_mutation_counts:
            general_count_dict['observed'] = observed_mutation_counts.total
            general_count_dict['unique'] = unique_mutation_counts.total

        mutation_type_count_dict = _get_mutation_type_count_dict(observed_mutation_counts,
                                                                 unique_mutation_counts)
        functional_change_type_count_dict = _get_functional_change_type_count_dict(observed_mutation_counts,
                                                                                   unique_mutation_counts)
        barchart_item_count = get_histogram_item_count(request)
        histogram_data = BarCharts.objects.first()

        if histogram_data:
            gene_histogram_data = histogram_data.mut_gene_json[:barchart_item_count]
            gene_mut_histogram_data = histogram_data.mut_json[:barchart_item_count]
        else:
            gene_histogram_data = []
            gene_mut_histogram_data = []

        context = common_context.copy()
        context.update({"experiments": get_all_ale_exps(request.user),
                        "functional_change_type_count_dict": functional_change_type_count_dict,
                        "count_dict": general_count_dict,
                        "mutation_type_count_dict": mutation_type_count_dict,
                        "genes": mark_safe(gene_histogram_data),
                        "sequence_changes": mark_safe(gene_mut_histogram_data),
                        "gene_color_set": mark_safe(common.GENE_COLORS),
                        "seq_color_set": mark_safe(common.SEQ_COLORS),
                        "mutation_types": mark_safe(common.MUTATION_TYPE_LIST),
                        "protein_types": mark_safe(common.FUNCTIONAL_CHANGE_TYPE_LIST),
                        "number_of_genes_to_show": barchart_item_count,
                        "max_histogram_size": MAX_HISTOGRAM_SIZE,
                        "timeline": get_timeline()})
        performance_lgr.info("dashboard performance", extra=join_extras(user_extra(request), {"time taken": time.clock() - start_time}))

        return render(request, DASHBOARD_TEMPLATE, context, content_type="text/html")

    except Exception as e:
        exception_lgr.exception(e, extra = user_extra(request))



def _get_general_count_dict():
    count_dict = {}
    count_dict['ale_exp'] = AleExperiment.objects.count()  # No need to filter experiment count.

    sample_counts = SampleCounts.objects.first()

    if sample_counts:
        count_dict['ale'] = sample_counts.ale_count
        count_dict['flask'] = sample_counts.flask_count
        count_dict['isolate'] = sample_counts.isolate_count
    return count_dict


def _get_mutation_type_count_dict(observed_mutation_counts, unique_mutation_counts):

    mutation_type_count_dict = {'observed': {}, 'unique': {}}

    if not (unique_mutation_counts and observed_mutation_counts):
        return mutation_type_count_dict

    for mutation_type in common.MUTATION_TYPE_LIST:
        observed_mutation_type_count = 0
        unique_mutation_type_count = 0
        if mutation_type == 'SNP':
            observed_mutation_type_count = observed_mutation_counts.single_base_substitution
            unique_mutation_type_count = unique_mutation_counts.single_base_substitution
        elif mutation_type == 'SUB':
            observed_mutation_type_count = observed_mutation_counts.multiple_base_substitution
            unique_mutation_type_count = unique_mutation_counts.multiple_base_substitution
        elif mutation_type == 'DEL':
            observed_mutation_type_count = observed_mutation_counts.deletion
            unique_mutation_type_count = unique_mutation_counts.deletion
        elif mutation_type == 'INS':
            observed_mutation_type_count = observed_mutation_counts.insertion
            unique_mutation_type_count = unique_mutation_counts.insertion
        elif mutation_type == 'MOB':
            observed_mutation_type_count = observed_mutation_counts.mobile_element_insertion
            unique_mutation_type_count = unique_mutation_counts.mobile_element_insertion
        elif mutation_type == 'AMP':
            observed_mutation_type_count = observed_mutation_counts.amplification
            unique_mutation_type_count = unique_mutation_counts.amplification
        elif mutation_type == 'CON':
            observed_mutation_type_count = observed_mutation_counts.gene_conversion
            unique_mutation_type_count = unique_mutation_counts.gene_conversion
        elif mutation_type == 'INV':
            observed_mutation_type_count = observed_mutation_counts.inversion
            unique_mutation_type_count = unique_mutation_counts.inversion
        mutation_type_count_dict['observed'][mutation_type] = observed_mutation_type_count
        mutation_type_count_dict['unique'][mutation_type] = unique_mutation_type_count

    return mutation_type_count_dict


def _get_functional_change_type_count_dict(observed_mutation_counts, unique_mutation_counts):
    functional_change_type_count_dict = {'observed': {}, 'unique': {}}

    if not (unique_mutation_counts and observed_mutation_counts):
        return functional_change_type_count_dict

    for functional_change_type in common.FUNCTIONAL_CHANGE_TYPE_LIST:
        observed_function_change_count = 0
        unique_function_change_count = 0
        if functional_change_type == 'intergenic':
            observed_function_change_count = observed_mutation_counts.intergenic
            unique_function_change_count = unique_mutation_counts.intergenic
        elif functional_change_type == 'noncoding':
            observed_function_change_count = observed_mutation_counts.noncoding
            unique_function_change_count = unique_mutation_counts.noncoding
        elif functional_change_type == 'pseudogene':
            observed_function_change_count = observed_mutation_counts.pseudogene
            unique_function_change_count = unique_mutation_counts.pseudogene
        elif functional_change_type == 'snp_type_synonymous':
            observed_function_change_count = observed_mutation_counts.synonymous
            unique_function_change_count = unique_mutation_counts.synonymous
        elif functional_change_type == 'snp_type_nonsynonymous':
            observed_function_change_count = observed_mutation_counts.nonsynonymous
            unique_function_change_count = unique_mutation_counts.nonsynonymous
        functional_change_type_count_dict['observed'][functional_change_type] = observed_function_change_count
        functional_change_type_count_dict['unique'][functional_change_type] = unique_function_change_count

    return functional_change_type_count_dict
