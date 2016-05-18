import collections

import ale.common

import seq.views.common
import seq.models


def get_all_observed_mutations_from_ale():

    gene = 'ycjW'
    ale_experiment_id = 6

    seq_experiment_ordered_dict = collections.OrderedDict()

    ale_experiment_selector = seq.views.common.get_ale_experiment_selector(ale_experiment_id)

    ale_id_selector = seq.views.common.get_ale_number_selector(None)

    sql_query = seq.views.common.SEQ_EXPERIMENT_QUERY % (ale_experiment_selector, ale_id_selector)

    seq_experiments_raw_queryset = seq.models.ResequencingExperiment.objects.raw(sql_query)

    for seq_experiment in seq_experiments_raw_queryset:

            seq_experiment_ordered_dict[seq_experiment.id] = seq_experiment

    observed_mutations_query_set = seq.views.common.get_observed_mutations(seq_experiment_ordered_dict)

    mutations = seq.models.Mutation.objects.filter(pk__in=observed_mutations_query_set.values_list("mutation", flat=True))

    for mutation in mutations:
        print(mutation.gene)