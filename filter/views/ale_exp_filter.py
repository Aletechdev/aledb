from django.http import HttpResponse
from django.template import loader
from django.contrib.auth.decorators import login_required, permission_required
from seq.views import common
from filter.forms.filter import FilterForm
from filter.models import AleExperimentFilter
import filter.models
from filter.common import DEFAULT_MUTATION_FREQ_MIN, DEFAULT_MUTATION_FREQ_MAX
from django.utils.safestring import mark_safe
from filter.util import get_ignored_mut_id_list_from_str, get_ignored_mutations, TABLE_HEADER, is_number
from ale.utils import get_recent_ale_exps
from common.util import clear_dashboard_cache, get_user_context
from seq.models import Mutation
from logs.aledb_logger import get_logger, user_extra

exception_lgr = get_logger("exceptions")
usage_lgr = get_logger("usage")
performance_lgr = get_logger("performance")

__author__ = 'Denny Gosting, Patrick Phaneuf'

FILTER_TEMPLATE = "filter/index.html"

STARTING_STRAIN_HEADER = """<tr><td>Position</td><td>Mutation Type</td><td>Sequence Change</td><td>Gene</td><td>Function</td><td>Product</td><td>GO Process</td><td>GO Component</td><td>Details</td></tr>"""


@login_required
def mutation_filter(request):
	usage_lgr.info("mutation filter", extra=user_extra(request))
	try:
		context = get_user_context(request.user)
		experiment = common.get_ale_experiment(request)

		ale_experiment_name = experiment.name
		ale_experiment_id = experiment.ale_id

		template = loader.get_template(FILTER_TEMPLATE)

		filter_form_model, created = AleExperimentFilter.objects.get_or_create(
			ale_experiment=experiment,
			defaults=filter.models.get_default_experiment_filter_params(experiment))

		if request.method == 'POST':
			clear_dashboard_cache()
			_handle_POST(request, filter_form_model, ale_experiment_id)

		filter_form = FilterForm(filter_form_model.__dict__)

		table_body, ignored_mutation_id_list = get_ignored_mutations(filter_form_model)

		starting_strain_body = get_starting_strain_mutations(filter_form_model)

		context.update({
			"form": filter_form,
			"experiment": experiment,
			"table_body": mark_safe(table_body),
			"table_header": mark_safe(TABLE_HEADER),
			"recent_experiments": get_recent_ale_exps(ale_experiment_id),
			"starting_strain_body": mark_safe(starting_strain_body),
			"starting_strain_header": mark_safe(STARTING_STRAIN_HEADER)})
		return HttpResponse(template.render(context, request), content_type="text/html")
	except Exception as e:
		exception_lgr.exception("stats broke", extra=user_extra(request))
		template = loader.get_template("500.html")
		context['err_message'] = str(e)
		return HttpResponse(template.render(context, request), content_type="text/html")


def _handle_POST(request, filter_form_model, ale_experiment_id):
	filter_form = FilterForm(request.POST)

	if filter_form.is_valid():
		filter_form_model.min_cutoff = request.POST.get("min_cutoff", DEFAULT_MUTATION_FREQ_MIN)
		filter_form_model.max_cutoff = request.POST.get("max_cutoff", DEFAULT_MUTATION_FREQ_MAX)
		filter_form_model.ignored_genes = request.POST.get("ignored_genes", "")
		deleted_mut_id = request.POST.get('mut_id', None)
		ignored_mutation_id_list = get_ignored_mut_id_list_from_str(
			AleExperimentFilter.objects.get(ale_experiment_id=ale_experiment_id).ignored_mutations, deleted_mut_id)
		cleaned_list = get_ignored_mut_id_list_from_str(",".join(ignored_mutation_id_list))
		filter_form_model.ignored_mutations = ",".join(cleaned_list)
		filter_form_model.save()
	else:
		print(filter_form.errors)

	return


def get_starting_strain_mutations(filter_form_model):
	mutation_id_list = filter_form_model.starting_strain_mutations.split(',')

	table_body = ""

	for mut_id in mutation_id_list:

		if is_number(mut_id):
			mutation = Mutation.objects.get(id=mut_id)

			table_row = "<tr>"

			table_row += "<td>%s</td>" % format(int(mutation.position), ',d')
			table_row += "<td>%s</td>" % mutation.mutation_type
			table_row += "<td>%s</td>" % mutation.sequence_change
			table_row += "<td>%s</td>" % mutation.gene
			table_row += "<td>%s</td>" % mutation.function
			table_row += "<td>%s</td>" % mutation.product
			table_row += "<td>%s</td>" % mutation.go_process
			table_row += "<td>%s</td>" % mutation.go_component
			table_row += "<td>%s</td>" % mutation.protein_change

			table_row += "</tr>"

			table_body += table_row + "\n"

	return table_body
