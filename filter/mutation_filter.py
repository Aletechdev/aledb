from filter.models import AleExperimentFilter, GlobalFilter

from seq.models import Mutation

from django.core.exceptions import ObjectDoesNotExist

from ale.models import AleExperiment

__author__ = 'Patrick Phaneuf'

NO_BREAK_STRING_CODE = u'\xa0'

MODEL_TO_FILTER_MAPPINGS = {"protein": "protein_change",
                            "type": "mutation_type",
                            "sequence": "sequence_change",
                            "position": "position",
                            "gene": "gene"}

DELETE_ROW_BOX = """<td><img src="/static/DataTables/media/images/close-icon.gif" onclick="delete_row(%d)" width="12" height="11" style="float:right; cursor:pointer"></a></td>"""

TABLE_HEADER = "<tr><td></td><td>Position</td><td>Mutation Type</td><td>Sequence Change</td><td>Gene</td><td>Function</td><td>Product</td><td>GO Process</td><td>GO Component</td><td>Protein change</td></tr>"


def filter_ignored_genes_and_mutations(query_set, filter_settings):

    if filter_settings is None:
        ignored_genes = ""
        ignored_mutations = ""
        min_cutoff = 0
        max_cutoff = 100
    else:
        ignored_genes = filter_settings.ignored_genes
        ignored_mutations = filter_settings.ignored_mutations
        min_cutoff = filter_settings.min_cutoff
        max_cutoff = filter_settings.max_cutoff

    query_set = _filter_ignored_genes(query_set, ignored_genes)

    query_set = _filter_ignored_mutations(query_set, ignored_mutations)

    query_set = _filter_by_frequency(query_set, min_cutoff, max_cutoff)

    return query_set


def _filter_ignored_genes(query_set, ignored_genes):

    ignored_genes = _clean_ignored_genes_list(ignored_genes)

    global_ignored_genes = GlobalFilter.objects.get(id=1).ignored_genes.replace(" ", "").replace('\n', '').replace('\r', '').split(',')

    if ignored_genes == ['']:
        if global_ignored_genes == ['']:
            ignored_genes = []
        else:
            ignored_genes = global_ignored_genes
    else:
        ignored_genes.append(global_ignored_genes)

    if ignored_genes:

        if len(ignored_genes) > 0 and ignored_genes[0] is not '':
            for gene in ignored_genes:
                if str(gene).startswith('*'):
                    query_set = query_set.exclude(mutation__gene__endswith=str(gene)[1:])
                elif str(gene).endswith('*'):
                    query_set = query_set.exclude(mutation__gene__startswith=str(gene)[:-1])
                else:
                    query_set = query_set.exclude(mutation__gene__contains=gene)
    return query_set


def _filter_ignored_mutations(query_set, ignored_mutations):

    global_ignored_mutations = GlobalFilter.objects.get(id=1).ignored_mutations

    global_ignored_mutations = clean_ignored_mutation_id_list(global_ignored_mutations)

    ignored_mutations = clean_ignored_mutation_id_list(ignored_mutations)

    ignored_mutation_list = global_ignored_mutations + ignored_mutations

    for mut_id in ignored_mutation_list:

        if is_number(mut_id):

            query_set = query_set.exclude(mutation_id=mut_id)

    return query_set


def is_number(s):
    try:
        int(s)
        return True
    except ValueError:
        return False


def _filter_by_frequency(query_set, min_cutoff, max_cutoff):

    query_set = query_set.filter(frequency__gte=min_cutoff/100, frequency__lte=max_cutoff/100)

    return query_set


def _get_excluded_mutation_kwargs(mutation):

    kwargs = {}

    if not mutation:
        return kwargs

    if mutation['position'] is not '':
        kwargs['mutation__position'] = mutation['position']

    if mutation['type'] is not '':
        kwargs['mutation__mutation_type__contains'] = mutation['type']

    if mutation['sequence'] is not '':
        kwargs['mutation__sequence_change__contains'] = mutation['sequence']

    if mutation['gene'] is not '':
        kwargs['mutation__gene__contains'] = mutation['gene']

    if mutation['protein'] is not '':
        kwargs['mutation__protein_change__contains'] = mutation['protein']

    return kwargs


def get_filter_settings(ale_experiment_id):

    filter_settings, created = AleExperimentFilter.objects.get_or_create(ale_experiment_id=ale_experiment_id)

    return filter_settings


def clean_ignored_mutation_id_list(ignored_mutation_id_list, deleted_mutation_id=None):

    if not ignored_mutation_id_list:
        return []

    if ignored_mutation_id_list.startswith(','):
        ignored_mutation_id_list = ignored_mutation_id_list[1:]

    ignored_mutation_id_list = ignored_mutation_id_list.split(",")

    new_list = []

    for mut_id in ignored_mutation_id_list:

        if mut_id in new_list or is_number(mut_id) is False or not _mutation_exists(mut_id):
            continue

        if deleted_mutation_id is None or mut_id != deleted_mutation_id:
            new_list.append(mut_id)

    return new_list


def _clean_ignored_genes_list(ignored_genes):

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

    ignored_mutation_id_list = filter_form_model.ignored_mutations

    ignored_mutation_id_list = clean_ignored_mutation_id_list(ignored_mutation_id_list)

    for mut_id in ignored_mutation_id_list:
        try:
            mutation = Mutation.objects.get(id=mut_id)
        except ObjectDoesNotExist:
            continue

        table_row = "<tr id=\"%s\">" % mutation.id
        table_row += DELETE_ROW_BOX % mutation.id
        table_row += "<td>%d</td>" % mutation.position
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

    return table_body, ignored_mutation_id_list


def dashboard_filter(queryset):

    global_filter = GlobalFilter.objects.get(id=1)

    all_experiments = AleExperiment.objects.all()

    for exp in all_experiments:
        filter_settings = get_filter_settings(exp.ale_id)

        ignored_mutations = clean_ignored_mutation_id_list(filter_settings.ignored_mutations + global_filter.ignored_mutations)

        for mut_id in ignored_mutations:

            queryset = queryset.exclude(sequencing_experiment__tech_rep__isolate__flask__ale_id__ale_experiment__ale_id=exp.ale_id, mutation_id=mut_id)

        ignored_genes = _clean_ignored_genes_list(filter_settings.ignored_genes + "," + global_filter.ignored_genes)

        for gene in ignored_genes:

            if str(gene).startswith('*'):
                queryset = queryset.exclude(sequencing_experiment__tech_rep__isolate__flask__ale_id__ale_experiment__ale_id=exp.ale_id, mutation__gene__endswith=str(gene)[1:])
            elif str(gene).endswith('*'):
                queryset = queryset.exclude(sequencing_experiment__tech_rep__isolate__flask__ale_id__ale_experiment__ale_id=exp.ale_id, mutation__gene__startswith=str(gene)[:-1])
            else:
                queryset = queryset.exclude(sequencing_experiment__tech_rep__isolate__flask__ale_id__ale_experiment__ale_id=exp.ale_id, mutation__gene__contains=gene)

    return queryset


def _mutation_exists(mut_id):

    try:
        Mutation.objects.get(id=mut_id)
        return True
    except ObjectDoesNotExist:
        return False
