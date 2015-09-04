__author__ = 'pphaneuf'


from django.http import HttpResponse

from django.template import Context, loader

from ale.models import *    # TODO: only import necessary models.

from django.contrib.auth.decorators import login_required

import aleinfo.settings as settings

# TODO: used by multiple views. Also implemented within views.py; implement in one location.
DEFAULT_RESEQ_REPORT_URL = "http://localhost/sequencing/"


# TODO: used by multiple views. Also implemented within views.py; implement in one location.
if hasattr(settings, "sequencing_url"):
    reseqencing_report_url = settings.sequencing_url
else:
    reseqencing_report_url = DEFAULT_RESEQ_REPORT_URL


@login_required
def index(request):
    """display a list of ales with links to the resequencing"""

    experiments = AleExperiment.objects.all()

    template = loader.get_template("index.html")

    context = Context({"experiments": experiments,
                       "seq_url": reseqencing_report_url})

    return HttpResponse(template.render(context))