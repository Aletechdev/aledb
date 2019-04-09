from dashboard.models import ObservedMutationCounts, UniqueMutationCounts, SampleCounts, BarCharts
from seq.models import ObservedMutation
from filter.util import filter_observed_mutations
from seq.util import get_mutations_from_observed_muations
from seq.views.common import MUTATION_TYPE_LIST, FUNCTIONAL_CHANGE_TYPE_LIST
from ale.models import AleId, Isolate, Flask
from django.db.models import Q
from stats.util import generate_histogram_jsons, MAX_HISTOGRAM_SIZE


def rebuild_dashboard_data():
    rebuild_mutation_counts()
    rebuild_sample_counts()
    rebuild_mut_histogram_data()


def rebuild_mut_histogram_data():
    if ObservedMutation.objects.all().count() == 0:
        ObservedMutation.objects.create()
    raw_obs_mut_qryset = ObservedMutation.objects.all()
    obs_mutations = filter_observed_mutations(raw_obs_mut_qryset)
    genes_json = generate_histogram_jsons(obs_mutations)
    if BarCharts.objects.all().count() == 0:
        BarCharts.objects.create()
    histogram_data = BarCharts.objects.all()
    histogram_data.update(mut_gene_json=genes_json)


def rebuild_sample_counts():
    if SampleCounts.objects.all().count() == 0:
        SampleCounts.objects.create()
    ale_count = AleId.objects.filter(~Q(ale_id=0)).count()
    SampleCounts.objects.all().update(ale_count=ale_count)
    flask_count = Flask.objects.filter(~Q(ale_id__ale_id=0)).count()
    SampleCounts.objects.all().update(flask_count=flask_count)
    isolate_count = Isolate.objects.filter(~Q(flask__ale_id__ale_id=0)).count()
    SampleCounts.objects.all().update(isolate_count=isolate_count)


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

    # TODO: there has to be a better way than the below. It's full of unnecessary repetition.
    obs_mut_count_qryset.update(total=len(obs_muts))
    mut_count_qryset.update(total=len(muts))
    for mutation_type in MUTATION_TYPE_LIST:
        observed_mutation_type_count = len([obs_mut for obs_mut in obs_muts if obs_mut.mutation.mutation_type==mutation_type])
        unique_mutation_type_count = len([mut for mut in muts if mut.mutation_type==mutation_type])
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

    for functional_change_type in FUNCTIONAL_CHANGE_TYPE_LIST:
        observed_mutation_type_count = len([obs_mut.mutation for obs_mut in obs_muts if functional_change_type in obs_mut.mutation.protein_change])
        unique_mutation_type_count = len([mut for mut in muts if functional_change_type in mut.protein_change])
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
