__author__ = 'pphaneuf'


from django.contrib.auth.decorators import login_required

from django.template import Context, loader

from django.http import HttpResponse

from seq.views import common

import seq.models


DASHBOARD_TEMPLATE = "dashboard.html"


@login_required
def dashboard(request):
    mutation_type_count_dict = {}
    for mutation_type in common.MUTATION_TYPE_LIST:
        mutation_type_count = seq.models.Mutation.objects.filter(mutation_type=mutation_type).count()
        mutation_type_count_dict[mutation_type] = mutation_type_count

    protein_change_type_count_dict = {}
    for protein_change_type in common.PROTEIN_CHANGE_TYPE_LIST:
        protein_change_count = seq.models.Mutation.objects.filter(protein_change__contains=protein_change_type).count()
        protein_change_type_count_dict[protein_change_type] = protein_change_count

    context = Context({"protein_change_type_count_dict": protein_change_type_count_dict,
                       "mutation_type_count_dict": mutation_type_count_dict})

    template = loader.get_template(DASHBOARD_TEMPLATE)
    return HttpResponse(template.render(context))
