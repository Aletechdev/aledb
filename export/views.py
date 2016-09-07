from django.contrib.auth.decorators import login_required

from django.template import loader

from django.http import HttpResponse

from common.db_util import get_all_ale_experiments, get_recent_experiments
# Create your views here.


EXPORT_TEMPLATE = 'export.html'


@login_required
def export(request):

    experiment_names = request.GET.get('download_experiments', None)

    if experiment_names:

        experiment_name_list = experiment_names.split(',')

        print(experiment_name_list)

    template = loader.get_template(EXPORT_TEMPLATE)

    context = {"experiments": get_all_ale_experiments(),
               "recent_experiments": get_recent_experiments()}

    return HttpResponse(template.render(context))
