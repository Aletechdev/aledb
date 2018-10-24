from filter.models import AleExperimentFilter, GlobalFilter
from seq.models import Mutation, ObservedMutation
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist
from ale.models import AleExperiment
from genes.util import get_gene_list

__author__ = 'Patrick Phaneuf'

NO_BREAK_STRING_CODE = u'\xa0'

MODEL_TO_FILTER_MAPPINGS = {"protein": "protein_change",
                            "type": "mutation_type",
                            "sequence": "sequence_change",
                            "position": "position",
                            "gene": "gene"}

DELETE_ROW_BOX = """<td><img src="/static/close-icon.gif" onclick="delete_row(%d)" width="12" height="11" style="float:right; cursor:pointer"></td>"""

TABLE_HEADER = "<tr><td></td><td>Position</td><td>Mutation Type</td><td>Sequence Change</td><td>Gene</td><td>Function</td><td>Product</td><td>GO Process</td><td>GO Component</td><td>Details</td></tr>"


def get_filtered_observed_mutations_queryset(observed_mutation_queryset, filter_settings=None, mut_queryset=None):
    """
    R. Cai - updated 10/23/2018
    filter queryset based on AleExperimentFilters and GlobalFilter.
    if mut_queryset passed, use it to get all mutations
    otherwise, get mutations from observed_mutation_queryset
    :param observed_mutation_queryset:
    :param filter_settings:
    :param mut_queryset:
    :return: observed_mutation_queryset with experiment filters
    """
    if filter_settings:
        return _get_filtered_observed_mutations_queryset(observed_mutation_queryset, filter_settings, mut_queryset)

    if mut_queryset:
        mut_dict = {mutation.id: mutation for mutation in mut_queryset}
    else:
        # make sure mutations loaded
        observed_mutation_queryset = observed_mutation_queryset.select_related('mutation')
        mut_dict = {observed_mutation.mutation.id: observed_mutation.mutation for observed_mutation in
                    observed_mutation_queryset}
    global_filter = get_global_filter()
    # get experiment filters based on observed_mutations_queryset
    exp_qryset = AleExperiment.objects.filter(
        ale_id__in=observed_mutation_queryset.values(
            "sequencing_experiment__tech_rep__isolate__flask__ale_id__ale_experiment"))
    exp_dict = {exp.ale_id: exp for exp in exp_qryset}
    exp_filter_qryset = AleExperimentFilter.objects.filter(ale_experiment__ale_id__in=exp_dict.keys())
    exp_filter_dict = {exp_filter.ale_experiment_id: exp_filter for exp_filter in exp_filter_qryset}
    or_queries = Q()
    for exp_id, exp in exp_dict.items():
        exp_filter_settings = exp_filter_dict.get(exp_id)
        q_query = Q(sequencing_experiment__tech_rep__isolate__flask__ale_id__ale_experiment__ale_id=exp_id)
        q_query &= _filter_observed_mutations_given_filter_settings(mut_dict,
                                                                    exp_filter_settings,
                                                                    global_filter)
        or_queries.add(q_query, Q.OR)
    return observed_mutation_queryset.filter(or_queries)


def _get_filtered_observed_mutations_queryset(observed_mutation_queryset, filter_settings, mut_queryset=None):
    global_filter = get_global_filter()
    ignored_gene_list = _get_ignored_gene_list(filter_settings, global_filter)
    mut_dict = None
    if len(ignored_gene_list)>0:
        if mut_queryset:
            mut_dict = {mutation.id: mutation for mutation in mut_queryset}
        else:
            observed_mutation_queryset = observed_mutation_queryset.select_related('mutation')
            mut_dict = {observed_mutation.mutation.id: observed_mutation.mutation for observed_mutation in
                        observed_mutation_queryset}
    q_query = _filter_observed_mutations_given_filter_settings(mut_dict, filter_settings, global_filter)
    return observed_mutation_queryset.filter(q_query)


def _filter_observed_mutations_given_filter_settings(mutation_dict, filter_settings, global_filter=None):
    """
    Updated by R. Cai
    :param observed_mutation_queryset:
    :param filter_settings:
    :param global_filter:
    :return: Q query for the experiment filter
    """
    ignored_gene_list = _get_ignored_gene_list(filter_settings, global_filter)
    ignored_mut_list = _get_ignored_mut_list(filter_settings, global_filter)
    min_cutoff = 0
    max_cutoff = 100
    if filter_settings is not None:
        min_cutoff = filter_settings.min_cutoff
        max_cutoff = filter_settings.max_cutoff

    if mutation_dict:
        ignored_gene_mut_list = _get_ignored_genes_mutation_id_list(mutation_dict, ignored_gene_list)
        ignored_mut_list += ignored_gene_mut_list

    q_filters = Q(frequency__gte=min_cutoff / 100) & Q(frequency__lte=max_cutoff / 100)
    if len(ignored_mut_list) > 0:
        q_filters &= ~Q(mutation_id__in=ignored_mut_list)
    return q_filters


