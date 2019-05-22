from dashboard.models import ObservedMutationCounts, UniqueMutationCounts, SampleCounts, BarCharts
from seq.models import ObservedMutation, Mutation
from filter.util import filter_observed_mutations
from seq.util import get_mutations_from_observed_muations
from seq.views.common import MUTATION_TYPE_LIST, FUNCTIONAL_CHANGE_TYPE_LIST, UNANNOTATED
from ale.models import AleId, Isolate, Flask
from django.db.models import Q
from stats.util import generate_histogram_jsons, MAX_HISTOGRAM_SIZE


def rebuild_dashboard_data():
    rebuild_sample_counts()
    rebuild_mutation_counts()
    # rebuild_mut_histogram_data()


def rebuild_mut_histogram_data():
    if ObservedMutation.objects.all().count() == 0:
        ObservedMutation.objects.create(mutation_id=-1)
    raw_obs_mut_qryset = ObservedMutation.objects.all()
    obs_mutations = filter_observed_mutations(raw_obs_mut_qryset)
    genes_json = generate_histogram_jsons(obs_mutations)
    if BarCharts.objects.all().count() == 0:
        BarCharts.objects.create()
    BarCharts.objects.all().update(mut_gene_json=genes_json)


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


def rebuild_mutation_counts():
    raw_obs_mut_qryset = ObservedMutation.objects.all()
    obs_muts = filter_observed_mutations(raw_obs_mut_qryset)
    muts = get_mutations_from_observed_muations(obs_muts)

    if ObservedMutationCounts.objects.all().count() == 0:
        ObservedMutationCounts.objects.create()
    obs_mut_count_qryset = ObservedMutationCounts.objects.all()
    if UniqueMutationCounts.objects.all().count() == 0:
        UniqueMutationCounts.objects.create()
    mut_count_qryset = UniqueMutationCounts.objects.all()

    print("obs_mut ", len(obs_muts))
    obs_mut_count_qryset.update(total=len(obs_muts))
    print('muts', len(muts))
    mut_count_qryset.update(total=len(muts))

    mut_count_dict = {mut_type: 0 for mut_type in MUTATION_TYPE_LIST}
    mut_func_change_type_dict = {func_change_type: 0 for func_change_type in FUNCTIONAL_CHANGE_TYPE_LIST}
    for mut in muts:
        mutation_type = _find_mutation_type(mut)
        mut_count_dict[mutation_type] = mut_count_dict[mutation_type] + 1
        functional_change_type = _find_functional_change_type(mut)
        mut_func_change_type_dict[functional_change_type] = mut_func_change_type_dict[functional_change_type] + 1

    obs_mut_count_dict = {mut_type: 0 for mut_type in MUTATION_TYPE_LIST}
    obs_mut_func_change_type_dict = {func_change_type: 0 for func_change_type in FUNCTIONAL_CHANGE_TYPE_LIST}
    for obs_mut in obs_muts:
        mutation_type = _find_mutation_type(obs_mut.mutation)
        obs_mut_count_dict[mutation_type] = obs_mut_count_dict[mutation_type] + 1
        functional_change_type = _find_functional_change_type(obs_mut.mutation)
        obs_mut_func_change_type_dict[functional_change_type] = obs_mut_func_change_type_dict[functional_change_type] + 1

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
    if total_mut_cnt != len(muts):
        print("mut count does not match", total_mut_cnt, len(muts))
    if total_obs_mut_cnt != len(obs_muts):
        print("obs mut count does not match: ", total_obs_mut_cnt, len(obs_muts))

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
