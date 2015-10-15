from django.http import HttpResponse

from django.template import Context, loader

from ale.models import *    # TODO: only import necessary models.

from django.contrib.auth.decorators import login_required

import aleinfo.settings as settings

from seq.views import common


__author__ = 'pphaneuf'

INDEX_TEMPLATE = "index.html"


if hasattr(settings, common.SETTINGS_SEQUENCING_URL):
    reseqencing_report_url = settings.sequencing_url
else:
    reseqencing_report_url = common.DEFAULT_RESEQ_REPORT_URL


@login_required
def index(request):
    """display a list of ales with links to the resequencing"""

    experiments = AleExperiment.objects.all()

    template = loader.get_template(INDEX_TEMPLATE)

    context = Context({"experiments": experiments,
                       "seq_url": reseqencing_report_url})

    return HttpResponse(template.render(context))
