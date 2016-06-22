import collections

import ale.common

import ale.models

import seq.models

import aleinfo.settings

import os


__author__ = 'Patrick Phaneuf'

DEFAULT_RESEQ_REPORT_URL = "http://localhost/sequencing/"

SETTINGS_SEQUENCING_URL = "sequencing_url"

REQUEST_ALE_NUMBER = "ale_no"

REQUEST_ALE_EXPERIMENT_ID = "ale_experiment_id"

HTML_MUTATION_TABLE_HEADER = """<tr><td></td><td>Position</td><td>Mutation Type</td><td>Sequence Change</td><td>Gene</td><td>Protein change</td>"""
HTML_MUTATION_TABLE_EXPERIMENT_HEADER = """<a href="%s">%s</a>"""
HTML_CHECKBOX = """<td><input type="checkbox" class="cb" name=%s /><br>%s</td>"""

HTML_MUTATION_PRESENT_FALSE_CELL_HTML = """<td class="false">%d/%d</td>"""
HTML_MUTATION_PRESENT_TRUE_CELL_HTML = """<td id="true"><a href="%s">%.2f</a></td>"""
HTML_MUTATION_TABLE_ROW = """<td><a href="javascript:void(0)" style="float:right" onclick="deleteRow.call(this)"><img src="/static/DataTables/media/images/close-icon.gif" width="12" height="11"></a></td>"""
HTML_EMPTY_MUTATION_CELL = """<td id="empty"></td>"""

REQUEST_ALL = "all"

ALE_NUMBER_SELECTOR_QUERY = "AND ale_no = %d"
ALE_EXPERIMENT_SELECTOR_QUERY = "AND experiment_id = %d"

EXPERIMENT_MAPPING_FILTERING_SHOW_FLAG = "show"
EXPERIMENT_MAPPING_FILTERING_REMOVE_FLAG = "remove"

SEQ_EXPERIMENT_QUERY = """SELECT reseq_id AS id FROM id_mapping WHERE reseq_id IS NOT NULL %s %s ORDER BY ale_no, flask_no, isolate_no ASC;"""

MUTATION_TYPE_LIST = ['SNP', 'SUB', 'DEL', 'INS', 'MOB', 'AMP', 'CON', 'INV', 'DUP']

PROTEIN_CHANGE_TYPE_LIST = ['intergenic', 'noncoding', 'pseudogenes', 'snp_type_synonymous', 'snp_type_nonsynonymous']


if hasattr(aleinfo.settings, SETTINGS_SEQUENCING_URL):
    reseqencing_report_url = aleinfo.settings.sequencing_url
else:
    reseqencing_report_url = DEFAULT_RESEQ_REPORT_URL


# TODO: Refactor. The observed mutations argument may
# reference to a seq_experiment that doesn't exist due to checkbox filtering.
# This makes this function very confusing.
def get_table_body(seq_experiment_dict, observed_mutations_query_set, request, filter_settings=None):

    mutations = seq.models.Mutation.objects.filter(pk__in=observed_mutations_query_set.values_list("mutation", flat=True))
    mutation_index_dict = dict((id, i) for i, id in enumerate(mutations.values_list("id", flat=True)))

    experiment_urls = _get_experiment_urls(seq_experiment_dict)

    experiment_id_idx_mapping = _get_experiment_id_idx_mapping(seq_experiment_dict)

    # TODO: figure out what this is.
    extra_validation = False if request.GET.get("novalid") else True

    # Initialize all sample mutation table cells as empty.
    table_entries = [[HTML_EMPTY_MUTATION_CELL] * len(experiment_id_idx_mapping) for _ in range(len(mutations))]

    # Populating table_entries
    for observed_mutation in observed_mutations_query_set:

        # TODO: figure out what this is.
        # sometimes we do not want the extra validation
        if not extra_validation and not observed_mutation.breseq_present:
            continue

        if not _filter_mutation(filter_settings, observed_mutation):

            new_entry = _get_table_mutation_entry(observed_mutation, experiment_urls)

            if new_entry is not None and observed_mutation.sequencing_experiment_id in seq_experiment_dict.keys():
                table_entries[mutation_index_dict[observed_mutation.mutation_id]][experiment_id_idx_mapping[observed_mutation.sequencing_experiment_id]] = new_entry

    #Populating table body
    table_body = ""

    for mutation in mutations:

        if _contains_mutation(table_entries[mutation_index_dict[mutation.id]]):

            table_row = "<tr>"

            if mutation.reference_error:    # TODO: what is going on here? What is 'reference_error'?
                # table_row += """<td class="reference_error">%d %s</td>""" % (mutation.position, mutation.sequence_change)
                continue

            else:
                table_row += HTML_MUTATION_TABLE_ROW

            table_row += "<td>%s</td>" % mutation.position
            table_row += "<td>%s</td>" % mutation.mutation_type
            table_row += "<td>%s</td>" % mutation.sequence_change
            table_row += "<td><a href=/ale_analytics/gene?g=%s>%s</a></td>" % (mutation.gene, mutation.gene)
            table_row += "<td>%s</td>" % mutation.protein_change
            table_row += "".join(table_entries[mutation_index_dict[mutation.id]])
            table_row += "</tr>"

            table_body += table_row + "\n"

    return table_body


