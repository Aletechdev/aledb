from dashboard.models import ObservedMutationCounts, UniqueMutationCounts, SampleCounts, BarCharts
from seq.models import ObservedMutation, Mutation
from filter.util import filter_observed_mutations, build_filtered_observed_mutation_queryset
from genes.util import get_gene_list
from seq.util import get_mutations_from_observed_muations
from seq.views.common import MUTATION_TYPE_LIST, FUNCTIONAL_CHANGE_TYPE_LIST, UNANNOTATED
from ale.models import AleId, Isolate, Flask
from django.db.models import Q


def rebuild_dashboard_data():
    rebuild_sample_counts()
    rebuild_mutation_counts()


def rebuild_sample_counts():
    if SampleCounts.objects.all().count() == 0:
        SampleCounts.objects.create()
    ale_count = AleId.objects.filter(~Q(ale_id=0)).count()
    SampleCounts.objects.all().update(ale_count=ale_count)
    flask_count = Flask.objects.filter(~Q(ale_id__ale_id=0)).count()
    SampleCounts.objects.all().update(flask_count=flask_count)
    isolate_count = Isolate.objects.filter(~Q(flask__ale_id__ale_id=0)).count()
    SampleCounts.objects.all().update(isolate_count=isolate_count)
    print(ale_count, flask_count, isolate_count)


# Chunk size for streaming the observed-mutation table; bounds client memory.
OBS_MUT_COUNT_CHUNK_SIZE = 100000


def _compute_mutation_count_stats(observed_mutation_queryset):
    """
    Tally the same counts the old filter_observed_mutations + in-memory loops
    produced, but by streaming id-keyed chunks of a few slim columns instead of
    materializing every ObservedMutation with its related objects — the full
    table (5.8M+ rows) no longer fits in the host's RAM (see
    docs/ISSUE_upload_metadata_skipped_on_oom.md).
    """
    queryset, global_filter_genes, exp_filter_genes_map = build_filtered_observed_mutation_queryset(
        observed_mutation_queryset)
    apply_gene_filters = len(global_filter_genes) > 0 or len(exp_filter_genes_map) > 0
    deleted_global_mutations = set()
    obs_total = 0
    obs_mut_count_dict = {mut_type: 0 for mut_type in MUTATION_TYPE_LIST}
    obs_mut_func_change_type_dict = {func_change_type: 0 for func_change_type in FUNCTIONAL_CHANGE_TYPE_LIST}
    mut_classification = {}  # mutation id -> (mutation type, functional change type)
    last_id = 0
    while True:
        rows = list(queryset.filter(id__gt=last_id).order_by('id').values_list(
            'id', 'mutation_id', 'mutation__mutation_type', 'mutation__protein_change', 'mutation__gene',
            'sequencing_experiment__tech_rep__isolate__flask__ale_id__ale_experiment_id',
        )[:OBS_MUT_COUNT_CHUNK_SIZE])
        if not rows:
            break
        for obs_id, mut_id, mutation_type, protein_change, gene, experiment_id in rows:
            # Same per-row logic (and operator precedence) as filter_observed_mutations.
            deleted = mut_id in deleted_global_mutations
            if apply_gene_filters:
                if not deleted and len(global_filter_genes) > 0 or experiment_id in exp_filter_genes_map:
                    genes = set(get_gene_list(gene))
                    if len(global_filter_genes) >= len(genes) and genes.issubset(global_filter_genes):
                        deleted_global_mutations.add(mut_id)
                        deleted = True
                    elif experiment_id in exp_filter_genes_map:
                        exp_filter_genes = exp_filter_genes_map[experiment_id]
                        if len(exp_filter_genes) >= len(genes) and genes.issubset(exp_filter_genes):
                            deleted = True
            if deleted:
                continue
            classification = mut_classification.get(mut_id)
            if classification is None:
                mut_type = mutation_type if mutation_type in MUTATION_TYPE_LIST else UNANNOTATED
                func_type = UNANNOTATED
                for functional_change_type in FUNCTIONAL_CHANGE_TYPE_LIST:
                    if functional_change_type in protein_change:
                        func_type = functional_change_type
                        break
                classification = (mut_type, func_type)
                mut_classification[mut_id] = classification
            obs_total += 1
            obs_mut_count_dict[classification[0]] += 1
            obs_mut_func_change_type_dict[classification[1]] += 1
        last_id = rows[-1][0]

    mut_count_dict = {mut_type: 0 for mut_type in MUTATION_TYPE_LIST}
    mut_func_change_type_dict = {func_change_type: 0 for func_change_type in FUNCTIONAL_CHANGE_TYPE_LIST}
    for mut_type, func_type in mut_classification.values():
        mut_count_dict[mut_type] += 1
        mut_func_change_type_dict[func_type] += 1

    return {
        'obs_total': obs_total,
        'mut_total': len(mut_classification),
        'obs_mut_count_dict': obs_mut_count_dict,
        'obs_mut_func_change_type_dict': obs_mut_func_change_type_dict,
        'mut_count_dict': mut_count_dict,
        'mut_func_change_type_dict': mut_func_change_type_dict,
    }


