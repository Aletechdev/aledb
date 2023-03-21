from django.http import HttpResponse
from django.template import loader
from seq.views import common
from filter.forms.filter import FilterForm
from filter.models import AleExperimentFilter
import filter.models
from filter.common import DEFAULT_MUTATION_FREQ_MIN, DEFAULT_MUTATION_FREQ_MAX
from filter.util import get_ignored_mut_id_list_from_str
from common.util import clear_dashboard_cache, get_user_context
from seq.util import get_mutation_objects
from logs.aledb_logger import user_extra
from ale import permissions
import logging

logger = logging.getLogger(__name__)

__author__ = 'Denny Gosting, Patrick Phaneuf'

FILTER_TEMPLATE = "filter/experiment_filter.html"


def mutation_filter(request):
    logger.info("mutation filter", extra=user_extra(request))
    try:
        context = get_user_context(request.user)
        experiment = common.get_ale_experiment(request)

        template = loader.get_template(FILTER_TEMPLATE)

        filter_form_model, created = AleExperimentFilter.objects.get_or_create(
            ale_experiment=experiment,
            defaults=filter.models.get_default_experiment_filter_params(experiment))

        if request.method == 'POST':
            # check user permissions
            clear_dashboard_cache()
            _handle_POST(request, filter_form_model, experiment)

        filter_form = FilterForm(filter_form_model.__dict__)

        ignored_mutations = get_mutation_objects(filter_form_model.ignored_mutations)
        starting_strain_mutations = get_mutation_objects(filter_form_model.starting_strain_mutations)

        context.update({
            "form": filter_form,
            "experiment": experiment,
            "ale_experiment_id": experiment.ale_id,
            "ale_experiment_name": experiment.name,
            "ale_project_name": experiment.project.name,
            "ale_project_id": experiment.project.id,
            "ignored_mutations": ignored_mutations,
            "starting_strain_mutations": starting_strain_mutations})
        return HttpResponse(template.render(context, request), content_type="text/html")
    except Exception as e:
        logger.exception("stats broke", extra=user_extra(request))
        template = loader.get_template("500.html")
        context['err_message'] = str(e)
        return HttpResponse(template.render(context, request), content_type="text/html")


def _handle_POST(request, filter_form_model, experiment):
    filter_form = FilterForm(request.POST)
    if permissions.can_add_experiment_filter(request.user, experiment) and filter_form.is_valid():
        filter_form_model.min_cutoff = request.POST.get("min_cutoff", DEFAULT_MUTATION_FREQ_MIN)
        filter_form_model.max_cutoff = request.POST.get("max_cutoff", DEFAULT_MUTATION_FREQ_MAX)
        filter_form_model.ignored_genes = request.POST.get("ignored_genes", "")
        deleted_mut_id = request.POST.get('deleted_mut_id', None)
        ignored_mutation_id_list = get_ignored_mut_id_list_from_str(
            AleExperimentFilter.objects.get(ale_experiment_id=experiment.ale_id).ignored_mutations, deleted_mut_id)
        cleaned_list = get_ignored_mut_id_list_from_str(",".join(ignored_mutation_id_list))
        filter_form_model.ignored_mutations = ",".join(cleaned_list)
        filter_form_model.save()
    elif filter_form.is_valid():
        raise Exception("User doesn't have permission to edit experiment filter")
    else:
        print(filter_form.errors)
