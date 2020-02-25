from fixation.util import get_fixed_obs_mut_qryset
from seq.views.mutation_table_builder import get_mutation_table_data, HTML_MUTATION_TABLE_HEADER
from django.utils.html import strip_tags
from converge.util import get_converge_obs_mut_qryset

import collections
from filter.util import filter_observed_mutations
from seq.util import get_observed_mutation_queryset, get_ordered_reseq_dict

MUT_TYPE_STR = "mut"
FIXED_MUT_TYPE_STR = "fixed_mut"
CONVERGED_MUT_TYPE_STR = "converged_mut"


def get_csv_str(exp_id, mut_type_str):
    if mut_type_str == FIXED_MUT_TYPE_STR:
        obs_mut_qryset = get_fixed_obs_mut_qryset(exp_id)
    elif mut_type_str == CONVERGED_MUT_TYPE_STR:
        obs_mut_qryset = get_converge_obs_mut_qryset(exp_id)
    else:
        obs_mut_qryset = get_observed_mutation_queryset(exp_id)

    observed_mutations = filter_observed_mutations(obs_mut_qryset, exp_id)
    reseq_ordered_dict = get_ordered_reseq_dict(observed_mutations)

    mutations, table_entry_list, mutation_index_dict = get_mutation_table_data(reseq_ordered_dict, observed_mutations)

    mut_pos_index = 3
    rows = [
        HTML_MUTATION_TABLE_HEADER[mut_pos_index:] + [reseq_ordered_dict[reseq].exp_ale_flask_isolate_str for reseq in
                                                      reseq_ordered_dict]]

    rows += ([
            "" if mutation.reseq_reference is None else mutation.reseq_reference,
            format(mutation.position, ',d'),
            mutation.mutation_type,
            mutation.sequence_change,
            mutation.gene,
            "" if mutation.function is None else mutation.function,
            "" if mutation.product is None else mutation.product,
            "" if mutation.go_process is None else mutation.go_process,
            "" if mutation.go_component is None else mutation.go_component,
            mutation.id,
            strip_tags(mutation.protein_change)] + _strip_tags_from_list(
        table_entry_list[mutation_index_dict[mutation.id]])
             for mutation in mutations)
    # print(str(datetime.now()), "after get rows")
    return rows


def _strip_tags_from_list(frequencies):
    temp = []
    for frequency in frequencies:
        temp.append(strip_tags(frequency))
    return temp

