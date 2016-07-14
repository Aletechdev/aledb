from django.http import HttpResponse

from django.template import Context, loader

from django.contrib.auth.decorators import login_required

from seq.views import common

from filter.forms.filter import FilterForm

from filter.models import Filter

import json

from filter.common import DEFAULT_MUTATION_FREQ_MIN
from filter.common import DEFAULT_MUTATION_FREQ_MAX

__author__ = 'Denny Gosting, Patrick Phaneuf'

FILTER_TEMPLATE = "filter/index.html"


@login_required
def mutation_filter(request):
    ale_experiment_name = common.get_ale_experiment_name(request)
    ale_experiment_id = common.get_ale_experiment_id(request)
    template = loader.get_template(FILTER_TEMPLATE)

    default_filter_form_model = {'ale_experiment_id': ale_experiment_id,
                                 'min_cutoff': DEFAULT_MUTATION_FREQ_MIN,
                                 'max_cutoff': DEFAULT_MUTATION_FREQ_MAX,
                                 'ignored_genes': "",
                                 'ignored_mutations': ""}

    filter_form_model, created = Filter.objects.get_or_create(ale_experiment_id=ale_experiment_id,
                                                              defaults=default_filter_form_model)

    if request.method == 'POST':
        filter_form = _handle_POST(request, filter_form_model)
    else:
        filter_form = _handle_GET(request, filter_form_model)

    context = Context({
        "form": filter_form,
        "ale_experiment_id": ale_experiment_id,
        "ale_experiment_name": ale_experiment_name,
    })

    return HttpResponse(template.render(context))


def _handle_POST(request, filter_form_model):
    filter_form = FilterForm(request.POST)

    if filter_form.is_valid():
        filter_form_model.min_cutoff = request.POST.get("min_cutoff", DEFAULT_MUTATION_FREQ_MIN)
        filter_form_model.max_cutoff = request.POST.get("max_cutoff", DEFAULT_MUTATION_FREQ_MAX)
        filter_form_model.ignored_genes = request.POST.get("ignored_genes", "")
        filter_form_model.ignored_mutations = _get_ignored_mutations_json(request)
        filter_form_model.save()
    else:
        print(filter_form.errors)

    return filter_form


def _handle_GET(request, filter_form_model):
    ignored_mutations_dict = [{}]
    if filter_form_model.ignored_mutations != "":
        ignored_mutations_dict = json.loads(filter_form_model.ignored_mutations)

    initial_filter_form_data = {"min_cutoff": filter_form_model.min_cutoff,
                                "max_cutoff": filter_form_model.max_cutoff,
                                "ignored_genes": filter_form_model.ignored_genes,
                                "ignored_mutations": ignored_mutations_dict}

    filter_form = FilterForm(initial=initial_filter_form_data)

    return filter_form


def _get_ignored_mutations_json(request):
    ignored_mutations_string = request.POST.get("ignored_mutations", "")
    ignored_mutations_json = [{}]
    if ignored_mutations_string != "":
        ignored_mutations_json = json.loads(ignored_mutations_string)
    return json.dumps(ignored_mutations_json)
