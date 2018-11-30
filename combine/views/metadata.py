from django.template import loader

from django.http import HttpResponse

from ale.models import AleExperiment

from common.util import get_user_context

from metadata.views import get_reseq_info_list

from django.conf import settings

from seq.views import common

from combine.views.common import get_ordered_reseq_dict_and_obs_mut_queryset
__author__ = 'dgosting'

META_DATA_TEMPLATE = 'metadata/index.html'

if hasattr(settings, "SEQUENCING_URL"):
    reseq_report_url = settings.SEQUENCING_URL
else:
    reseq_report_url = common.DEFAULT_RESEQ_REPORT_URL


def combined_metadata(request):

    ale_experiment_list = request.GET.get('ale_experiment_id', None).replace('[', '').replace(']', '').split(',')

    ordered_reseq_dict, queryset = get_ordered_reseq_dict_and_obs_mut_queryset(ale_experiment_list)

    reseq_info_list = get_reseq_info_list(ordered_reseq_dict.values())

    header = ", ".join([AleExperiment.objects.get(ale_id=ale_exp_id).name for ale_exp_id in ale_experiment_list])

    template = loader.get_template(META_DATA_TEMPLATE)

    context = get_user_context(request.user)
    context.update({"ale_experiment_name": header,
               "reseq_info_list": reseq_info_list,
               "reseq_report_url": reseq_report_url,
               "multiple": True
               })

    return HttpResponse(template.render(context, request), content_type="text/html")
