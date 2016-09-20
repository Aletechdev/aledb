from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.template import loader
from django.utils.safestring import mark_safe
import aleinfo.settings as settings
import seq.models   # TODO: only import necessary models.
from seq.util import get_all_observed_mutations
from seq.views import common
from django.db.models import Count
from filter import util
from common.db_util import get_reseq_queryset,\
    get_ordered_reseq_dict,\
    get_mutation_queryset_from_obs_mut_queryset

from common.constants import REQUEST_ALE_EXPERIMENT_ID, REQUEST_ALE_ID

from filter.util import filter_mutations

from common.db_util import get_all_ale_experiments, get_recent_experiments

__author__ = 'pphaneuf'

STATS_TEMPLATE = "stats/index.html"


# TODO: used by multiple views. Also implemented within ale_exp_filter.py; implement in one location.
if hasattr(settings, "sequencing_url"):
    resequencing_report_url = settings.sequencing_url


# TODO: Move to common --> is also being used in compare.views.index.py
def get_ale_flask_isolate_count_list(reseq_queryset):
    ale_flask_isolate_count_dict = {}
    for reseq in reseq_queryset:
        if reseq.ale_id not in ale_flask_isolate_count_dict.keys():
            ale_flask_isolate_count_dict[reseq.ale_id] = {reseq.flask_number: 1}
        else:
            if reseq.flask_number not in ale_flask_isolate_count_dict[reseq.ale_id].keys():
                ale_flask_isolate_count_dict[reseq.ale_id][reseq.flask_number] = 1
            else:
                ale_flask_isolate_count_dict[reseq.ale_id][reseq.flask_number] += 1

    ale_flask_isolate_count_list = []
    for ale_id, flask_isolate_count_dict in ale_flask_isolate_count_dict.items():
        ale_flask_count = 0
        ale_isolate_count = 0
        for flask_isolate_count in flask_isolate_count_dict.values():
            ale_flask_count += 1
            ale_isolate_count += flask_isolate_count
        ale_flask_isolate_count_list.append((ale_id, ale_flask_count, ale_isolate_count))

    return ale_flask_isolate_count_list


@login_required
def stats(request):
    ale_experiment_id = request.GET.get(REQUEST_ALE_EXPERIMENT_ID)
    ale_id = request.GET.get(REQUEST_ALE_ID)
    reseq_queryset = get_reseq_queryset(ale_experiment_id, ale_id)

    ale_flask_isolate_count_list = get_ale_flask_isolate_count_list(reseq_queryset)

    # Would rather want to use something like a dictionary since an experiment is
    # unique, though an experiment is currently a structure and an integral type
    # that can be used as a key.

    ale_experiment_id = common.get_ale_experiment_id(request)

    experiments_info_list = get_reseq_experiment_info_list(reseq_queryset)

    observed_mutations_queryset = _get_observed_mutation_queryset(request, ale_experiment_id)

    mutation_query_set = get_mutation_queryset_from_obs_mut_queryset(observed_mutations_queryset)

    mutation_type_count_dict = _get_mutation_type_count_dict(mutation_query_set)
    observed_mutation_type_count_dict = _get_observed_mutation_type_count_dict(observed_mutations_queryset)

    protein_change_type_count_dict = _get_protein_change_type_count_dict(mutation_query_set)
    observed_protein_change_type_count_dict = _get_observed_protein_change_type_count_dict(observed_mutations_queryset)

    template = loader.get_template(STATS_TEMPLATE)

    ale_experiment_name = common.get_ale_experiment_name(request)

    needle_plot_data = []

    for observed_mutation in observed_mutations_queryset:
        needle_plot_data.append(
            {'coord': str(observed_mutation.mutation.position), 'category': observed_mutation.mutation.mutation_type,
             'value': 1})

    gene_bar_chart_dict = common.get_gene_bar_chart_dict(observed_mutations_queryset, ale_experiment_name)

    sequence_change_query = observed_mutations_queryset.values('mutation__gene', 'mutation__protein_change').annotate(
        the_count=Count('mutation__gene')).order_by('-the_count')

    genes = common.set_gene_bar_chart_colors(gene_bar_chart_dict)

    sequence_changes = common.set_sequence_change_bar_chart_colors(sequence_change_query)

    genes_to_show, sequence_changes_to_show, number_of_genes_to_show = common.get_genes_to_show(request, genes, sequence_changes)

    context = {"protein_change_type_count_dict": protein_change_type_count_dict,
               "observed_protein_change_type_count_dict": observed_protein_change_type_count_dict,
               "mutation_type_count_dict": mutation_type_count_dict,
               "observed_mutation_type_count_dict": observed_mutation_type_count_dict,
               "experiments_info_list": experiments_info_list,
               "resequencing_report_url": resequencing_report_url,
               "ale_experiment_name": ale_experiment_name,
               "needle_plot_data": mark_safe(list(needle_plot_data)),
               "genes": mark_safe(genes_to_show),
               "sequence_changes": mark_safe(sequence_changes_to_show),
               "gene_color_set": mark_safe(common.GENE_COLORS),
               "seq_color_set": mark_safe(common.SEQ_COLORS),
               "mutation_types": mark_safe(common.MUTATION_TYPE_LIST),
               "protein_types": mark_safe(common.PROTEIN_CHANGE_TYPE_LIST),
               "number_of_genes_to_show": number_of_genes_to_show,
               "ale_experiment_id": ale_experiment_id,
               "ale_flask_isolate_count_list": ale_flask_isolate_count_list,
               "experiments": get_all_ale_experiments(),
               "recent_experiments": get_recent_experiments(ale_experiment_id)}

    return HttpResponse(template.render(context))


