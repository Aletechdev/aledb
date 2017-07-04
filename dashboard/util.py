from dashboard.models import ObservedMutationCounts, UniqueMutationCounts, SampleCounts
from seq.models import ObservedMutation
from filter.util import dashboard_filter
from common.db_util import get_mutation_queryset_from_obs_mut_queryset
from seq.views.common import MUTATION_TYPE_LIST, FUNCTIONAL_CHANGE_TYPE_LIST
from ale.models import AleId, Isolate, Flask
from django.db.models import Q


def rebuild_dashboard_counts():
    rebuild_mutation_counts()
    rebuild_sample_counts()


def rebuild_sample_counts():
    if SampleCounts.objects.all().count() == 0:
        SampleCounts.objects.create()
    ale_count = AleId.objects.filter(~Q(ale_id=0)).count()
    SampleCounts.objects.all().update(ale_count=ale_count)
    flask_count = Flask.objects.filter(~Q(ale_id__ale_id=0)).count()
    SampleCounts.objects.all().update(flask_count=flask_count)
    isolate_count = Isolate.objects.filter(~Q(flask__ale_id__ale_id=0)).count()
    SampleCounts.objects.all().update(isolate_count=isolate_count)


# TODO: build unit test for this.
def rebuild_mutation_counts():
    observed_mutation_count_queryset = ObservedMutationCounts.objects.all()
    if observed_mutation_count_queryset.count() == 0:
        ObservedMutationCounts.objects.create()
        observed_mutation_count_queryset = ObservedMutationCounts.objects.all()
    unique_mutation_count_queryset = UniqueMutationCounts.objects.all()
    if unique_mutation_count_queryset.count() == 0:
        UniqueMutationCounts.objects.create()
        unique_mutation_count_queryset = UniqueMutationCounts.objects.all()

    raw_observed_mutation_queryset = ObservedMutation.objects.all()
    observed_mutation_queryset = dashboard_filter(raw_observed_mutation_queryset)
    unique_mutation_queryset = get_mutation_queryset_from_obs_mut_queryset(observed_mutation_queryset)

    # TODO: there has to be a better way than the below. It's full of unnecessary repetition.
    observed_mutation_count_queryset.update(total=observed_mutation_queryset.count())
    unique_mutation_count_queryset.update(total=unique_mutation_queryset.count())
    for mutation_type in MUTATION_TYPE_LIST:
        observed_mutation_type_count = observed_mutation_queryset.filter(mutation__mutation_type=mutation_type).count()
        unique_mutation_type_count = unique_mutation_queryset.filter(mutation_type=mutation_type).count()
        if mutation_type == 'SNP':
            observed_mutation_count_queryset.update(single_base_substitution=observed_mutation_type_count)
            unique_mutation_count_queryset.update(single_base_substitution=unique_mutation_type_count)
        elif mutation_type == 'SUB':
            observed_mutation_count_queryset.update(multiple_base_substitution=observed_mutation_type_count)
            unique_mutation_count_queryset.update(multiple_base_substitution=unique_mutation_type_count)
        elif mutation_type == 'DEL':
            observed_mutation_count_queryset.update(deletion=observed_mutation_type_count)
            unique_mutation_count_queryset.update(deletion=unique_mutation_type_count)
        elif mutation_type == 'INS':
            observed_mutation_count_queryset.update(insertion=observed_mutation_type_count)
            unique_mutation_count_queryset.update(insertion=unique_mutation_type_count)
        elif mutation_type == 'MOB':
            observed_mutation_count_queryset.update(mobile_element_insertion=observed_mutation_type_count)
            unique_mutation_count_queryset.update(mobile_element_insertion=unique_mutation_type_count)
        elif mutation_type == 'DUP':
            observed_mutation_count_queryset.update(duplication=observed_mutation_type_count)
            unique_mutation_count_queryset.update(duplication=unique_mutation_type_count)
        elif mutation_type == 'AMP':
            observed_mutation_count_queryset.update(amplification=observed_mutation_type_count)
            unique_mutation_count_queryset.update(amplification=unique_mutation_type_count)
        elif mutation_type == 'CON':
            observed_mutation_count_queryset.update(gene_conversion=observed_mutation_type_count)
            unique_mutation_count_queryset.update(gene_conversion=unique_mutation_type_count)
        elif mutation_type == 'INV':
            observed_mutation_count_queryset.update(inversion=observed_mutation_type_count)
            unique_mutation_count_queryset.update(inversion=unique_mutation_type_count)

    for functional_change_type in FUNCTIONAL_CHANGE_TYPE_LIST:
        observed_mutation_type_count = observed_mutation_queryset.filter(mutation__protein_change__contains=functional_change_type).count()
        unique_mutation_type_count = unique_mutation_queryset.filter(protein_change__contains=functional_change_type).count()
        if functional_change_type == 'intergenic':
            observed_mutation_count_queryset.update(intergenic=observed_mutation_type_count)
            unique_mutation_count_queryset.update(intergenic=unique_mutation_type_count)
        elif functional_change_type == 'noncoding':
            observed_mutation_count_queryset.update(noncoding=observed_mutation_type_count)
            unique_mutation_count_queryset.update(noncoding=unique_mutation_type_count)
        elif functional_change_type == 'pseudogene':
            observed_mutation_count_queryset.update(pseudogene=observed_mutation_type_count)
            unique_mutation_count_queryset.update(pseudogene=unique_mutation_type_count)
        elif functional_change_type == 'snp_type_synonymous':
            observed_mutation_count_queryset.update(synonymous=observed_mutation_type_count)
            unique_mutation_count_queryset.update(synonymous=unique_mutation_type_count)
        elif functional_change_type == 'snp_type_nonsynonymous':
            observed_mutation_count_queryset.update(nonsynonymous=observed_mutation_type_count)
            unique_mutation_count_queryset.update(nonsynonymous=unique_mutation_type_count)