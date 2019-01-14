from django.http import HttpResponse
from django.template import loader
from filter.forms.filter import FilterForm
from django.utils.safestring import mark_safe
from filter.util import get_ignored_mut_id_list_from_str, get_ignored_mutations, TABLE_HEADER, get_global_filter
from common.util import clear_dashboard_cache, get_user_context
from logs.aledb_logger import user_extra
from ale import permissions
import logging

__author__ = 'Denny Gosting, Patrick Phaneuf'

GLOBAL_FILTER_TEMPLATE = "filter/global_filter.html"

logger = logging.getLogger(__name__)


def global_filter(request):
    logger.info("global filter usage", extra=user_extra(request))
    try:
        template = loader.get_template(GLOBAL_FILTER_TEMPLATE)

        filter_form_model = get_global_filter()

        if request.method == 'POST':
            clear_dashboard_cache()
            _handle_POST(request, filter_form_model)

        initial_filter_form_data = {"ignored_genes": filter_form_model.ignored_genes}

        filter_form = FilterForm(initial=initial_filter_form_data)

        table_body, ignored_mutation_id_list = get_ignored_mutations(filter_form_model)

        context = get_user_context(request.user)
        context.update({
            "form": filter_form,
            "table_body": mark_safe(table_body),
            "table_header": mark_safe(TABLE_HEADER)})

        return HttpResponse(template.render(context, request), content_type="text/html")

    except Exception as e:
        logger.exception("global filter broke", extra=user_extra(request))
        template = loader.get_template("500.html")
        context['err_message'] = str(e)
        return HttpResponse(template.render(context, request), content_type="text/html")


def _handle_POST(request, filter_form_model):
    if permissions.can_add_global_filter(request.user):
        filter_form_model.ignored_genes = request.POST.get("ignored_genes", "")
        deleted_mut_id = request.POST.get('mut_id', None)
        ignored_mutation_id_list = get_ignored_mut_id_list_from_str(get_global_filter().ignored_mutations, deleted_mut_id)
        cleaned_list = get_ignored_mut_id_list_from_str(",".join(ignored_mutation_id_list))
        filter_form_model.ignored_mutations = ",".join(cleaned_list)
        filter_form_model.save()
    else:
        raise Exception("User doesn't have permission to edit global filter")


