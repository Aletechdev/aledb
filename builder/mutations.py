import collections
import json

import ale.common
import ale.models

import seq.views.common
import seq.models


def get_all_genes():

    gene_list = []

    with open('ME.txt') as f:
        for line in f:
            gene_list.append(line.strip())

    return gene_list


def get_all_observed_mutations_from_ale():

    gene_list = get_all_genes()
    ale_experiment_id_list = [4, 6, 24, 25, 28, 35, 36, 37, 43, 44, 46, 59, 60, 64, 66, 70, 71, 72, 75, 76, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88]
    ale_mutation_dict = {}

    for ale_experiment_id in ale_experiment_id_list:

        ale_experiment = ale.models.AleExperiment.objects.filter(ale_id=ale_experiment_id)
        ale_experiment_name = ale_experiment[0].name

        seq_experiment_ordered_dict = collections.OrderedDict()

        ale_experiment_selector = seq.views.common.get_ale_experiment_selector(ale_experiment_id)

        ale_id_selector = seq.views.common.get_ale_number_selector(None)

        sql_query = seq.views.common.SEQ_EXPERIMENT_QUERY % (ale_experiment_selector, ale_id_selector)

        seq_experiments_raw_queryset = seq.models.ResequencingExperiment.objects.raw(sql_query)

        for seq_experiment in seq_experiments_raw_queryset:

                seq_experiment_ordered_dict[seq_experiment.id] = seq_experiment

        observed_mutations_query_set = seq.views.common.get_observed_mutations(seq_experiment_ordered_dict)

        mutations = seq.models.Mutation.objects.filter(pk__in=observed_mutations_query_set.values_list("mutation", flat=True))

        mutated_gene_list = [mutation.gene for mutation in mutations]

        ale_mutation_dict[ale_experiment_name] = list(set(mutated_gene_list).intersection(set(gene_list)))
        # print(ale_mutation_dict)

    with open('ME.json', 'w') as fp:
        json.dump(ale_mutation_dict, fp)