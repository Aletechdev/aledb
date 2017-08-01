from django.http import HttpResponse
from django.template import loader
from filter.forms.filter import FilterForm
from django.utils.safestring import mark_safe
from filter.util import get_ignored_mut_id_list_from_str, get_ignored_mutations, TABLE_HEADER, get_global_filter
from common.util import get_all_ale_exps, get_recent_ale_exps, clear_dashboard_cache

__author__ = 'Denny Gosting, Patrick Phaneuf'

GLOBAL_FILTER_TEMPLATE = "filter/global_filter.html"


def global_filter(request):

    template = loader.get_template(GLOBAL_FILTER_TEMPLATE)

    filter_form_model = get_global_filter()

    if request.method == 'POST':
        clear_dashboard_cache()
        _handle_POST(request, filter_form_model)

    initial_filter_form_data = {"ignored_genes": filter_form_model.ignored_genes}

    filter_form = FilterForm(initial=initial_filter_form_data)

    table_body, ignored_mutation_id_list = get_ignored_mutations(filter_form_model)

    context = {"form": filter_form,
               "table_body": mark_safe(table_body),
               "table_header": mark_safe(TABLE_HEADER),
               "experiments": get_all_ale_exps(),
               "recent_experiments": get_recent_ale_exps()}

    return HttpResponse(template.render(context))


def _handle_POST(request, filter_form_model):

    filter_form_model.ignored_genes = request.POST.get("ignored_genes", "")
    deleted_mut_id = request.POST.get('mut_id', None)
    ignored_mutation_id_list = get_ignored_mut_id_list_from_str(get_global_filter().ignored_mutations, deleted_mut_id)
    cleaned_list = get_ignored_mut_id_list_from_str(",".join(ignored_mutation_id_list))
    filter_form_model.ignored_mutations = ",".join(cleaned_list)
    filter_form_model.save()


