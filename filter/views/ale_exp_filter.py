from django.http import HttpResponse

from django.template import loader

from django.contrib.auth.decorators import login_required

from seq.views import common

from filter.forms.filter import FilterForm

from filter.models import AleExperimentFilter

from filter.common import DEFAULT_MUTATION_FREQ_MIN, DEFAULT_MUTATION_FREQ_MAX

from django.utils.safestring import mark_safe

from filter.mutation_filter import clean_ignored_mutation_id_list, get_ignored_mutations, TABLE_HEADER

from common.db_util import get_all_ale_experiments, get_recent_experiments

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

    filter_form_model, created = AleExperimentFilter.objects.get_or_create(ale_experiment_id=ale_experiment_id,
                                                                           defaults=default_filter_form_model)

    if request.method == 'POST':
        _handle_POST(request, filter_form_model, ale_experiment_id)

    initial_filter_form_data = {"ignored_genes": filter_form_model.ignored_genes}

    filter_form = FilterForm(initial=initial_filter_form_data)

    table_body, ignored_mutation_id_list = get_ignored_mutations(filter_form_model)

    context = {"form": filter_form,
               "ale_experiment_id": ale_experiment_id,
               "ale_experiment_name": ale_experiment_name,
               "table_body": mark_safe(table_body),
               "table_header": mark_safe(TABLE_HEADER),
               "experiments": get_all_ale_experiments(),
               "recent_experiments": get_recent_experiments(ale_experiment_id)}

    return HttpResponse(template.render(context))


def _handle_POST(request, filter_form_model, ale_experiment_id):

    filter_form = FilterForm(request.POST)

    if filter_form.is_valid():
        filter_form_model.min_cutoff = request.POST.get("min_cutoff", DEFAULT_MUTATION_FREQ_MIN)
        filter_form_model.max_cutoff = request.POST.get("max_cutoff", DEFAULT_MUTATION_FREQ_MAX)
        filter_form_model.ignored_genes = request.POST.get("ignored_genes", "")
        deleted_mut_id = request.POST.get('mut_id', None)
        ignored_mutation_id_list = clean_ignored_mutation_id_list(
            AleExperimentFilter.objects.get(ale_experiment_id=ale_experiment_id).ignored_mutations, deleted_mut_id)
        cleaned_list = clean_ignored_mutation_id_list(",".join(ignored_mutation_id_list))
        filter_form_model.ignored_mutations = ",".join(cleaned_list)
        filter_form_model.save()
    else:
        print(filter_form.errors)

    return
