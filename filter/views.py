from django.http import HttpResponse

from django.template import loader

from django.contrib.auth.decorators import login_required

from seq.views import common

from filter.forms.filter import FilterForm

from filter.models import AleExperimentFilter

import simplejson as json

from filter.common import DEFAULT_MUTATION_FREQ_MIN
from filter.common import DEFAULT_MUTATION_FREQ_MAX

from django.utils.safestring import mark_safe

from seq.views.mutation_table_builder import HTML_MUTATION_TABLE_ROW

from  filter.models import GlobalFilter

__author__ = 'Denny Gosting, Patrick Phaneuf'

FILTER_TEMPLATE = "filter/index.html"

TABLE_HEADER = "<tr><td></td><td>Position</td><td>Mutation Type</td><td>Sequence Change</td><td>Gene</td><td>Protein Change</td></tr>"


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

    filter_form_model, created = AleExperimentFilter.objects.get_or_create(ale_experiment_id=ale_experiment_id,
                                                                           defaults=default_filter_form_model)

    if request.method == 'POST':
        filter_form = _handle_POST(request, filter_form_model)
    else:
        filter_form = _handle_GET(request, filter_form_model)

    ignored_mutations, table_body = _get_ignored_mutations(filter_form)

    context = {"form": filter_form,
               "ale_experiment_id": ale_experiment_id,
               "ale_experiment_name": ale_experiment_name,
               "table_body": mark_safe(table_body),
               "table_header": mark_safe(TABLE_HEADER),
               "ignored_mutations": ignored_mutations
    }

    return HttpResponse(template.render(context))


def _handle_POST(request, filter_form_model):

    filter_form = FilterForm(request.POST)

    if filter_form.is_valid():
        filter_form_model.min_cutoff = request.POST.get("min_cutoff", DEFAULT_MUTATION_FREQ_MIN)
        filter_form_model.max_cutoff = request.POST.get("max_cutoff", DEFAULT_MUTATION_FREQ_MAX)
        filter_form_model.ignored_genes = request.POST.get("ignored_genes", "")
        filter_form_model.ignored_mutations = _save_ignored_mutations(request)
        filter_form_model.save()
    else:
        print(filter_form.errors)

    return filter_form


def _handle_GET(request, filter_form_model):

    initial_filter_form_data = {"min_cutoff": filter_form_model.min_cutoff,
                                "max_cutoff": filter_form_model.max_cutoff,
                                "ignored_genes": filter_form_model.ignored_genes,
                                "ignored_mutations": filter_form_model.ignored_mutations}

    filter_form = FilterForm(initial=initial_filter_form_data)

    return filter_form


def _get_ignored_mutations(filter_form):

    table_body = ""
    ignored_mutations = []
    try:
        ignored_mutation_value = str(filter_form['ignored_mutations'].value()).replace("'", '"')
        ignored_mutations = json.loads(ignored_mutation_value)
        for ignored_mutation in ignored_mutations:
            table_row = "<tr>"
            table_row += HTML_MUTATION_TABLE_ROW
            table_row += "<td>" + _get_position(ignored_mutation) + "</td>"
            table_row += "<td>" + _get_type(ignored_mutation) + "</td>"
            table_row += "<td>" + _get_sequence(ignored_mutation) + "</td>"
            table_row += "<td>" + _get_gene(ignored_mutation) + "</td>"
            table_row += "<td>" + _get_protein(ignored_mutation) + "</td>"
            table_row += "</tr>"
            table_body += table_row
        ignored_mutations = ignored_mutation_value
    except Exception as e:
        print(e)
        pass
    return ignored_mutations, table_body


def _get_position(ignored_mutation):

    try:
        return str(ignored_mutation['position']).replace(" ", "")
    except:
        return ""


def _get_type(ignored_mutation):
    try:
        return str(ignored_mutation['type']).replace(" ", "")
    except:
        return ""


def _get_sequence(ignored_mutation):
    try:
        return str(ignored_mutation['sequence']).replace(" ", "")
    except:
        return ""


def _get_gene(ignored_mutation):
    try:
        return str(ignored_mutation['gene']).replace(" ", "")
    except:
        return ""


def _get_protein(ignored_mutation):
    try:
        return str(ignored_mutation['protein']).replace(" ", "")
    except:
        return ""


def _save_ignored_mutations(request):

    ignored_mutations = request.POST.get("ignored_mutations", "")

    ignored_mutations_json = json.loads(str(ignored_mutations).replace("'", '"'))

    for ignored_mutation in ignored_mutations_json:

        ignored_mutation['position'] = _get_position(ignored_mutation)
        ignored_mutation['type'] = _get_type(ignored_mutation)
        ignored_mutation['sequence'] = _get_sequence(ignored_mutation)
        ignored_mutation['gene'] = _get_gene(ignored_mutation)
        ignored_mutation['protein'] = _get_protein(ignored_mutation)

    return str(ignored_mutations_json)


def global_filter(request):

    template = loader.get_template('filter/global_filter.html')

    filter_form_model, created = GlobalFilter.objects.get_or_create(id=1)

    if request.method == 'POST':
        filter_form = _handle_POST(request, filter_form_model)
    else:
        filter_form = _handle_GET(request, filter_form_model)

    ignored_mutations, table_body = _get_ignored_mutations(filter_form)

    context = {"form": filter_form,
               "table_body": mark_safe(table_body),
               "table_header": mark_safe(TABLE_HEADER),
               "ignored_mutations": ignored_mutations
               }

    return HttpResponse(template.render(context))
