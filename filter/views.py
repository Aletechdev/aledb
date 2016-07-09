from django.http import HttpResponse, HttpResponseRedirect

from django.template import Context, loader

from django.contrib.auth.decorators import login_required

import aleinfo.settings as settings

from seq.views import common

import seq

import ale.models

from filter.forms.filter import FilterForm


__author__ = 'Denny Gosting, Patrick Phaneuf'


FILTER_TEMPLATE = "filter/index.html"
INDEX_TEMPLATE_EDIT = "filter_edit_page.html"   #TODO: remove since not being used
ALE_TEMPLATE = "index.html"                     #TODO: remove since not being used


if hasattr(settings, common.SETTINGS_SEQUENCING_URL):
    reseqencing_report_url = settings.sequencing_url
else:
    reseqencing_report_url = common.DEFAULT_RESEQ_REPORT_URL


# TODO: make 20 and 100 constants  to be referred to within some other global file.
@login_required
def filter(request):
    ale_experiment_name = common.get_ale_experiment_name(request)
    ale_experiment_id = seq.views.common.get_ale_experiment_id(request)
    template = loader.get_template(FILTER_TEMPLATE)

    default_filter_form_model = {'ale_experiment_id': ale_experiment_id,
                                 'min_cutoff': 20,
                                 'max_cutoff': 100,
                                 'ignored_genes': "",
                                 'ignored_mutations': ""}

    if request.method == 'POST':

        filter_form = FilterForm(request.POST)

        if filter_form.is_valid():
            filter_form_model, created = ale.models.Filter.objects.get_or_create(ale_experiment_id=ale_experiment_id,
                                                                                 defaults=default_filter_form_model)

            filter_form_model.min_cutoff = request.POST.get("min_cutoff", 20)
            filter_form_model.max_cutoff = request.POST.get("max_cutoff", 100)
            filter_form_model.ignored_genes = request.POST.get("ignored_genes", "")
            filter_form_model.ignored_mutations = request.POST.get("ignored_mutations", "")
            filter_form_model.save()
        else:
            print(filter_form.errors)

    else:  # request.method == 'GET'
        filter_form_model, created = ale.models.Filter.objects.get_or_create(ale_experiment_id=ale_experiment_id,
                                                                             defaults=default_filter_form_model)
        initial_filter_form_data = {"min_cutoff": filter_form_model.min_cutoff,
                                    "max_cutoff": filter_form_model.max_cutoff,
                                    "ignored_genes": filter_form_model.ignored_genes,
                                    "ignored_mutations": filter_form_model.ignored_mutations}

        filter_form = FilterForm(initial=initial_filter_form_data)

    context = Context({
        "form": filter_form,
        "ale_experiment_id": ale_experiment_id,
        "ale_experiment_name": ale_experiment_name,
    })

    return HttpResponse(template.render(context))
