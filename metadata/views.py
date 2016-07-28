from django.contrib.auth.decorators import login_required

from django.http import HttpResponse

from django.template import Context, loader

import aleinfo.settings as settings

from seq.views import common


__author__ = 'Patrick Phaneuf'

META_DATA_TEMPLATE = "metadata/index.html"


# TODO: used by multiple views. Also implemented within views.py; implement in one location.
if hasattr(settings, "sequencing_url"):
    reseq_report_url = settings.sequencing_url
else:
    reseq_report_url = common.DEFAULT_RESEQ_REPORT_URL


@login_required
def meta_data(request):
    reseq_queryset = common.get_reseq_queryset(request)

    # Would rather want to use something like a dictionary since an experiment is
    # unique, though an experiment is currently a structure and an integral type
    # that can be used as a key.

    reseq_info_list = get_reseq_info_list(reseq_queryset)

    template = loader.get_template(META_DATA_TEMPLATE)

    ale_experiment_name = common.get_ale_experiment_name(request)

    context = Context({"reseq_info_list": reseq_info_list,
                       "reseq_report_url": reseq_report_url,
                       "ale_experiment_name": ale_experiment_name})

    return HttpResponse(template.render(context))


def get_reseq_info_list(reseq_queryset):

    reseq_info_list = []

    for reseq in reseq_queryset:

        clonal_or_population = "clonal"

        if reseq.isolate.is_population:

            clonal_or_population = "population"

        experiment_info_tuple = (reseq,
                                 clonal_or_population,
                                 reseq.isolate.flask.media.temperature,
                                 reseq.isolate.flask.media.description,
                                 reseq.isolate.flask.media.substrate,
                                 reseq.isolate.flask.ale_id.species,
                                 reseq.isolate.flask.ale_id.strain,
                                 reseq.isolate.flask.ale_id.knockouts,  # TODO: switch to ale_id.description.
                                 reseq.isolate.library_prep,
                                 reseq.isolate.reseq_reference,
                                 reseq.isolate.breseq_version,
                                 reseq.isolate.reseq_date)

        reseq_info_list.append(experiment_info_tuple)

    return reseq_info_list
