import collections
import seq.models
from common.util import is_int
from filter.util import filter_observed_mutations

HTML_ECOCYC = """<a href = "https://ecocyc.org/ECOLI/substring-search?type=GENE&object={gene}">{gene}</a>"""


def get_observed_mutation_queryset(experiment_id):
    return seq.models.ObservedMutation.objects.filter(sequencing_experiment__tech_rep__isolate__flask__ale_id__ale_experiment__ale_id=experiment_id)


def get_all_observed_muations_filtered(experiment_id, filter_type = None):
    queryset = get_observed_mutation_queryset(experiment_id)
    return filter_observed_mutations(queryset, experiment_id, filter_type)


def get_all_observed_mutations(reseq_id_list):
    return seq.models.ObservedMutation.objects.filter(sequencing_experiment_id__in=reseq_id_list)


def get_ordered_reseq_queryset(ale_experiment_id, ale_id=None, sample_type=None):
    reseq_qryset = seq.models.ResequencingExperiment.objects.select_related(
        'tech_rep__isolate__flask__ale_id__ale_experiment', 'tech_rep__isolate__flask__media'
    ).order_by(
        'tech_rep__isolate__flask__ale_id__ale_experiment__name',
        'tech_rep__isolate__flask__ale_id__ale_id',
        'tech_rep__isolate__flask__flask_number',
        'tech_rep__isolate__isolate_number',
        'tech_rep__tech_rep_number'
    )
    if ale_experiment_id:
        reseq_qryset = reseq_qryset.filter(tech_rep__isolate__flask__ale_id__ale_experiment__ale_id=ale_experiment_id)
    if ale_id:
        reseq_qryset = reseq_qryset.filter(tech_rep__isolate__flask__ale_id__ale_id=ale_id)
    if sample_type:
        flag = 0
        if sample_type == 'population':
            flag = 1
        reseq_qryset = reseq_qryset.filter(tech_rep__isolate__is_population=flag)
    return reseq_qryset


def get_reseq_ordered_dict(ale_experiment_id, ale_no=None, sample_type=None, request=None):
    """
    Args:
        ale_experiment_id:
        ale_no:
        sample_type: population sample

    Returns:
        reseq_ordered_dict: a ordered dictionary of reseq values and their ID's as keys.
        The reseq values within the dictionary will be ordered according to that
        defined within RESEQ_QUERY
        :param request:

    """
    reseq_queryset = get_ordered_reseq_queryset(ale_experiment_id, ale_no, sample_type)
    if request and request.GET.get('tag_select'):
        tag = request.GET.get('tag_select').split(':')
        if tag[0] == 'Hide Tag':
            reseq_queryset = reseq_queryset.exclude(tech_rep__tags__contains=tag[1].replace(' ', ''))
        elif tag[0] == 'Show Tag':
            reseq_queryset = reseq_queryset.filter(tech_rep__tags__contains=tag[1].replace(' ', ''))
    reseq_ordered_dict = collections.OrderedDict((reseq.id, reseq) for reseq in reseq_queryset)
    return reseq_ordered_dict


def get_mutations_from_observed_muations(observed_mutations):
    mut_map = {obs_mut.mutation.id: obs_mut.mutation for obs_mut in observed_mutations}
    return mut_map.values()


def get_ordered_reseq_dict(observed_mutations):
    """
    Get reseq {id: reseq} map
    :param observed_mutations:
    :return: ordered map
    """
    seq_experiment_ordered_dict = collections.OrderedDict()
    for observed_mutation in observed_mutations:
        seq_experiment_ordered_dict[observed_mutation.sequencing_experiment.id] = observed_mutation.sequencing_experiment
    return seq_experiment_ordered_dict


def get_ecocyc_gene_list(gene_list, is_ecocyc_gene: bool = False):
    url_list = []
    for each in gene_list:
        if each.startswith("<"):
            each = each.split(">")[-1]
        if is_ecocyc_gene:
            url_list.append(HTML_ECOCYC.format(gene=each))
        else:
            url_list.append(each)
    return url_list


def get_mutation_objects(mutations_id_str):
    """
    Get list of mutations for the ids
    :param mutations_id_str: mutation ids, in string, separated by ','
    :return: list of mutations from database
    """
    mutations = []
    if mutations_id_str and len(mutations_id_str)>0:
        mutations_ids = [mut_id for mut_id in mutations_id_str.split(',') if is_int(mut_id)]
        mutations = [mutation for mutation in seq.models.Mutation.objects.filter(id__in=mutations_ids)]
    return mutations


def get_ref_sequences():
    muts = seq.models.Mutation.objects.all()
    ref_seq_set = {mut.reseq_reference for mut in muts}
    ref_seq_list = [ref_seq for ref_seq in ref_seq_set if ref_seq]
    return sorted(ref_seq_list)


def get_matching_observed_mutation_ids(mutation_id, experiment_id):
    local_observed_mutations = seq.models.ObservedMutation.objects.filter(sequencing_experiment__tech_rep__isolate__flask__ale_id__ale_experiment__ale_id=experiment_id, mutation__id=mutation_id).order_by(
        'sequencing_experiment__tech_rep__isolate__flask__ale_id__ale_experiment__name',
        'sequencing_experiment__tech_rep__isolate__flask__ale_id__ale_id',
        'sequencing_experiment__tech_rep__isolate__flask__flask_number',
        'sequencing_experiment__tech_rep__isolate__isolate_number',
        'sequencing_experiment__tech_rep__tech_rep_number')
    return local_observed_mutations
