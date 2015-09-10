from seq.models import ResequencingExperiment


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

SEQ_EXPERIMENT_QUERY = """SELECT reseq_id AS id FROM id_mapping WHERE reseq_id IS NOT NULL %s %s ORDER BY ale_no, flask_no, isolate_no ASC;"""


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
