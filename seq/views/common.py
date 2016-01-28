import collections

import ale.common

import ale.models

import seq.models

import aleinfo.settings


__author__ = 'Patrick Phaneuf'

DEFAULT_RESEQ_REPORT_URL = "http://localhost/sequencing/"

SETTINGS_SEQUENCING_URL = "sequencing_url"

REQUEST_ALE_NUMBER = "ale_no"

REQUEST_ALE_EXPERIMENT_ID = "ale_experiment_id"

HTML_MUTATION_TABLE_HEADER = """<tr><td>Mutation Type</td><td>Mutation</td><td>Gene</td><td>Protein change</td>"""
HTML_MUTATION_TABLE_EXPERIMENT_HEADER = """<a href="%s">%s</a>"""
HTML_CHECKBOX = """<td><input type="checkbox" class="cb" name=%s /><br>%s</td>"""

HTML_MUTATION_PRESENT_FALSE_CELL_HTML = """<td class="false">%d/%d</td>"""
HTML_MUTATION_PRESENT_TRUE_CELL_HTML = """<td class="true">%.2f</td>"""
HTML_MUTATION_TABLE_ROW = """<td>%d %s<a href="javascript:void(0)" class="shut" style="float:right;display:none;" onclick="deleteRow.call(this)"><img src="/static/DataTables/media/images/close-icon.gif" width="12" height="11"></a></td>"""
HTML_EMPTY_MUTATION_CELL = """<td class="false"></td>"""

REQUEST_ALL = "all"

ALE_NUMBER_SELECTOR_QUERY = "AND ale_no = %d"
ALE_EXPERIMENT_SELECTOR_QUERY = "AND experiment_id = %d"

EXPERIMENT_MAPPING_FILTERING_SHOW_FLAG = "show"
EXPERIMENT_MAPPING_FILTERING_REMOVE_FLAG = "remove"

SEQ_EXPERIMENT_QUERY = """SELECT reseq_id AS id FROM id_mapping WHERE reseq_id IS NOT NULL %s %s ORDER BY ale_no, flask_no, isolate_no ASC;"""


if hasattr(aleinfo.settings, SETTINGS_SEQUENCING_URL):
    reseqencing_report_url = aleinfo.settings.sequencing_url
else:
    reseqencing_report_url = DEFAULT_RESEQ_REPORT_URL


# TODO: Refactor. The observed mutations argument may
# reference to a seq_experiment that doesn't exist due to checkbox filtering.
# This makes this function very confusing.
def get_table_body(seq_experiment_dict, observed_mutations_query_set, request):

    mutations = seq.models.Mutation.objects.filter(pk__in=observed_mutations_query_set.values_list("mutation", flat=True))
    mutation_dict = dict((id, i) for i, id in enumerate(mutations.values_list("id", flat=True)))

    experiment_urls = _get_experiment_urls(seq_experiment_dict)

    experiment_id_idx_mapping = _get_experiment_id_idx_mapping(seq_experiment_dict)

    # TODO: figure out what this is.
    extra_validation = False if request.GET.get("novalid") else True

    # Initialize all sample mutation table cells as empty.
    table_entries = [[HTML_EMPTY_MUTATION_CELL] * len(experiment_id_idx_mapping) for idx in range(len(mutations))]

    # Populating table_entries
    for observed_mutation in observed_mutations_query_set:

        # TODO: figure out what this is.
        # sometimes we do not want the extra validation
        if not extra_validation and not observed_mutation.breseq_present:
            continue

        new_entry = _get_table_mutation_entry(observed_mutation, experiment_urls)

        if new_entry is not None and observed_mutation.sequencing_experiment_id in seq_experiment_dict.keys():
            table_entries[mutation_dict[observed_mutation.mutation_id]][experiment_id_idx_mapping[observed_mutation.sequencing_experiment_id]] = new_entry

    #Populating table body
    table_body = ""

    for mutation in mutations:

        table_row = "<tr>"

        if mutation.reference_error:    # TODO: what is going on here? What is 'reference_error'?
            # table_row += """<td class="reference_error">%d %s</td>""" % (mutation.position, mutation.sequence_change)
            continue

        else:
            table_row += "<td>%s</td>" % mutation.mutation_type
            table_row += HTML_MUTATION_TABLE_ROW % (
                mutation.position,
                mutation.sequence_change)

        table_row += "<td>%s</td>" % mutation.gene
        table_row += "<td>%s</td>" % mutation.protein_change
        table_row += "".join(table_entries[mutation_dict[mutation.id]])
        table_row += "</tr>"

        table_body += table_row + "\n"

    return table_body


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

    ale_experiment_name = "All ALE Experiment"

    if ale_experiment_id is not None and ale_experiment_id != "all":

        ale_experiment = ale.models.AleExperiment.objects.filter(ale_id=ale_experiment_id)

        # TODO: should only ever be returning 1 experiment. Implement error handling for more than one returned.
        ale_experiment_name = ale_experiment[0].name

    return ale_experiment_name


def _get_table_mutation_entry(observed_mutation, experiment_urls):

    table_entry = ""

    if observed_mutation.breseq_present:

        table_entry = HTML_MUTATION_PRESENT_TRUE_CELL_HTML % float(observed_mutation.frequency)

    # TODO: Figure out what this is supposed to do.
    elif observed_mutation.present is False:

        table_entry = HTML_MUTATION_PRESENT_FALSE_CELL_HTML % (observed_mutation.mutated_reads,
                                                               observed_mutation.wt_reads)

    return table_entry


def _get_ale_experiment_selector(ale_experiment_id):

    if ale_experiment_id is None or ale_experiment_id == REQUEST_ALL:

        ale_experiment_selector = ""

    else:

        ale_experiment_selector = ALE_EXPERIMENT_SELECTOR_QUERY % int(ale_experiment_id)

    return ale_experiment_selector


def _get_ale_number_selector(ale_id):

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

    ale_experiment_selector = _get_ale_experiment_selector(ale_experiment_id)

    ale_id_selector = _get_ale_number_selector(ale_id)

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

        checked_experiment_ids = query_string.encode('latin_1').replace("{", "").replace("}", "")

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

        checked_experiment_ids = query_string.encode('latin_1').replace("{", "").replace("}", "")

        if checked_experiment_ids != "":

            for checked_experiment_id in checked_experiment_ids.split(","):

                if checked_experiment_id != "":

                    del seq_experiment_dict[int(checked_experiment_id)]

    return seq_experiment_dict


def get_observed_mutations(seq_experiment_dict):

    observed_mutations = seq.models.ObservedMutation.objects.filter(sequencing_experiment_id__in=seq_experiment_dict.keys())

    return observed_mutations