def _filter_mutation(filter_settings, observed_mutation):

    filter_mutation = _is_filter_on_gene(filter_settings, observed_mutation) or _is_filter_on_freq(filter_settings, observed_mutation)

    return filter_mutation


def _is_filter_on_gene(filter_settings, observed_mutation):
    is_filter_on_gene = False

    if filter_settings is not None:

        filtered_gene_list = filter_settings.ignored_genes.replace(" ", "").split(',')

        if observed_mutation.mutation.gene in filtered_gene_list:
            is_filter_on_gene = True

    return is_filter_on_gene


def _is_filter_on_freq(filter_settings, observed_mutation):
    is_filter_on_freq = True

    # Creating up defaults.
    if filter_settings is not None:
        minimum_mutation_frequency = float(filter_settings.min_cutoff) / 100
        maximum_mutation_frequency = float(filter_settings.max_cutoff) / 100
    else:
        minimum_mutation_frequency = 0.0
        maximum_mutation_frequency = 1.0

    if minimum_mutation_frequency <= observed_mutation.frequency <= maximum_mutation_frequency:
        is_filter_on_freq = False

    return is_filter_on_freq


def _contains_mutation(filtered_observed_mutations_row):

    contains_mutation = False

    for observed_mutation_entry in filtered_observed_mutations_row:
        if "true" in observed_mutation_entry:
            contains_mutation = True

    return contains_mutation


def _get_experiment_id_idx_mapping(seq_experiment_dict):

    experiment_id_idx_mapping = dict((reseq_exp_id, idx) for idx, reseq_exp_id in enumerate(seq_experiment_dict.keys()))

    return experiment_id_idx_mapping


def get_seq_experiment_queryset(experiment_ids, exclude_starting_strain=False):

    if experiment_ids is not None:

        experiment = ale.models.AleExperiment.objects.get(ale_id=experiment_ids)

        experiment_queryset = experiment.aleid_set.only("ale_id")

    else:

        experiment_queryset = seq.models.ResequencingExperiment.objects.all()

    if exclude_starting_strain:

        experiment_queryset = experiment_queryset.exclude(ale_id=ale.common.STARTING_STRAIN_ALE_ID)

    return experiment_queryset


def get_table_header(seq_experiment_dict):

    table_header = HTML_MUTATION_TABLE_HEADER

    experiment_urls = _get_experiment_urls(seq_experiment_dict)

    for seq_experiment_id in seq_experiment_dict:

        seq_experiment = seq_experiment_dict[seq_experiment_id]

        sample_name = _get_sample_name(seq_experiment)

        mutation_identifier = HTML_MUTATION_TABLE_EXPERIMENT_HEADER % (experiment_urls[seq_experiment_id],
                                                                       sample_name)

        table_header += HTML_CHECKBOX % (
            seq_experiment.id,
            mutation_identifier)

    table_header += "</tr>"

    return table_header


def get_ale_number(request):

    ale_number = request.GET.get(REQUEST_ALE_NUMBER)

    ale_number = None if ale_number is None or ale_number == "all" else int(ale_number)

    return ale_number


def get_ale_experiment_id(request):

    # Get the full list of ale experiments for the ale number of interest
    experiment_ids = request.GET.get(REQUEST_ALE_EXPERIMENT_ID)

    experiment_ids = None if experiment_ids is None or experiment_ids == "all" else int(experiment_ids)

    return experiment_ids


def get_ale_experiment_name(request):

    ale_experiment_id = request.GET.get(REQUEST_ALE_EXPERIMENT_ID)

    ale_experiment_name = "All ALE Experiments"

    if ale_experiment_id is not None and ale_experiment_id != "all":

        ale_experiment = ale.models.AleExperiment.objects.filter(ale_id=ale_experiment_id)

        # TODO: should only ever be returning 1 experiment. Implement error handling for more than one returned.
        ale_experiment_name = ale_experiment[0].name

    return ale_experiment_name


def _get_table_mutation_entry(observed_mutation, experiment_urls):

    table_entry = ""

    if observed_mutation.breseq_present and observed_mutation.sequencing_experiment_id in experiment_urls:

        url = experiment_urls[observed_mutation.sequencing_experiment_id]

        if observed_mutation.mutation.mutation_type == "DUP":

            base_name = os.path.basename(os.path.dirname(os.path.dirname(url)))

            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(url)))

            dup_url = base_dir + "/dups/" + base_name + "/" + base_name + ".html"

            table_entry = HTML_MUTATION_PRESENT_TRUE_CELL_HTML % (dup_url, float(observed_mutation.frequency))

        else:
            evidence_url = url + _find_between(observed_mutation.evidence, "\"", "\"")
            table_entry = HTML_MUTATION_PRESENT_TRUE_CELL_HTML % (evidence_url, float(observed_mutation.frequency))

    # TODO: Figure out what this is supposed to do.
    elif observed_mutation.present is False:

        table_entry = HTML_MUTATION_PRESENT_FALSE_CELL_HTML % (observed_mutation.mutated_reads,
                                                               observed_mutation.wt_reads)

    return table_entry


