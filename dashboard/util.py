from dashboard.models import ObservedMutationCounts, UniqueMutationCounts, SampleCounts, BarCharts
from seq.models import ObservedMutation
from filter.util import filter_obs_muts
from common.util import get_mut_queryset_from_obs_mut_queryset
from seq.views.common import MUTATION_TYPE_LIST, FUNCTIONAL_CHANGE_TYPE_LIST
from ale.models import AleId, Isolate, Flask
from django.db.models import Q
from stats.util import get_histogram_jsons, MAX_HISTOGRAM_SIZE


def rebuild_dashboard_counts():
    rebuild_mutation_counts()
    rebuild_sample_counts()
    rebuild_mut_histogram_data()


def rebuild_mut_histogram_data():
    if ObservedMutation.objects.all().count() == 0:
        ObservedMutation.objects.create()
    raw_obs_mut_qryset = ObservedMutation.objects.all()
    obs_mut_qryset = filter_obs_muts(raw_obs_mut_qryset)
    genes_json, sequence_change_json = get_histogram_jsons(obs_mut_qryset, MAX_HISTOGRAM_SIZE)
    if BarCharts.objects.all().count() == 0:
        BarCharts.objects.create()
    histogram_data = BarCharts.objects.all()
    histogram_data.update(mut_gene_json=genes_json)
    histogram_data.update(mut_json=sequence_change_json)


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
    obs_mut_qryset = filter_obs_muts(raw_obs_mut_qryset)
    mut_qryset = get_mut_queryset_from_obs_mut_queryset(obs_mut_qryset)

    if ObservedMutationCounts.objects.all().count() == 0:
        ObservedMutationCounts.objects.create()
    obs_mut_count_qryset = ObservedMutationCounts.objects.all()
    if UniqueMutationCounts.objects.all().count() == 0:
        UniqueMutationCounts.objects.create()
    mut_count_qryset = UniqueMutationCounts.objects.all()

    # TODO: there has to be a better way than the below. It's full of unnecessary repetition.
    obs_mut_count_qryset.update(total=obs_mut_qryset.count())
    mut_count_qryset.update(total=mut_qryset.count())
    for mutation_type in MUTATION_TYPE_LIST:
        observed_mutation_type_count = obs_mut_qryset.filter(mutation__mutation_type=mutation_type).count()
        unique_mutation_type_count = mut_qryset.filter(mutation_type=mutation_type).count()
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
        elif mutation_type == 'DUP':
            obs_mut_count_qryset.update(duplication=observed_mutation_type_count)
            mut_count_qryset.update(duplication=unique_mutation_type_count)
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
        observed_mutation_type_count = obs_mut_qryset.filter(mutation__protein_change__contains=functional_change_type).count()
        unique_mutation_type_count = mut_qryset.filter(protein_change__contains=functional_change_type).count()
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