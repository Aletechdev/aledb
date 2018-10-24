from common.util import get_reseq_ordered_dict
from fixation.util import get_exp_fixed_obs_mut_qryset
from seq.views.mutation_table_builder import \
    get_mutation_table_queryset_and_entry_list_for_export, \
    HTML_MUTATION_TABLE_HEADER
from django.utils.html import strip_tags
from combine.views.common import get_exp_ordered_reseq_dict_and_obs_mut_queryset
from converge.util import get_converge_obs_mut_qryset
from datetime import datetime

MUT_TYPE_STR = "mut"
FIXED_MUT_TYPE_STR = "fixed_mut"
CONVERGED_MUT_TYPE_STR = "converged_mut"


def get_csv_str(exp_id, mut_type_str):
    print(str(datetime.now()), exp_id, mut_type_str)
    filtered = False
    if mut_type_str == FIXED_MUT_TYPE_STR:
        reseq_ordered_dict = get_reseq_ordered_dict(exp_id)
        obs_mut_qryset = get_exp_fixed_obs_mut_qryset(reseq_ordered_dict)
    elif mut_type_str == CONVERGED_MUT_TYPE_STR:
        reseq_ordered_dict = get_reseq_ordered_dict(exp_id)
        obs_mut_qryset = get_converge_obs_mut_qryset(reseq_ordered_dict)
    else:
        reseq_ordered_dict, \
        obs_mut_qryset = get_exp_ordered_reseq_dict_and_obs_mut_queryset(exp_id)
        filtered = True

    obs_mut_qryset = obs_mut_qryset.select_related(
        'sequencing_experiment__tech_rep__isolate__flask__ale_id__ale_experiment',
        'mutation'
    )
    # R. Cai: removed var filtered_observed_mutations since it was not used
    mut_qryset, \
    table_entry_list, \
    mut_index_dict = get_mutation_table_queryset_and_entry_list_for_export(reseq_ordered_dict, obs_mut_qryset, exp_id,
                                                                           not filtered)

    mut_pos_index = 3
    # TODO: harden below against an empty reseq_ordered_dict
    rows = [
        HTML_MUTATION_TABLE_HEADER[mut_pos_index:] + [reseq_ordered_dict[reseq].exp_ale_flask_isolate_str for reseq in
                                                      reseq_ordered_dict]]

    rows += ([format(mutation.position, ',d'),
              mutation.mutation_type,
              mutation.sequence_change,
              mutation.gene,
              "" if mutation.function is None else mutation.function,
              "" if mutation.product is None else mutation.product,
              "" if mutation.go_process is None else mutation.go_process,
              "" if mutation.go_component is None else mutation.go_component,
              strip_tags(mutation.protein_change)] + _strip_tags_from_list(
        table_entry_list[mut_index_dict[mutation.id]])
             for mutation in mut_qryset)
    print(str(datetime.now()), "after get rows")
    return rows


def _strip_tags_from_list(frequencies):
    temp = []
    for frequency in frequencies:
        temp.append(strip_tags(frequency))
    return temp
