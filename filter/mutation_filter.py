from filter.models import AleExperimentFilter, GlobalFilter

import json

from django.utils.html import strip_tags

from filter.models import GlobalFilter

from seq.models import Mutation

from django.core.exceptions import ObjectDoesNotExist

__author__ = 'Patrick Phaneuf'

NO_BREAK_STRING_CODE = u'\xa0'

MODEL_TO_FILTER_MAPPINGS = {"protein": "protein_change",
                            "type": "mutation_type",
                            "sequence": "sequence_change",
                            "position": "position",
                            "gene": "gene"}

DELETE_ROW_BOX = """<td><img src="/static/DataTables/media/images/close-icon.gif" onclick="delete_row(%d)" width="12" height="11" style="float:right; cursor:pointer"></a></td>"""

TABLE_HEADER = "<tr><td></td><td>Position</td><td>Mutation Type</td><td>Sequence Change</td><td>Gene</td><td>Function</td><td>Product</td><td>GO Process</td><td>GO Component</td><td>Protein change</td></tr>"


# TODO: Maybe make filtering part of the database query instead of post processing.
# TODO: Could become an issue for large experiments with many filters
def is_excluded_on_mutation(mutation, filter_settings):
    mutation_dict = dict(mutation.__dict__)

    if filter_settings is not None:

        default_ignored_mutations_json_string = "[]"

        if filter_settings.ignored_mutations != ""\
                and len(filter_settings.ignored_mutations) != len(default_ignored_mutations_json_string):

            mutation_to_exclude_list = json.loads(filter_settings.ignored_mutations.replace("'", '"'))

            for mutation_to_exclude in mutation_to_exclude_list:

                for key in mutation_to_exclude:

                    mutation_data = _get_sanitized_mutation_data(key, mutation_dict)

                    if mutation_to_exclude[key] is not '':
                        try:
                            if mutation_to_exclude[key] not in mutation_data:
                                break
                        except:
                            try:
                                if int(mutation_to_exclude[key]) != int(mutation_data):
                                    break
                            except:
                                continue
                    else:
                        continue
                else:
                    return True

    return False


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

    ignored_genes = ignored_genes.replace(" ", "").replace('\n', '').replace('\r', '').split(',')

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


def _get_sanitized_mutation_data(key, mutation_dict):
    try:
        mutation_data = strip_tags(mutation_dict[MODEL_TO_FILTER_MAPPINGS[key]]).replace(
            NO_BREAK_STRING_CODE, u'').replace(" ", "")
    except:
        mutation_data = mutation_dict[MODEL_TO_FILTER_MAPPINGS[key]]
    return mutation_data


def _normalize_sequence_change_string(sequence_change_string):
    return sequence_change_string.replace(NO_BREAK_STRING_CODE, u' ')


def is_excluded_on_gene(mutation, filter_settings):
    is_mutation_excluded = False

    if filter_settings is not None:

        excluded_gene_list = filter_settings.ignored_genes.replace(" ", "").split(',')

        if mutation.gene in excluded_gene_list:
            is_mutation_excluded = True

    return is_mutation_excluded


def is_excluded_on_freq(observed_mutation, filter_settings):
    is_mutation_excluded = True

    # Creating up defaults.
    if filter_settings is not None:
        minimum_mutation_frequency = float(filter_settings.min_cutoff) / 100
        maximum_mutation_frequency = float(filter_settings.max_cutoff) / 100
    else:
        minimum_mutation_frequency = 0.0
        maximum_mutation_frequency = 1.0

    if minimum_mutation_frequency <= observed_mutation.frequency <= maximum_mutation_frequency:
        is_mutation_excluded = False

    return is_mutation_excluded


def get_filter_settings(ale_experiment_id):
    filter_queryset = AleExperimentFilter.objects.filter(ale_experiment_id=ale_experiment_id)

    if len(filter_queryset) == 0:
        filter_settings = AleExperimentFilter()
    else:
        filter_settings = filter_queryset[0]  # Since there's only one filter setting per experiment.

    filter_settings.ignored_mutations = _append_global_ignored_mutations_json(filter_settings.ignored_mutations)

    filter_settings.ignored_genes = _append_global_ignored_genes(filter_settings.ignored_genes)

    return filter_settings


def _append_global_ignored_mutations_json(ignored_mutations):

    global_filter_settings = GlobalFilter.objects.get_or_create(id=1)[0]

    if global_filter_settings.ignored_mutations is ''\
            or global_filter_settings.ignored_mutations == "[]":  # TODO: define what "[]" means in a CONSTANT string up top.
        return ignored_mutations

    ignored_mutations = ignored_mutations.replace("]", "")

    global_ignored_mutations = global_filter_settings.ignored_mutations.replace("[", "")

    if ignored_mutations != "[":
        ignored_mutations += ", "

    ignored_mutations += global_ignored_mutations

    return ignored_mutations


def _append_global_ignored_genes(ignored_genes):

    global_filter_settings = GlobalFilter.objects.get_or_create(id=1)[0]

    if global_filter_settings.ignored_genes == "":
        return ignored_genes

    if ignored_genes == "":
        ignored_genes = global_filter_settings.ignored_genes
    else:
        ignored_genes += ", " + global_filter_settings.ignored_genes

    return ignored_genes


def clean_ignored_mutation_id_list(ignored_mutation_id_list, deleted_mutation_id=None):

    if ignored_mutation_id_list.startswith(','):
        ignored_mutation_id_list = ignored_mutation_id_list[1:]

    ignored_mutation_id_list = ignored_mutation_id_list.split(",")

    new_list = []

    for mut_id in ignored_mutation_id_list:

        if mut_id in new_list or is_number(mut_id) is False:
            continue

        if deleted_mutation_id is None or mut_id != deleted_mutation_id:
            new_list.append(mut_id)

    return new_list


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
