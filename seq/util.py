import collections

from seq.models import ObservedMutation, ResequencingExperiment, Mutation


def get_all_observed_mutations(reseq_id_list):
    return ObservedMutation.objects.filter(sequencing_experiment_id__in=reseq_id_list)


def get_ordered_reseq_queryset(ale_experiment_id, ale_id=None):
    reseq_qryset = ResequencingExperiment.objects.select_related(
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
    return reseq_qryset


def get_reseq_ordered_dict(ale_experiment_id, ale_no=None, request=None):
    """
    Args:
        ale_experiment_id:
        ale_no:

    Returns:
        reseq_ordered_dict: a ordered dictionary of reseq values and their ID's as keys.
        The reseq values within the dictionary will be ordered according to that
        defined within RESEQ_QUERY
        :param request:

    """
    reseq_queryset = get_ordered_reseq_queryset(ale_experiment_id, ale_no)
    if request and request.GET.get('tag_select'):
        tag = request.GET.get('tag_select').split(':')
        if tag[0] == 'Hide Tag':
            reseq_queryset = reseq_queryset.exclude(tech_rep__tags__contains=tag[1].replace(' ', ''))
        elif tag[0] == 'Show Tag':
            reseq_queryset = reseq_queryset.filter(tech_rep__tags__contains=tag[1].replace(' ', ''))
    reseq_ordered_dict = collections.OrderedDict((reseq.id, reseq) for reseq in reseq_queryset)
    return reseq_ordered_dict


def get_mut_queryset_from_obs_mut_queryset(observed_mutations_queryset):
    return Mutation.objects.filter(pk__in=observed_mutations_queryset.values_list("mutation", flat=True))


def get_unique_obs_mut_queryset_from_obs_mut_queryset(observed_mutations_queryset):
    """
    Updated by R. Cai
    This method get one observed mutation for each mutation (??). The observed mutation is used
    to extract strain information to decide if a 'gene linked' is need for display
    :param observed_mutations_queryset:
    :return: dict that map mutation_id to one observed mutation
    """
    unique_obs_mut = {observed_mutation.mutation.id: observed_mutation for observed_mutation in observed_mutations_queryset}
    return unique_obs_mut
