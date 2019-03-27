
from filter.models import AleExperimentFilter, GlobalFilter
import seq.models
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist
from genes.util import get_gene_list
from common.util import is_int

__author__ = 'Patrick Phaneuf'

NO_BREAK_STRING_CODE = u'\xa0'


def filter_observed_mutations(observed_mutation_queryset, experiment_id=None):
    """
    R. Cai - 1/19/2019
    :param observed_mutation_queryset:
    :param experiment_id: experiment_id for the observed_mutation_queryset
    :return: list of observed_mutations sorted and loaded with related objects
    """
    if experiment_id:
        exp_filters = AleExperimentFilter.objects.filter(ale_experiment_id=experiment_id)
    else:
        exp_filters = AleExperimentFilter.objects.filter(ale_experiment_id__in=observed_mutation_queryset.values(
            "sequencing_experiment__tech_rep__isolate__flask__ale_id__ale_experiment_id"))
    global_filter_genes, global_filter_muts = _get_global_filter_genes_muts()
    exp_filter_genes_map = dict()

    # filter muts by global filter
    q_queries = Q()
    if len(global_filter_muts) > 0:
        q_queries.add(Q(mutation__id__in=global_filter_muts), Q.OR)
    # filter muts by experiment filters
    for exp_filter in exp_filters:
        exp_filter_genes, exp_filter_muts = _get_exp_filter_genes_muts(exp_filter)
        if len(exp_filter_genes) > 0:
            exp_filter_genes_map[exp_filter.ale_experiment_id] = exp_filter_genes

        q_exp = Q()
        if exp_filter.min_cutoff and exp_filter.min_cutoff > 0:
            q_exp.add(Q(frequency__lt=exp_filter.min_cutoff / 100), Q.OR)
        if exp_filter.max_cutoff and exp_filter.max_cutoff < 100:
            q_exp.add(Q(frequency__gt=exp_filter.max_cutoff / 100), Q.OR)
        if len(exp_filter_muts) > 0:
            q_exp.add(Q(mutation__id__in=exp_filter_muts), Q.OR)
        exp_q_query = Q(
            sequencing_experiment__tech_rep__isolate__flask__ale_id__ale_experiment__ale_id=exp_filter.ale_experiment_id)
        exp_q_query.add(q_exp, Q.AND)
        q_queries.add(exp_q_query, Q.OR)
    queryset = observed_mutation_queryset.exclude(q_queries)

    # filter genes
    queryset = queryset.select_related(
        'sequencing_experiment__tech_rep__isolate__flask__ale_id__ale_experiment', 'mutation'
    ).order_by(
        'sequencing_experiment__tech_rep__isolate__flask__ale_id__ale_experiment__name',
        'sequencing_experiment__tech_rep__isolate__flask__ale_id__ale_id',
        'sequencing_experiment__tech_rep__isolate__flask__flask_number',
        'sequencing_experiment__tech_rep__isolate__isolate_number',
        'sequencing_experiment__tech_rep__tech_rep_number'
    )
    observed_mutations = []
    deleted_global_mutations = {}
    if len(global_filter_genes) > 0 or len(exp_filter_genes_map) > 0:
        for obs_mut in queryset:
            deleted = obs_mut.mutation.id in deleted_global_mutations
            if not deleted and len(global_filter_genes) > 0 or obs_mut.get_experiment_id() in exp_filter_genes_map:
                genes = set(get_gene_list(obs_mut.mutation.gene))
                if len(global_filter_genes) >= len(genes) and genes.issubset(global_filter_genes):
                    deleted_global_mutations.add(obs_mut.mutation.id)
                    deleted = True
                elif obs_mut.get_experiment_id() in exp_filter_genes_map:
                    exp_filter_genes = exp_filter_genes_map[obs_mut.get_experiment_id()]
                    if len(exp_filter_genes) >= len(genes) and genes.issubset(exp_filter_genes):
                        deleted = True
            if not deleted:
                observed_mutations.append(obs_mut)
    else:
        observed_mutations = [obs_mut for obs_mut in queryset]
    return observed_mutations


def _get_global_filter_genes_muts():
    ignored_genes = []
    ignored_mutations = []
    f = get_global_filter()
    if f.ignored_mutations:
        ignored_mutations = get_ignored_mut_id_list_from_str(f.ignored_mutations)
    if f.ignored_genes:
        ignored_genes = get_gene_list(f.ignored_genes)
    return set(ignored_genes), ignored_mutations


def _get_exp_filter_genes_muts(exp_filter: AleExperimentFilter):
    ignored_genes = []
    ignored_mutations = []
    if exp_filter.ignored_mutations:
        ignored_mutations = get_ignored_mut_id_list_from_str(exp_filter.ignored_mutations)
    if exp_filter.starting_strain_mutations:
        ignored_mutations += get_ignored_mut_id_list_from_str(exp_filter.starting_strain_mutations)
    if exp_filter.ignored_genes:
        ignored_genes = get_gene_list(exp_filter.ignored_genes)
    return set(ignored_genes), ignored_mutations


def get_ignored_mut_id_list_from_str(ignored_mutation_id_str, deleted_mutation_id=None):
    if not ignored_mutation_id_str:
        return []

    ignored_mutation_ids = ignored_mutation_id_str.split(",")
    deleted_mutation_ids = []
    if deleted_mutation_id:
        deleted_mutation_ids = deleted_mutation_id.split(",")

    new_list = [mut_id for mut_id in ignored_mutation_ids if is_int(mut_id) and mut_id not in deleted_mutation_ids]
    return new_list


def _get_ignored_gene_list_from_str(ignored_genes):

    if not ignored_genes:
        return []

    if ignored_genes.endswith(','):
        ignored_genes = ignored_genes[:-1]

    if ignored_genes.startswith(','):
        ignored_genes = ignored_genes[1:]

    ignored_genes = ignored_genes.replace(" ", "").replace('\n', '').replace('\r', '').split(',')
    cleaned_list = []

    for gene in ignored_genes:

        if gene == '' or not gene:
            continue

        cleaned_list.append(gene)

    return cleaned_list


def _mutation_exists(mut_id):
    try:
        seq.models.Mutation.objects.get(id=mut_id)
        return True
    except ObjectDoesNotExist:
        return False


def get_global_filter():
    global_filter, created = GlobalFilter.objects.get_or_create(id=1)
    return global_filter
