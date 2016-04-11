from django.http import HttpResponse

from django.template import Context, loader

from ale.models import *    # TODO: only import necessary models.

import seq.models

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

    mutation_type_count_dict = {}
    for mutation_type in common.MUTATION_TYPE_LIST:
        mutation_type_count = seq.models.Mutation.objects.filter(mutation_type=mutation_type).count()
        mutation_type_count_dict[mutation_type] = mutation_type_count

    protein_change_type_count_dict = {}
    for protein_change_type in common.PROTEIN_CHANGE_TYPE_LIST:
        protein_change_count = seq.models.Mutation.objects.filter(protein_change__contains=protein_change_type).count()
        protein_change_type_count_dict[protein_change_type] = protein_change_count

    print(protein_change_type_count_dict)

    ale_experiments = AleExperiment.objects.all()

    template = loader.get_template(INDEX_TEMPLATE)

    context = Context({"protein_change_type_count_dict": protein_change_type_count_dict,
                       "mutation_type_count_dict": mutation_type_count_dict,
                       "experiments": ale_experiments,
                       "seq_url": reseqencing_report_url})

    return HttpResponse(template.render(context))
