__author__ = 'pphaneuf'


from django.contrib.auth.decorators import login_required

from django.http import HttpResponse

from django.template import Context, loader

from django.utils.safestring import mark_safe

import aleinfo.settings as settings

import seq.models   # TODO: only import necessary models.

from seq.views import common

from django.db.models import Count

from seq.forms.ignored_gene import IgnoredGenesForm

EXPERIMENT_LIST_TEMPLATE = "experiment_view.html"


# TODO: used by multiple views. Also implemented within views.py; implement in one location.
if hasattr(settings, "sequencing_url"):
    resequencing_report_url = settings.sequencing_url
else:
    resequencing_report_url = common.DEFAULT_RESEQ_REPORT_URL


@login_required
def lists(request):
    """return a list of resequencing experiments"""

    reseq_experiments = common.get_seq_experiment_raw_queryset(request)

    # Would rather want to use something like a dictionary since an experiment is
    # unique, though an experiment is currently a structure and an integral type
    # that can be used as a key.

    ale_experiment_id = common.get_ale_experiment_id(request)

    experiments_info_list = _get_reseq_experiment_info_list(reseq_experiments)

    mutation_query_set = _get_mutation_query_set(request)
    observed_mutations_query_set = _get_observed_mutation_queryset(request)

    mutation_type_count_dict = _get_mutation_type_count_dict(mutation_query_set)
    observed_mutation_type_count_dict = _get_observed_mutation_type_count_dict(observed_mutations_query_set)

    protein_change_type_count_dict = _get_protein_change_type_count_dict(mutation_query_set)
    observed_protein_change_type_count_dict = _get_observed_protein_change_type_count_dict(observed_mutations_query_set)

    template = loader.get_template(EXPERIMENT_LIST_TEMPLATE)

    ale_experiment_name = common.get_ale_experiment_name(request)

    needle_plot_data = []

    for observed_mutation in observed_mutations_query_set:
        needle_plot_data.append(
            {'coord': str(observed_mutation.mutation.position), 'category': observed_mutation.mutation.mutation_type,
             'value': 1})

    gene_query = observed_mutations_query_set.values('mutation__gene', 'mutation__mutation_type').annotate(
        the_count=Count('mutation__gene')).order_by('-the_count')
    sequence_change_query = observed_mutations_query_set.values('mutation__gene', 'mutation__protein_change').annotate(
        the_count=Count('mutation__gene')).order_by('-the_count')

    gene_list, genes, sequence_changes = common.get_ignored_genes(request, gene_query, sequence_change_query)

    genes = common.set_gene_bar_chart_colors(genes)

    sequence_changes = common.set_sequence_change_bar_chart_colors(sequence_changes)

    genes_to_show, sequence_changes_to_show, number_of_genes_to_show = common.get_genes_to_show(request, genes, sequence_changes)

    context = Context({"protein_change_type_count_dict": protein_change_type_count_dict,
                       "observed_protein_change_type_count_dict": observed_protein_change_type_count_dict,
                       "mutation_type_count_dict": mutation_type_count_dict,
                       "observed_mutation_type_count_dict": observed_mutation_type_count_dict,
                       "experiments_info_list": experiments_info_list,
                       "resequencing_report_url": resequencing_report_url,
                       "ale_experiment_name": ale_experiment_name,
                       "muts_needle_plot": loader.get_template("muts_needle_plot.html"),
                       "needle_plot_data": mark_safe(list(needle_plot_data)),
                       "genes": mark_safe(genes_to_show),
                       "sequence_changes": mark_safe(sequence_changes_to_show),
                       "gene_color_set": mark_safe(common.GENE_COLORS),
                       "seq_color_set": mark_safe(common.SEQ_COLORS),
                       "mutation_types": mark_safe(common.MUTATION_TYPE_LIST),
                       "protein_types": mark_safe(common.PROTEIN_CHANGE_TYPE_LIST),
                       "Ignored_Gene_Form": IgnoredGenesForm({"ignored_genes": gene_list}),
                       "number_of_genes_to_show": number_of_genes_to_show,
                       "ale_experiment_id": ale_experiment_id})

    return HttpResponse(template.render(context))


def _get_mutation_query_set(request):

    observed_mutations_query_set = _get_observed_mutation_queryset(request)
    mutation_query_set = seq.models.Mutation.objects.filter(pk__in=observed_mutations_query_set.values_list("mutation", flat=True))

    return mutation_query_set


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


def _get_reseq_experiment_info_list(reseq_experiments):

    reseq_experiments_info_list = []

    for reseq_experiment in reseq_experiments:

        mc_list = seq.models.UnassignedMissingCoverageEvidence.objects.filter(sequencing_experiment_id=reseq_experiment.id)

        mapped_read_count = int((reseq_experiment.percentage_mapped / 100) * reseq_experiment.reads)

        species = reseq_experiment.isolate.flask.ale_id.species

        strain = reseq_experiment.isolate.flask.ale_id.strain

        knockouts = reseq_experiment.isolate.flask.ale_id.knockouts

        clonal_or_population = "clonal"

        if reseq_experiment.isolate.is_population:

            clonal_or_population = "population"

        media_temperature = reseq_experiment.isolate.flask.media.temperature

        media_description = reseq_experiment.isolate.flask.media.description

        substrate = reseq_experiment.isolate.flask.media.substrate

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


# TODO: should be transfered to common and have a parameter to filter wt mutations.
def _get_observed_mutation_queryset(request):

    seq_experiment_ordered_dict = common.get_experiment_ordered_dict(request, include_starting_strain=True)

    wt_id = seq.views.common.get_wt_seq_experiment_id(seq_experiment_ordered_dict)

    seq_experiment_ordered_dict = common.filter_out_starting_strain_seq_experiment(seq_experiment_ordered_dict)

    filter_mutation_list = seq.views.common.get_observed_mutations([wt_id])
    filter_mutation_id_list = [observed_mutation.mutation.id for observed_mutation in filter_mutation_list]

    observed_mutation_query_set = common.get_observed_mutations(list(seq_experiment_ordered_dict.keys()))

    filter_observed_mutation_queryset = observed_mutation_query_set.exclude(mutation__in=filter_mutation_id_list)

    return filter_observed_mutation_queryset
