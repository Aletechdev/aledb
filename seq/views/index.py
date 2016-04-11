from django.http import HttpResponse

from django.template import Context, loader

from ale.models import *    # TODO: only import necessary models.

import seq.models

from django.contrib.auth.decorators import login_required

import aleinfo.settings as settings

from seq.views import common


__author__ = 'pphaneuf'

INDEX_TEMPLATE = "index.html"

MUTATION_TYPE_LIST = ['SNP', 'SUB', 'DEL', 'INS', 'MOB', 'AMP', 'CON', 'INV']


if hasattr(settings, common.SETTINGS_SEQUENCING_URL):
    reseqencing_report_url = settings.sequencing_url
else:
    reseqencing_report_url = common.DEFAULT_RESEQ_REPORT_URL


@login_required
def index(request):

    mutation_type_count_dict = {}
    for mutation_type in MUTATION_TYPE_LIST:
        mutation_type_count = seq.models.Mutation.objects.filter(mutation_type=mutation_type).count()
        mutation_type_count_dict[mutation_type] = mutation_type_count

    ale_experiments = AleExperiment.objects.all()

    template = loader.get_template(INDEX_TEMPLATE)

    context = Context({"mutation_type_count_dict": mutation_type_count_dict,
                       "experiments": ale_experiments,
                       "seq_url": reseqencing_report_url})

    return HttpResponse(template.render(context))
