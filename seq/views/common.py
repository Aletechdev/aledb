__author__ = 'pphaneuf'


from seq.models import ResequencingExperiment

from decimal import *


DEFAULT_RESEQ_REPORT_URL = "http://localhost/sequencing/"

SETTINGS_SEQUENCING_URL = "sequencing_url"

REQUEST_ALE_NUMBER = "ale_no"

REQUEST_ALE_EXPERIMENT_ID = "ale_experiment_id"

MUTATION_PRESENT_FALSE_CELL_HTML = """<td class="false">%d/%d</td>"""
MUTATION_PRESENT_TRUE_CELL_HTML = """<td class="true">%.2f</td>"""

REQUEST_ALL = "all"


def get_table_mutation_entry(observed, experiment_urls):

    if observed.breseq_present:
        table_entry = MUTATION_PRESENT_TRUE_CELL_HTML % float(observed.frequency)

    # TODO: Figure out what this is supposed to do.
    elif observed.present is False:
        table_entry = MUTATION_PRESENT_FALSE_CELL_HTML % (observed.mutated_reads,
                                                          observed.wt_reads)

    return table_entry


def get_ale_number_selector(request):

    ale_no = request.GET.get(REQUEST_ALE_NUMBER)
    if ale_no is None or ale_no == REQUEST_ALL:
        ale_no_selector = ""
    else:
        ale_no_selector = "AND ale_no = %d" % int(ale_no)

    return ale_no_selector


def get_seq_experiments(request):
    """return a list of seq experiments for a given ALE"""

    ale_experiment_selector = _get_ale_experiment_selector(request)

    ale_no_selector = get_ale_number_selector(request)

    experiments = ResequencingExperiment.objects.raw(
        """SELECT reseq_id AS id FROM id_mapping WHERE
        reseq_id IS NOT NULL %s %s
        ORDER BY ale_no, flask_no, isolate_no ASC;""" % (ale_experiment_selector, ale_no_selector))

    return experiments


def _get_ale_experiment_selector(request):

    ale_experiment_id = request.GET.get(REQUEST_ALE_EXPERIMENT_ID)
    if ale_experiment_id is None or ale_experiment_id == REQUEST_ALL:
        ale_experiment_selector = ""
    else:
        ale_experiment_selector = "AND experiment_id = %d" % int(ale_experiment_id)

    return ale_experiment_selector