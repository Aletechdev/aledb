__author__ = 'pphaneuf'


from django.contrib.auth.decorators import login_required

from django.http import HttpResponse

from django.template import Context, loader

import aleinfo.settings as settings

from seq.models import *    # TODO: only import necessary models.

from seq.views import common


EXPERIMENT_LIST_TEMPLATE = "experiment_view.html"


# TODO: used by multiple views. Also implemented within views.py; implement in one location.
if hasattr(settings, "sequencing_url"):
    reseqencing_report_url = settings.sequencing_url
else:
    reseqencing_report_url = common.DEFAULT_RESEQ_REPORT_URL


@login_required
def lists(request):
    """return a list of resequencing experiments"""

    experiments = common.get_seq_experiment_raw_queryset(request)

    # Would rather want to use something like a dictionary since an experiment is
    # unique, though an experiment is currently a structure and an integral type
    # that can be used as a key.

    experiments_info_list = _get_experiment_info_list(experiments)

    template = loader.get_template(EXPERIMENT_LIST_TEMPLATE)

    ale_experiment_name = common.get_ale_experiment_name(request)

    context = Context({"experiments_info_list": experiments_info_list,
                       "resequencing_report_url": reseqencing_report_url,
                       "ale_experiment_name": ale_experiment_name})

    return HttpResponse(template.render(context))


def _get_experiment_info_list(experiments):

    experiments_info_list = []

    for experiment in experiments:

        mc_list = UnassignedMissingCoverageEvidence.objects.filter(sequencing_experiment_id=experiment.id)

        mapped_read_count = int((experiment.percentage_mapped / 100) * experiment.reads)

        clonal_or_population = "clonal"
        if experiment.isolate.is_population:
            clonal_or_population = "population"

        media_temperature = experiment.isolate.flask.media.temperature

        media_description = experiment.isolate.flask.media.description

        substrate = experiment.isolate.flask.media.substrate

        # Using tuple because immutable; mc_list must remain associated with particular experiment.
        experiment_info_tuple = (experiment,
                                 mc_list,
                                 mapped_read_count,
                                 clonal_or_population,
                                 media_temperature,
                                 media_description,
                                 substrate)

        experiments_info_list.append(experiment_info_tuple)

    return experiments_info_list
