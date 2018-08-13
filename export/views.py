from django.template import loader
from django.http import HttpResponse
from common.util import common_context
from ale.models import AleExperiment
from django.core.serializers.json import DjangoJSONEncoder
import json
from django.utils.safestring import mark_safe
from export.util import \
    get_csv_str, \
    MUT_TYPE_STR, \
    FIXED_MUT_TYPE_STR, \
    CONVERGED_MUT_TYPE_STR


EXPORT_TEMPLATE = 'export.html'


def export(request):
    exp_name_str = request.GET.get('download_experiments', None)
    mut_type_str = request.GET.get('mut_type_selected', None)
    context = common_context.copy()
    context.update({
        "mut_types_str_list": [MUT_TYPE_STR, CONVERGED_MUT_TYPE_STR, FIXED_MUT_TYPE_STR],
        "is_download": False
    })
    if exp_name_str and mut_type_str:
        if exp_name_str == 'All':
            exp_list = [(exp.ale_id, exp.name) for exp in AleExperiment.objects.all()]
        else:
            exp_name_list = exp_name_str.split(',')
            exp_list = [(AleExperiment.objects.get(name=exp_name).ale_id, exp_name) for exp_name in exp_name_list]

        csv_str = [(get_csv_str(exp_id, mut_type_str), exp_name) for exp_id, exp_name in exp_list]
        context['data'] = mark_safe(json.dumps(csv_str, cls=DjangoJSONEncoder))
        context['is_download'] = True

    template = loader.get_template(EXPORT_TEMPLATE)

    return HttpResponse(template.render(context, request), content_type="text/html")


