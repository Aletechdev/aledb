from django.http import HttpResponse

from django.template import Context, loader

from django.contrib.auth.decorators import login_required

import aleinfo.settings as settings

from seq.views import common

from bs4 import BeautifulSoup as soup

import seq

import ale.models

import seq.forms.filter


__author__ = 'dgosting'

INDEX_TEMPLATE = "filter.html"
INDEX_TEMPLATE_EDIT = "filter_edit_page.html"
ALE_TEMPLATE = "index.html"

if hasattr(settings, common.SETTINGS_SEQUENCING_URL):
    reseqencing_report_url = settings.sequencing_url
else:
    reseqencing_report_url = common.DEFAULT_RESEQ_REPORT_URL


# TODO: make 20 and 100 constants  to be referred to within some other global file.
@login_required
def create_filter(request):
    ale_experiment_name = common.get_ale_experiment_name(request)
    ale_experiment_id = seq.views.common.get_ale_experiment_id(request)
    template = loader.get_template(INDEX_TEMPLATE)

    default_filter_form_model = {'ale_experiment_id': ale_experiment_id,
                                 'min_cutoff': 20,
                                 'max_cutoff': 100,
                                 'ignored_genes': ""}

    if request.method == 'POST':

        filter_form = seq.forms.filter.FilterForm(request.POST)

        if filter_form.is_valid():
            filter_form_model, created = ale.models.Filter.objects.get_or_create(ale_experiment_id=ale_experiment_id,
                                                                      defaults=default_filter_form_model)

            filter_form_model.min_cutoff = request.POST.get("min_cutoff", 20)
            filter_form_model.max_cutoff = request.POST.get("max_cutoff", 100)
            filter_form_model.save()
        else:
            print filter_form.errors

    else:  # request.method == 'GET'
        filter_form_model, created = ale.models.Filter.objects.get_or_create(ale_experiment_id=ale_experiment_id,
                                                                  defaults=default_filter_form_model)
        initial_filter_form_data = {"min_cutoff": filter_form_model.min_cutoff,
                            "max_cutoff": filter_form_model.max_cutoff,
                            "ignored_genes": filter_form_model.ignored_genes}
        filter_form = seq.forms.filter.FilterForm(initial=initial_filter_form_data)

    context = Context({
        "form": filter_form,
        "ale_experiment_id": ale_experiment_id,
        "ale_experiment_name": ale_experiment_name
    })

    return HttpResponse(template.render(context))


def filter_table(table, min_cutoff=0.20, max_cutoff=1.00, ignore_gene_list=[]):
    soup_table = soup(table, from_encoding='utf-8')
    filtered_table = ""
    rows = soup.find_all(soup_table, 'tr')
    for row in rows:
        table_row = "<tr>"
        cell = row.find_all('td')
        skip_row = False
        for entry in cell:
            entry.find_all('class')
            text = entry.get_text()
            for gene in ignore_gene_list:
                if gene == text:
                    skip_row = True
            try:
                element = float(text)
                if min_cutoff <= element <= max_cutoff:
                    table_row += entry.encode('utf-8')
                else:
                    skip_row = True
            except ValueError:
                table_row += entry.encode('utf-8')
        if skip_row is True:
            continue
        table_row += "</tr>"
        filtered_table += table_row + "\n"

    return filtered_table