def _get_protein_change_type_count_dict(mutation_query_set):

    protein_change_type_count_dict = {}
    for protein_change_type in common.PROTEIN_CHANGE_TYPE_LIST:
        protein_change_count = mutation_query_set.filter(protein_change__contains=protein_change_type).count()
        protein_change_type_count_dict[protein_change_type] = protein_change_count

    return protein_change_type_count_dict


def _get_observed_protein_change_type_count_dict(observed_mutations_query_set):

    protein_change_type_count_dict = {protein_change_type:0 for protein_change_type in common.PROTEIN_CHANGE_TYPE_LIST}

    for observed_mutation in observed_mutations_query_set:
        for protein_change_type in common.PROTEIN_CHANGE_TYPE_LIST:
            if protein_change_type in observed_mutation.mutation.protein_change:
                protein_change_type_count_dict[protein_change_type] += 1

    return protein_change_type_count_dict


def _get_mutation_type_count_dict(mutation_query_set):

    mutation_type_count_dict = {}
    for mutation_type in common.MUTATION_TYPE_LIST:
        mutation_type_count = mutation_query_set.filter(mutation_type=mutation_type).count()
        mutation_type_count_dict[mutation_type] = mutation_type_count

    return mutation_type_count_dict


def _get_observed_mutation_type_count_dict(observed_mutation_query_set):

    mutation_type_count_dict = {mutation_type:0 for mutation_type in common.MUTATION_TYPE_LIST}

    for observed_mutation in observed_mutation_query_set:
        mutation_type_count_dict[observed_mutation.mutation.mutation_type] += 1

    return mutation_type_count_dict


# TODO: Move to common --> is also being used in compare.views.index.py
def get_reseq_experiment_info_list(reseq_experiments):

    reseq_experiments_info_list = []

    for reseq_experiment in reseq_experiments:

        mc_list = seq.models.UnassignedMissingCoverageEvidence.objects.filter(sequencing_experiment_id=reseq_experiment.id)

        mapped_read_count = int((reseq_experiment.percentage_mapped / 100) * reseq_experiment.reads)

        species = reseq_experiment.tech_rep.isolate.flask.ale_id.species

        strain = reseq_experiment.tech_rep.isolate.flask.ale_id.strain

        knockouts = reseq_experiment.tech_rep.isolate.flask.ale_id.description

        clonal_or_population = "clonal"

        if reseq_experiment.tech_rep.isolate.is_population:

            clonal_or_population = "population"

        media_temperature = reseq_experiment.tech_rep.isolate.flask.media.temperature

        media_description = reseq_experiment.tech_rep.isolate.flask.media.description

        substrate = reseq_experiment.tech_rep.isolate.flask.media.substrate

        # Using tuple because immutable; mc_list must remain associated with particular experiment.
        experiment_info_tuple = (reseq_experiment,
                                 mc_list,
                                 mapped_read_count,
                                 clonal_or_population,
                                 media_temperature,
                                 media_description,
                                 substrate,
                                 species,
                                 strain,
                                 knockouts)

        reseq_experiments_info_list.append(experiment_info_tuple)

    return reseq_experiments_info_list


# TODO: should be transferred to filter app and have a parameter to filter wt mutations.
def _get_observed_mutation_queryset(request, ale_experiment_id):

    ordered_reseq_dict = get_ordered_reseq_dict(ale_experiment_id)

    observed_mutation_query_set = get_all_observed_mutations(list(ordered_reseq_dict.keys()))

    observed_mutation_query_set = _exclude_ignored_genes_and_mutations(request, observed_mutation_query_set)

    return observed_mutation_query_set


# TODO: Should move this function into the filter app
def _exclude_ignored_genes_and_mutations(request, observed_mutation_query_set):

    observed_mutation_query_set = observed_mutation_query_set.exclude(mutation__gene='')

    ale_experiment_id = common.get_ale_experiment_id(request)

    filter_settings = util.get_filter_settings(ale_experiment_id)

    observed_mutation_query_set = filter_mutations(observed_mutation_query_set, filter_settings)

    return observed_mutation_query_set
