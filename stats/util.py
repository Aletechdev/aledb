import re
from django.db.models import Count
from genes.util import get_gene_list
from operator import itemgetter
from collections import Counter
from seq.models import UnassignedMissingCoverageEvidence
from seq.views.common import MUTATION_TYPE_LIST, COLORS, DEFAULT_COLOR, FUNCTIONAL_CHANGE_TYPE_LIST


MAX_HISTOGRAM_SIZE = 50


def get_histogram_jsons(observed_mutation_queryset, histogram_item_count):
    observed_mutation_queryset = observed_mutation_queryset.exclude(mutation__gene='')
    observed_mutation_queryset = observed_mutation_queryset.exclude(mutation__gene='-')
    observed_mutation_queryset = observed_mutation_queryset.exclude(mutation__gene='–, –')
    gene_bar_chart_list = get_gene_bar_chart_list(observed_mutation_queryset)
    sequence_change_query = observed_mutation_queryset.values('mutation__gene', 'mutation__protein_change').annotate(
        the_count=Count('mutation__gene')).order_by('-the_count')
    genes = set_gene_bar_chart_colors(gene_bar_chart_list)
    sequence_changes = set_sequence_change_bar_chart_colors(sequence_change_query)

    genes_json = list(genes[:histogram_item_count])
    sequence_change_json = list(sequence_changes[:histogram_item_count])

    return genes_json, sequence_change_json


def get_needle_plot_data(obs_mut_queryset):
    needle_plot_data = []
    for observed_mutation in obs_mut_queryset:
        needle_plot_data.append(
            {'coord': str(observed_mutation.mutation.position),
             'category': observed_mutation.mutation.mutation_type,
             'value': 1})
    return needle_plot_data


def get_mutation_type_count_dict(mutation_query_set):
    mutation_type_count_dict = {}
    for mutation_type in MUTATION_TYPE_LIST:
        mutation_type_count = mutation_query_set.filter(mutation_type=mutation_type).count()
        mutation_type_count_dict[mutation_type] = mutation_type_count
    return mutation_type_count_dict


def get_observed_mutation_type_count_dict(observed_mutation_query_set):
    mutation_type_count_dict = {mutation_type:0 for mutation_type in MUTATION_TYPE_LIST}
    for observed_mutation in observed_mutation_query_set:
        mutation_type_count_dict[observed_mutation.mutation.mutation_type] += 1
    return mutation_type_count_dict


def get_protein_change_type_count_dict(mutation_query_set):
    protein_change_type_count_dict = {}
    for protein_change_type in FUNCTIONAL_CHANGE_TYPE_LIST:
        protein_change_count = mutation_query_set.filter(protein_change__contains=protein_change_type).count()
        protein_change_type_count_dict[protein_change_type] = protein_change_count
    return protein_change_type_count_dict


def get_observed_protein_change_type_count_dict(observed_mutations_query_set):
    protein_change_type_count_dict = {protein_change_type:0 for protein_change_type in FUNCTIONAL_CHANGE_TYPE_LIST}
    for observed_mutation in observed_mutations_query_set:
        for protein_change_type in FUNCTIONAL_CHANGE_TYPE_LIST:
            if protein_change_type in observed_mutation.mutation.protein_change:
                protein_change_type_count_dict[protein_change_type] += 1
    return protein_change_type_count_dict


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


def get_reseq_experiment_info_list(reseq_experiments):
    reseq_experiments_info_list = []
    for reseq_experiment in reseq_experiments:
        mc_list = UnassignedMissingCoverageEvidence.objects.filter(sequencing_experiment_id=reseq_experiment.id)
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


def get_gene_bar_chart_list(observed_mutation_queryset):

    gene_list = [[get_gene_list(gene['mutation__gene']), gene['mutation__mutation_type']] for
                 gene in observed_mutation_queryset.values('mutation__gene', 'mutation__mutation_type')]

    mutation_type_gene_dict = {}

    for pair in gene_list:
        genes = set(pair[0])
        try:
            mutation_type_gene_dict[pair[1]] += [genes]
        except KeyError:
            mutation_type_gene_dict[pair[1]] = [genes]

    final_list = []

    for key, value in mutation_type_gene_dict.items():
        flattened_list = sorted([item for sublist in value for item in sublist], reverse=True)
        counted_list = Counter(flattened_list)
        for k, v in counted_list.items():
            new_dict = {'mutation__gene': k, 'the_count': v, 'mutation__mutation_type': key}
            final_list.append(new_dict)
    final_sorted_list = sorted(final_list, key=itemgetter('the_count'), reverse=True)

    return final_sorted_list



def set_gene_bar_chart_colors(genes):
    for gene in genes:
        if gene['mutation__mutation_type'] in MUTATION_TYPE_LIST:
            gene['color'] = COLORS[MUTATION_TYPE_LIST.index(gene['mutation__mutation_type'])]
        else:
            gene['color'] = DEFAULT_COLOR
    return genes


def set_sequence_change_bar_chart_colors(sequence_changes):
    for seq_change in sequence_changes:
        has_match = False
        for protein in FUNCTIONAL_CHANGE_TYPE_LIST:
            if protein in seq_change['mutation__protein_change']:
                seq_change['color'] = COLORS[FUNCTIONAL_CHANGE_TYPE_LIST.index(protein)]
                has_match = True
                break
        if has_match is False:
            seq_change['color'] = DEFAULT_COLOR
        seq_change['mutation__protein_change'] = re.compile(r'<[^>]+>').sub('', seq_change['mutation__protein_change'])
    return sequence_changes
