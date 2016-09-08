from django.http import HttpResponse

from django.template import loader

from django.contrib.auth.decorators import login_required

from filter.forms.filter import FilterForm

from django.utils.safestring import mark_safe

from filter.models import GlobalFilter

from filter.mutation_filter import clean_ignored_mutation_id_list, get_ignored_mutations, TABLE_HEADER

from common.db_util import get_all_ale_experiments, get_recent_experiments, clear_dashboard_cache

__author__ = 'Denny Gosting, Patrick Phaneuf'

GLOBAL_FILTER_TEMPLATE = "filter/global_filter.html"


@login_required
def global_filter(request):

    template = loader.get_template(GLOBAL_FILTER_TEMPLATE)

    filter_form_model, created = GlobalFilter.objects.get_or_create(id=1)

    if request.method == 'POST':
        clear_dashboard_cache()
        _handle_POST(request, filter_form_model)

    initial_filter_form_data = {"ignored_genes": filter_form_model.ignored_genes}

    filter_form = FilterForm(initial=initial_filter_form_data)

    table_body, ignored_mutation_id_list = get_ignored_mutations(filter_form_model)

    context = {"form": filter_form,
               "table_body": mark_safe(table_body),
               "table_header": mark_safe(TABLE_HEADER),
               "experiments": get_all_ale_experiments(),
               "recent_experiments": get_recent_experiments()}

    return HttpResponse(template.render(context))


def _handle_POST(request, filter_form_model):

    filter_form_model.ignored_genes = request.POST.get("ignored_genes", "")
    deleted_mut_id = request.POST.get('mut_id', None)
    ignored_mutation_id_list = clean_ignored_mutation_id_list(
        GlobalFilter.objects.get(id=1).ignored_mutations, deleted_mut_id)
    cleaned_list = clean_ignored_mutation_id_list(",".join(ignored_mutation_id_list))
    filter_form_model.ignored_mutations = ",".join(cleaned_list)
    filter_form_model.save()


