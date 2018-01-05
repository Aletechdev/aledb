import json

from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse, JsonResponse
from django.template import loader
from django.utils.safestring import mark_safe

from ale.models import AleExperiment
from common.util import get_all_ale_exps, get_recent_ale_exps
from export.datapackage.observed_mutations import ObservedMutationsDataPackageWriter
from export.forms import ExportForm
from export.util import \
    get_csv_str, \
    MUT_TYPE_STR, \
    FIXED_MUT_TYPE_STR, \
    ENRICH_MUT_TYPE_STR

EXPORT_TEMPLATE = 'export.html'


def export(request):
    exp_name_str = request.GET.get('download_experiments', None)
    mut_type_str = request.GET.get('mut_type_selected', None)
    context = {
        "mut_types_str_list": [MUT_TYPE_STR, ENRICH_MUT_TYPE_STR, FIXED_MUT_TYPE_STR],
        "experiments": get_all_ale_exps(),
        "recent_experiments": get_recent_ale_exps(),
        "is_download": False
    }
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


def export_datapackage(request):
    form = ExportForm(request.GET, request.FILES)

    if not form.is_valid():
        return JsonResponse(form.errors, status=400)

    ale_experiments = form.cleaned_data['experiments']
    mutation_type = form.cleaned_data['mutation_type']

    package_writer = ObservedMutationsDataPackageWriter(ale_experiments=ale_experiments, mutation_type=mutation_type)
    output_buf = package_writer.write()
    output_buf.seek(0)

    response = HttpResponse(output_buf.read(), content_type="application/x-zip-compressed")
    response['Content-Disposition'] = 'attachment; filename={}'.format(package_writer.package_name)

    return response
