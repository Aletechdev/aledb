from django.contrib.auth.decorators import login_required

from django.template import loader

from django.http import HttpResponse

from ale.models import AleExperiment

from common.db_util import get_all_ale_experiments, get_recent_experiments

from common.util import check_hidden_columns_and_filters

# Create your views here.


COMPARE_TEMPLATE = 'compare.html'


@login_required
def compare(request):

    all_experiments = get_all_ale_experiments()

    hidden_columns = check_hidden_columns_and_filters(request, None)

    first_exp_name = request.GET.get('first_exp', None)

    second_exp_name = request.GET.get('second_exp', None)

    if not first_exp_name or not second_exp_name:
        return handle_get_response(all_experiments, hidden_columns)

    first_exp = AleExperiment.objects.get(name=first_exp_name)

    second_exp = AleExperiment.objects.get(name=second_exp_name)

    title = "Comparison of %s and %s" % (first_exp_name, second_exp_name)

    context = {"experiments": all_experiments,
               "experiment_id": "%s,%s" % (first_exp.ale_id, second_exp.ale_id),
               "has_comparison": True,
               "first_exp_name": first_exp_name,
               "second_exp_name": second_exp_name,
               "title": title,
               "header": title,
               "recent_experiments": get_recent_experiments()}

    template = loader.get_template(COMPARE_TEMPLATE)

    return HttpResponse(template.render(context))


def handle_get_response(all_experiments, hidden_columns):

    context = {"experiments": all_experiments,
               "has_comparison": False,
               "hidden_columns": hidden_columns,
               "recent_experiments": get_recent_experiments(None),
               "title": "Compare",
               "header": "Compare"}

    template = loader.get_template(COMPARE_TEMPLATE)

    return HttpResponse(template.render(context))

