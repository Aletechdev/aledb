import re
from django.db.models import Count
from genes.util import get_gene_list
from operator import itemgetter
from collections import Counter
from seq.models import UnassignedMissingCoverageEvidence
from seq.util import get_all_observed_mutations, get_reseq_ordered_dict
from seq.views.common import MUTATION_TYPE_LIST, COLORS, DEFAULT_COLOR, FUNCTIONAL_CHANGE_TYPE_LIST
from stats.models import StaticData
from logs.aledb_logger import get_logger
from filter.util import get_filtered_observed_mutations_queryset
import stats.models


MAX_HISTOGRAM_SIZE = 50
exception_lgr = get_logger("exceptions")
usage_lgr = get_logger("usage")
performance_lgr = get_logger("performance")


def get_observed_mutation_queryset(ale_experiment_id):
    ordered_reseq_dict = get_reseq_ordered_dict(ale_experiment_id)
    observed_mutation_query_set = get_all_observed_mutations(list(ordered_reseq_dict.keys()))
    observed_mutation_query_set = get_filtered_observed_mutations_queryset(observed_mutation_query_set)
    return observed_mutation_query_set


def get_histogram_jsons(ale_experiment_id, histogram_item_count):
    genes = StaticData.objects.get(id=ale_experiment_id).histogram_data[:histogram_item_count]
    return genes


def generate_histogram_jsons(observed_mutation_queryset):
    observed_mutation_queryset = observed_mutation_queryset.exclude(mutation__gene='')
    observed_mutation_queryset = observed_mutation_queryset.exclude(mutation__gene='-')
    observed_mutation_queryset = observed_mutation_queryset.exclude(mutation__gene='–, –')
    gene_bar_chart_list = get_gene_bar_chart_list(observed_mutation_queryset)
    genes = set_gene_bar_chart_colors(gene_bar_chart_list)

    genes_json = list(genes)
    return genes_json


def generate_needle_plot_data(obs_mut_queryset):
    needle_plot_data = []
    for observed_mutation in obs_mut_queryset:
        needle_plot_data.append(
            {'coord': str(observed_mutation.mutation.position),
             'category': observed_mutation.mutation.mutation_type,
             'value': 1})
    return needle_plot_data


def get_needle_plot_data(experiment_id):
    data = StaticData.objects.get(id=experiment_id).mut_needle_data
    return data


def generate_static_data(ale_id):
    observed_mutation_queryset = get_observed_mutation_queryset(ale_id)
    mutation_needle_data = generate_needle_plot_data(observed_mutation_queryset)
    static_data_orm, created = stats.models.StaticData.objects.get_or_create(id=ale_id)
    static_data_orm.mut_needle_data = mutation_needle_data
    static_data_orm.histogram_data = generate_histogram_jsons(observed_mutation_queryset)
    static_data_orm.save()


def get_mutation_type_count_dict(mutation_query_set):
    mutation_type_count_dict = {}
    for mutation_type in MUTATION_TYPE_LIST:
        mutation_type_count = mutation_query_set.filter(mutation_type=mutation_type).count()
        mutation_type_count_dict[mutation_type] = mutation_type_count
    return mutation_type_count_dict


def get_observed_mutation_type_count_dict(observed_mutation_query_set):
    mutation_type_count_dict = {mutation_type:0 for mutation_type in MUTATION_TYPE_LIST}
    for observed_mutation in observed_mutation_query_set:
        mut_type = observed_mutation.mutation.mutation_type
        if mut_type in mutation_type_count_dict.keys():
            mutation_type_count_dict[mut_type] += 1
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
    for reseq in reseq_experiments:
        mc_list = UnassignedMissingCoverageEvidence.objects.filter(sequencing_experiment_id=reseq.id)
        mapped_read_count = int((reseq.percentage_mapped / 100) * reseq.reads)
        species = reseq.tech_rep.isolate.flask.ale_id.species
        strain = reseq.tech_rep.isolate.flask.ale_id.strain
        knockouts = reseq.tech_rep.isolate.flask.ale_id.description
        clonal_or_population = "clonal"
        if reseq.tech_rep.isolate.is_population:
            clonal_or_population = "population"
        media_temperature = reseq.tech_rep.isolate.flask.media.temperature
        media_description = reseq.tech_rep.isolate.flask.media.description
        substrate = reseq.tech_rep.isolate.flask.media.substrate

        # Using tuple because immutable; mc_list must remain associated with particular experiment.
        experiment_info_tuple = (reseq,
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
