from django.contrib.auth.decorators import login_required

from django.template import loader

from django.http import HttpResponse

from ale.models import AleExperiment

from common.db_util import get_all_ale_experiments, get_recent_experiments

from metadata.views import get_reseq_info_list

import aleinfo.settings as settings

from seq.views import common

from compare.views.common import get_ordered_reseq_dict_and_queryset
__author__ = 'dgosting'

META_DATA_TEMPLATE = 'metadata/index.html'

if hasattr(settings, "sequencing_url"):
    reseq_report_url = settings.sequencing_url
else:
    reseq_report_url = common.DEFAULT_RESEQ_REPORT_URL


@login_required
def comparison_metadata(request):

    all_experiments = get_all_ale_experiments()

    first_exp_name = request.GET.get('first_exp', None)

    second_exp_name = request.GET.get('second_exp', None)

    first_exp = AleExperiment.objects.get(name=first_exp_name)

    second_exp = AleExperiment.objects.get(name=second_exp_name)

    ale_experiment_list = [first_exp.ale_id, second_exp.ale_id]

    ordered_reseq_dict, queryset = get_ordered_reseq_dict_and_queryset(ale_experiment_list)

    reseq_info_list = get_reseq_info_list(ordered_reseq_dict.values())

    name = "%s and %s" % (first_exp_name, second_exp_name)

    title = "Meta Data Comparison of %s" % name

    template = loader.get_template(META_DATA_TEMPLATE)

    context = {"experiments": all_experiments,
               "experiment_id": "%s,%s" % (first_exp.ale_id, second_exp.ale_id),
               "title": title,
               "header": title,
               "recent_experiments": get_recent_experiments(),
               "reseq_info_list": reseq_info_list,
               "reseq_report_url": reseq_report_url,
               "ale_experiment_name": name,
               }

    return HttpResponse(template.render(context))
