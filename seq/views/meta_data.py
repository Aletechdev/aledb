from django.contrib.auth.decorators import login_required

from django.http import HttpResponse

from django.template import Context, loader

import aleinfo.settings as settings

from seq.views import common


__author__ = 'Patrick Phaneuf'

META_DATA_TEMPLATE = "meta_data.html"


# TODO: used by multiple views. Also implemented within views.py; implement in one location.
if hasattr(settings, "sequencing_url"):
    resequencing_report_url = settings.sequencing_url
else:
    resequencing_report_url = common.DEFAULT_RESEQ_REPORT_URL


@login_required
def meta_data(request):
    """return a list of resequencing experiments"""

    experiments = common.get_seq_experiment_raw_queryset(request)

    # Would rather want to use something like a dictionary since an experiment is
    # unique, though an experiment is currently a structure and an integral type
    # that can be used as a key.

    experiments_info_list = _get_experiment_info_list(experiments)

    template = loader.get_template(META_DATA_TEMPLATE)

    ale_experiment_name = common.get_ale_experiment_name(request)

    context = Context({"experiments_info_list": experiments_info_list,
                       "resequencing_report_url": resequencing_report_url,
                       "ale_experiment_name": ale_experiment_name})

    return HttpResponse(template.render(context))


def _get_experiment_info_list(experiments):

    experiments_info_list = []

    for experiment in experiments:

        clonal_or_population = "clonal"

        if experiment.isolate.is_population:

            clonal_or_population = "population"

        experiment_info_tuple = (experiment,
                                 clonal_or_population,
                                 experiment.isolate.flask.media.temperature,
                                 experiment.isolate.flask.media.description,
                                 experiment.isolate.flask.media.substrate,
                                 experiment.isolate.flask.ale_id.species,
                                 experiment.isolate.flask.ale_id.strain,
                                 experiment.isolate.flask.ale_id.knockouts,  # TODO: switch to ale_id.description.
                                 experiment.isolate.library_prep,
                                 experiment.isolate.reseq_reference,
                                 experiment.isolate.breseq_version,
                                 experiment.isolate.reseq_date)

        experiments_info_list.append(experiment_info_tuple)

    return experiments_info_list