def rebuild_mutation_counts():
    stats = _compute_mutation_count_stats(ObservedMutation.objects.all())

    if ObservedMutationCounts.objects.all().count() == 0:
        ObservedMutationCounts.objects.create()
    obs_mut_count_qryset = ObservedMutationCounts.objects.all()
    if UniqueMutationCounts.objects.all().count() == 0:
        UniqueMutationCounts.objects.create()
    mut_count_qryset = UniqueMutationCounts.objects.all()

    print("obs_mut ", stats['obs_total'])
    obs_mut_count_qryset.update(total=stats['obs_total'])
    print('muts', stats['mut_total'])
    mut_count_qryset.update(total=stats['mut_total'])

    mut_count_dict = stats['mut_count_dict']
    mut_func_change_type_dict = stats['mut_func_change_type_dict']
    obs_mut_count_dict = stats['obs_mut_count_dict']
    obs_mut_func_change_type_dict = stats['obs_mut_func_change_type_dict']

    total_mut_cnt = 0
    total_obs_mut_cnt = 0
    for mutation_type in MUTATION_TYPE_LIST:
        observed_mutation_type_count = obs_mut_count_dict[mutation_type]
        unique_mutation_type_count = mut_count_dict[mutation_type]
        print(mutation_type, observed_mutation_type_count, unique_mutation_type_count)
        total_obs_mut_cnt += observed_mutation_type_count
        total_mut_cnt += unique_mutation_type_count
        if mutation_type == 'SNP':
            obs_mut_count_qryset.update(single_base_substitution=observed_mutation_type_count)
            mut_count_qryset.update(single_base_substitution=unique_mutation_type_count)
        elif mutation_type == 'SUB':
            obs_mut_count_qryset.update(multiple_base_substitution=observed_mutation_type_count)
            mut_count_qryset.update(multiple_base_substitution=unique_mutation_type_count)
        elif mutation_type == 'DEL':
            obs_mut_count_qryset.update(deletion=observed_mutation_type_count)
            mut_count_qryset.update(deletion=unique_mutation_type_count)
        elif mutation_type == 'INS':
            obs_mut_count_qryset.update(insertion=observed_mutation_type_count)
            mut_count_qryset.update(insertion=unique_mutation_type_count)
        elif mutation_type == 'MOB':
            obs_mut_count_qryset.update(mobile_element_insertion=observed_mutation_type_count)
            mut_count_qryset.update(mobile_element_insertion=unique_mutation_type_count)
        elif mutation_type == 'AMP':
            obs_mut_count_qryset.update(amplification=observed_mutation_type_count)
            mut_count_qryset.update(amplification=unique_mutation_type_count)
        elif mutation_type == 'CON':
            obs_mut_count_qryset.update(gene_conversion=observed_mutation_type_count)
            mut_count_qryset.update(gene_conversion=unique_mutation_type_count)
        elif mutation_type == 'INV':
            obs_mut_count_qryset.update(inversion=observed_mutation_type_count)
            mut_count_qryset.update(inversion=unique_mutation_type_count)
    if total_mut_cnt != stats['mut_total']:
        print("mut count does not match", total_mut_cnt, stats['mut_total'])
    if total_obs_mut_cnt != stats['obs_total']:
        print("obs mut count does not match: ", total_obs_mut_cnt, stats['obs_total'])

    for functional_change_type in FUNCTIONAL_CHANGE_TYPE_LIST:
        observed_mutation_type_count = obs_mut_func_change_type_dict[functional_change_type]
        unique_mutation_type_count = mut_func_change_type_dict[functional_change_type]
        if functional_change_type == 'intergenic':
            obs_mut_count_qryset.update(intergenic=observed_mutation_type_count)
            mut_count_qryset.update(intergenic=unique_mutation_type_count)
        elif functional_change_type == 'noncoding':
            obs_mut_count_qryset.update(noncoding=observed_mutation_type_count)
            mut_count_qryset.update(noncoding=unique_mutation_type_count)
        elif functional_change_type == 'pseudogene':
            obs_mut_count_qryset.update(pseudogene=observed_mutation_type_count)
            mut_count_qryset.update(pseudogene=unique_mutation_type_count)
        elif functional_change_type == 'snp_type_synonymous':
            obs_mut_count_qryset.update(synonymous=observed_mutation_type_count)
            mut_count_qryset.update(synonymous=unique_mutation_type_count)
        elif functional_change_type == 'snp_type_nonsynonymous':
            obs_mut_count_qryset.update(nonsynonymous=observed_mutation_type_count)
            mut_count_qryset.update(nonsynonymous=unique_mutation_type_count)
        elif functional_change_type == UNANNOTATED:
            obs_mut_count_qryset.update(unannotated=observed_mutation_type_count)
            mut_count_qryset.update(unannotated=unique_mutation_type_count)


def _find_functional_change_type(mutation:Mutation)->str:
    for functional_change_type in FUNCTIONAL_CHANGE_TYPE_LIST:
        if functional_change_type in mutation.protein_change:
            return functional_change_type;
    return UNANNOTATED


def _find_mutation_type(mutation:Mutation)->str:
    if mutation.mutation_type in MUTATION_TYPE_LIST:
        return mutation.mutation_type
    return UNANNOTATED
