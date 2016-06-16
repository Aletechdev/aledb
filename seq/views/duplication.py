__author__ = 'dgosting'

from django.http import HttpResponse

from django.template import Context, loader

from django.contrib.auth.decorators import login_required

import aleinfo.settings as settings

from seq.views import common

import seq

import operator

import os

import requests


INDEX_TEMPLATE = "duplication.html"

if hasattr(settings, common.SETTINGS_SEQUENCING_URL):
    reseqencing_report_url = settings.sequencing_url
else:
    reseqencing_report_url = common.DEFAULT_RESEQ_REPORT_URL


@login_required
def duplication(request):

    ale_experiment_name = common.get_ale_experiment_name(request)

    ale_experiment_id = seq.views.common.get_ale_experiment_id(request)

    template = loader.get_template(INDEX_TEMPLATE)

    seq_experiment_ordered_dict = common.get_experiment_ordered_dict(request, include_starting_strain=True)

    seq_experiment_ordered_dict = common.filter_checked_flasks(request, seq_experiment_ordered_dict)

    experiment_urls = common._get_experiment_urls(seq_experiment_ordered_dict)

    experiment_id_idx_mapping = common._get_experiment_id_idx_mapping(seq_experiment_ordered_dict)

    sorted_experiment_url_indices = sorted(experiment_id_idx_mapping.items(), key=operator.itemgetter(1))

    experiemnt_links = []

    for experiment_url_index in sorted_experiment_url_indices:

        temp = os.path.dirname(os.path.dirname(experiment_urls[experiment_url_index[0]]))

        basename = os.path.basename(temp)

        temp = os.path.dirname(temp)

        url = temp + "/dups/" + basename + "/" + basename + ".html"

        response = requests.get(url, auth=('ale', 'olalemutats'))
        if response.status_code == 200:
            experiemnt_links.append((url, basename))
        else:
            experiemnt_links.append((False, basename))




    context = Context({
        "experiemnt_links": experiemnt_links,
        "reseqencing_report_url": reseqencing_report_url,
        "ale_experiment_id": ale_experiment_id,
        "ale_experiment_name": ale_experiment_name
    })

    return HttpResponse(template.render(context))