def _get_ignored_mut_list(filter_settings, global_filter):
    ignored_mut_list = []
    if filter_settings is not None:
        ignored_mut_str = filter_settings.ignored_mutations
        ignored_mut_list = get_ignored_mut_id_list_from_str(ignored_mut_str)
        starting_strain_mut_list = get_ignored_mut_id_list_from_str(filter_settings.starting_strain_mutations)
        ignored_mut_list += starting_strain_mut_list
    if global_filter:
        ignored_mut_list += get_ignored_mut_id_list_from_str(global_filter.ignored_mutations)
    return ignored_mut_list


def _get_ignored_gene_list(filter_settings, global_filter):
    ignored_gene_list = []
    if filter_settings:
        ignored_gene_list = _get_ignored_gene_list_from_str(filter_settings.ignored_genes)
    if global_filter:
        ignored_gene_list += _get_ignored_gene_list_from_str(global_filter.ignored_genes)
    return ignored_gene_list


def _get_ignored_genes_mutation_id_list(mutation_dict, ignored_genes):
    """
    Check gene names, and return list of ignored mutation_ids
    :param observed_mutation_queryset:
    :param ignored_genes:
    :return:
    """
    ignored_mutation_id_list = []
    if ignored_genes:
        if len(ignored_genes) > 0 and ignored_genes[0] is not '':
            for mut_id, mutation in mutation_dict.items():
                gene_list = get_gene_list(mutation.gene)
                if set(gene_list).issubset(set(ignored_genes)):
                    ignored_mutation_id_list.append(mutation.id)
    return ignored_mutation_id_list


def _ignored_muts_filter(observed_mutation_queryset, ignored_mutation_list):
    observed_mutation_queryset = observed_mutation_queryset.exclude(mutation_id__in=ignored_mutation_list)
    return observed_mutation_queryset


def is_number(s):
    try:
        int(s)
        return True
    except ValueError:
        return False


def _frequency_filter(observed_mutation_queryset, min_cutoff, max_cutoff):
    observed_mutation_queryset = observed_mutation_queryset.filter(frequency__gte=min_cutoff / 100, frequency__lte=max_cutoff / 100)
    return observed_mutation_queryset


def get_filter_settings(ale_experiment_id):
    filter_settings, created = AleExperimentFilter.objects.get_or_create(ale_experiment_id=ale_experiment_id)
    return filter_settings


def get_ignored_mut_id_list_from_str(ignored_mutation_id_str, deleted_mutation_id=None):

    if not ignored_mutation_id_str:
        return []

    if ignored_mutation_id_str.startswith(','):
        ignored_mutation_id_str = ignored_mutation_id_str[1:]

    ignored_mutation_id_str = ignored_mutation_id_str.split(",")

    new_list = []

    for mut_id in ignored_mutation_id_str:

        if mut_id in new_list or is_number(mut_id) is False:
            continue

        if deleted_mutation_id is None or mut_id != deleted_mutation_id:
            new_list.append(mut_id)

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


def get_ignored_mutations(filter_form_model):

    table_body = ""

    ignored_mutation_id_str = filter_form_model.ignored_mutations

    ignored_mutation_id_list = get_ignored_mut_id_list_from_str(ignored_mutation_id_str)

    for mut_id in ignored_mutation_id_list:
        try:
            mutation = Mutation.objects.get(id=mut_id)
        except ObjectDoesNotExist:
            continue

        table_row = '<tr id="%s">' % mutation.id
        table_row += DELETE_ROW_BOX % mutation.id
        table_row += "<td>%s</td>" % format(int(mutation.position), ',d')
        table_row += "<td>%s</td>" % mutation.mutation_type
        table_row += "<td>%s</td>" % mutation.sequence_change
        table_row += "<td><a href=/gene?g=%s>%s</a></td>" % (mutation.gene, mutation.gene)
        table_row += "<td>%s</td>" % ("" if mutation.function is None else mutation.function)
        table_row += "<td>%s</td>" % ("" if mutation.product is None else mutation.product)
        table_row += "<td>%s</td>" % ("" if mutation.go_process is None else mutation.go_process)
        table_row += "<td>%s</td>" % ("" if mutation.go_component is None else mutation.go_component)
        table_row += "<td>%s</td>" % mutation.protein_change
        table_row += "</tr>"
        table_body += table_row

    if table_body is None:
        table_body = []

    return table_body, ignored_mutation_id_list


def _mutation_exists(mut_id):
    try:
        Mutation.objects.get(id=mut_id)
        return True
    except ObjectDoesNotExist:
        return False


def get_global_filter():
    global_filter, created = GlobalFilter.objects.get_or_create(id=1)
    return global_filter
