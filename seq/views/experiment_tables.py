__author__ = 'pphaneuf'


from django.contrib.auth.decorators import login_required

from django.http import HttpResponse

from django.template import Context, loader

import aleinfo.settings as settings

from seq.models import *    # TODO: only import necessary models.


# TODO: used by multiple views. Also implemented within views.py; implement in one location.
REQUEST_ALE_EXPERIMENT_ID = "ale_experiment_id"

EXPERIMENT_LIST_TEMPLATE = "experiment_view.html"

# TODO: used by multiple views. Also implemented within views.py; implement in one location.
DEFAULT_RESEQ_REPORT_URL = "http://localhost/sequencing/"

# TODO: used by multiple views. Also implemented within views.py; implement in one location.
REQUEST_ALL = "all"

# TODO: used by multiple views. Also implemented within views.py; implement in one location.
REQUEST_ALE_NUMBER = "ale_no"


# TODO: used by multiple views. Also implemented within views.py; implement in one location.
if hasattr(settings, "sequencing_url"):
    reseqencing_report_url = settings.sequencing_url
else:
    reseqencing_report_url = DEFAULT_RESEQ_REPORT_URL


@login_required
def lists(request):
    """return a list of resequencing experiments"""

    experiments = _get_seq_experiments(request)

    # Would rather want to use something like a dictionary since an experiment is
    # unique, though an experiment is currently a structure and an integral type
    # that can be used as a key.

    experiments_info_list = _get_experiment_info_list(experiments)

    template = loader.get_template(EXPERIMENT_LIST_TEMPLATE)

    context = Context({"experiments_info_list": experiments_info_list,
                       "resequencing_report_url": reseqencing_report_url})

    return HttpResponse(template.render(context))


def _get_seq_experiments(request):
    """return a list of seq experiments for a given ALE"""

    ale_experiment_selector = _get_ale_experiment_selector(request)

    ale_no_selector = _get_ale_number_selector(request)

    experiments = ResequencingExperiment.objects.raw(
        """SELECT reseq_id AS id FROM id_mapping WHERE
        reseq_id IS NOT NULL %s %s
        ORDER BY ale_no, flask_no, isolate_no ASC;""" % (ale_experiment_selector, ale_no_selector))

    return experiments


# TODO: used by multiple views. Also implemented within views.py; implement in one location.
def _get_ale_experiment_selector(request):

    ale_experiment_id = request.GET.get(REQUEST_ALE_EXPERIMENT_ID)
    if ale_experiment_id is None or ale_experiment_id == REQUEST_ALL:
        ale_experiment_selector = ""
    else:
        ale_experiment_selector = "AND experiment_id = %d" % int(ale_experiment_id)

    return ale_experiment_selector


def _get_experiment_info_list(experiments):
    experiments_info_list = []

    for experiment in experiments:
        mc_list = UnassignedMissingCoverageEvidence.objects.filter(sequencing_experiment_id=experiment.id)

        mapped_read_count = int((experiment.percentage_mapped / 100) * experiment.reads)

        # Using tuple because immutable; mc_list must remain associated with particular experiment.
        experiment_info_tuple = (experiment, mc_list, mapped_read_count)

        experiments_info_list.append(experiment_info_tuple)

    return experiments_info_list


# TODO: used by multiple views. Also implemented within views.py; implement in one location.
def _get_ale_number_selector(request):

    ale_no = request.GET.get(REQUEST_ALE_NUMBER)
    if ale_no is None or ale_no == REQUEST_ALL:
        ale_no_selector = ""
    else:
        ale_no_selector = "AND ale_no = %d" % int(ale_no)

    return ale_no_selector