import collections

from seq.models import ResequencingExperiment

import aleinfo.settings as settings


__author__ = 'pphaneuf'

DEFAULT_RESEQ_REPORT_URL = "http://localhost/sequencing/"

SETTINGS_SEQUENCING_URL = "sequencing_url"

REQUEST_ALE_NUMBER = "ale_no"

REQUEST_ALE_EXPERIMENT_ID = "ale_experiment_id"

MUTATION_PRESENT_FALSE_CELL_HTML = """<td class="false">%d/%d</td>"""
MUTATION_PRESENT_TRUE_CELL_HTML = """<td class="true"><a href=%s>%.2f</td>"""

REQUEST_ALL = "all"

ALE_NUMBER_SELECTOR_QUERY = "AND ale_no = %d"
ALE_EXPERIMENT_SELECTOR_QUERY = "AND experiment_id = %d"

EXPERIMENT_MAPPING_FILTERING_SHOW_FLAG = "show"
EXPERIMENT_MAPPING_FILTERING_REMOVE_FLAG = "remove"

SEQ_EXPERIMENT_QUERY = """SELECT reseq_id AS id FROM id_mapping WHERE reseq_id IS NOT NULL %s %s ORDER BY ale_no, flask_no, isolate_no ASC;"""


if hasattr(settings, SETTINGS_SEQUENCING_URL):
    reseqencing_report_url = settings.sequencing_url
else:
    reseqencing_report_url = DEFAULT_RESEQ_REPORT_URL


def get_ale_experiment_id(request):

    # Get the full list of ale experiments for the ale number of interest
    experiment_ids = request.GET.get(REQUEST_ALE_EXPERIMENT_ID)

    experiment_ids = None if experiment_ids is None or experiment_ids == "all" else int(experiment_ids)

    return experiment_ids


def get_table_mutation_entry(observed, experiment_urls):

    table_entry = ""

    if observed.breseq_present:

        table_entry = MUTATION_PRESENT_TRUE_CELL_HTML % (experiment_urls, float(observed.frequency))

    # TODO: Figure out what this is supposed to do.
    elif observed.present is False:

        table_entry = MUTATION_PRESENT_FALSE_CELL_HTML % (observed.mutated_reads,
                                                          observed.wt_reads)

    return table_entry


def get_seq_experiments(request):
    """return a list of seq experiments for a given ALE"""

    ale_experiment_selector = _get_ale_experiment_selector(request)

    ale_number_selector = _get_ale_number_selector(request)

    sql_query = SEQ_EXPERIMENT_QUERY % (ale_experiment_selector, ale_number_selector)

    seq_experiments_raw_query_set = ResequencingExperiment.objects.raw(sql_query)

    return seq_experiments_raw_query_set


def _get_ale_experiment_selector(request):

    ale_experiment_id = request.GET.get(REQUEST_ALE_EXPERIMENT_ID)

    if ale_experiment_id is None or ale_experiment_id == REQUEST_ALL:

        ale_experiment_selector = ""

    else:

        ale_experiment_selector = ALE_EXPERIMENT_SELECTOR_QUERY % int(ale_experiment_id)

    return ale_experiment_selector


def _get_ale_number_selector(request):

    ale_no = request.GET.get(REQUEST_ALE_NUMBER)

    if ale_no is None or ale_no == REQUEST_ALL:

        ale_no_selector = ""

    else:

        ale_no_selector = ALE_NUMBER_SELECTOR_QUERY % int(ale_no)

    return ale_no_selector


def get_experiment_ordered_dict(request):

    seq_experiments_raw_query_set = get_seq_experiments(request)

    seq_experiment_ordered_dict = collections.OrderedDict((seq_experiment.id, seq_experiment) for seq_experiment in seq_experiments_raw_query_set)

    return seq_experiment_ordered_dict


def get_experiment_urls(seq_experiment_dict):

    experiment_urls = dict((i.id, reseqencing_report_url + i.location) for i in seq_experiment_dict.values())

    return experiment_urls


def get_sample_name(seq_experiment):

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