def get_ale_experiment_selector(ale_experiment_id):

    if ale_experiment_id is None or ale_experiment_id == REQUEST_ALL:

        ale_experiment_selector = ""

    else:

        ale_experiment_selector = ALE_EXPERIMENT_SELECTOR_QUERY % int(ale_experiment_id)

    return ale_experiment_selector


def get_ale_number_selector(ale_id):

    if ale_id is None or ale_id == REQUEST_ALL:

        ale_no_selector = ""

    else:

        ale_no_selector = ALE_NUMBER_SELECTOR_QUERY % int(ale_id)

    return ale_no_selector


def get_experiment_ordered_dict(request, include_starting_strain=False):

    seq_experiment_ordered_dict = collections.OrderedDict()

    if include_starting_strain:

        starting_strain_raw_queryset = _get_starting_string_mutation_queryset(request)

        for seq_experiment in starting_strain_raw_queryset:
            seq_experiment_ordered_dict[seq_experiment.id] = seq_experiment

    seq_experiments_raw_queryset = get_seq_experiment_raw_queryset(request)

    for seq_experiment in seq_experiments_raw_queryset:

        seq_experiment_ordered_dict[seq_experiment.id] = seq_experiment

    return seq_experiment_ordered_dict


def get_seq_experiment_raw_queryset(request):

    ale_id = request.GET.get(REQUEST_ALE_NUMBER)

    return _get_seq_experiment_raw_queryset(request, ale_id)


def _get_starting_string_mutation_queryset(request):

    ale_id = ale.common.STARTING_STRAIN_ALE_ID

    return _get_seq_experiment_raw_queryset(request, ale_id)


def _get_seq_experiment_raw_queryset(request, ale_id):

    ale_experiment_id = request.GET.get(REQUEST_ALE_EXPERIMENT_ID)

    ale_experiment_selector = get_ale_experiment_selector(ale_experiment_id)

    ale_id_selector = get_ale_number_selector(ale_id)

    sql_query = SEQ_EXPERIMENT_QUERY % (ale_experiment_selector, ale_id_selector)

    seq_experiments_raw_queryset = seq.models.ResequencingExperiment.objects.raw(sql_query)

    return seq_experiments_raw_queryset


def _get_experiment_urls(seq_experiment_dict):

    experiment_urls = dict((i.id, reseqencing_report_url + i.location) for i in seq_experiment_dict.values())

    return experiment_urls


def _get_sample_name(seq_experiment):

    sample_name = seq_experiment.isolate.flask.ale_id.ale_experiment.name

    sample_name += " "

    sample_name += seq_experiment.get_isolate_name().replace("_", " ")

    return sample_name


def filter_checked_flasks(request, seq_experiment_dict):

    seq_experiment_dict = _show_checked_flasks(request, seq_experiment_dict)

    seq_experiment_dict = _remove_checked_flasks(request, seq_experiment_dict)

    return seq_experiment_dict


def _show_checked_flasks(request, seq_experiment_dict):

    query_string = request.GET.get(EXPERIMENT_MAPPING_FILTERING_SHOW_FLAG)

    if query_string is not None:

        checked_experiment_ids = str(query_string).replace("{", "").replace("}", "")

        if checked_experiment_ids != "":

            checked_experiment_id_list = [int(i) for i in checked_experiment_ids.split(",") if i != ""]

            checked_experiment_ids = seq_experiment_dict.keys()

            for checked_experiment_id in checked_experiment_ids:

                if checked_experiment_id not in checked_experiment_id_list:

                    del seq_experiment_dict[checked_experiment_id]

    return seq_experiment_dict


def _remove_checked_flasks(request, seq_experiment_dict):

    query_string = request.GET.get(EXPERIMENT_MAPPING_FILTERING_REMOVE_FLAG)

    if query_string is not None:

        checked_experiment_ids = str(query_string).replace("{", "").replace("}", "")

        if checked_experiment_ids != "":

            for checked_experiment_id in checked_experiment_ids.split(","):

                if checked_experiment_id != "":

                    del seq_experiment_dict[int(checked_experiment_id)]

    return seq_experiment_dict


def get_observed_mutations(seq_experiment_dict):

    observed_mutations = seq.models.ObservedMutation.objects.filter(sequencing_experiment_id__in=seq_experiment_dict.keys())

    return observed_mutations


def get_filter_settings(ale_experiment_id):

    filter_queryset = ale.models.Filter.objects.filter(ale_experiment_id=ale_experiment_id)

    if len(filter_queryset) is 0:
        return ale.models.Filter()

    filter_settings = filter_queryset[0]  # Since there's only one filter setting per experiment.

    return filter_settings


def _find_between(s, first, last):
    try:
        start = s.index(first) + len(first)
        end = s.index(last, start)
        return s[start:end]
    except ValueError:
        return ""
