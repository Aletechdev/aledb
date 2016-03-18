__author__ = 'dgosting'

from django.http import HttpResponse

from django.template import Context, loader

from django.contrib.auth.decorators import login_required

import aleinfo.settings as settings

from seq.views import common

from django import forms

# from ale.models import Filter
from seq.models import Filter

from bs4 import BeautifulSoup as soup

import seq

INDEX_TEMPLATE = "filter.html"
INDEX_TEMPLATE_EDIT = "filter_edit_page.html"
ALE_TEMPLATE = "index.html"

if hasattr(settings, common.SETTINGS_SEQUENCING_URL):
    reseqencing_report_url = settings.sequencing_url
else:
    reseqencing_report_url = common.DEFAULT_RESEQ_REPORT_URL


class FilterForm(forms.ModelForm):
    min_cutoff = forms.IntegerField(min_value=0, max_value=100, required=False, initial=20)
    max_cutoff = forms.IntegerField(min_value=0, max_value=100, required=False, initial=100)

    def has_changed(self):
        return True

    class Meta:
        model = Filter
        fields = ["min_cutoff", "max_cutoff"]


@login_required
def create_filter(request):
    ale_experiment_name = common.get_ale_experiment_name(request)
    ale_experiment_id = seq.views.common.get_ale_experiment_id(request)

    template = loader.get_template(INDEX_TEMPLATE)

    if request.method == 'POST':

        # print "Saving"
        f = FilterForm(request.POST)
        if f.is_valid():
            # print "Is Valid"
            save_it = f.save(commit=False)
            save_it.pk = ale_experiment_id
            save_it.save()
            # f = Filter.objects.get(pk=ale_experiment_id)
        else:
            print f.errors

        request.method = 'GET'
        return create_filter(request)

    else:
        # print "Getting"
        try:
            f = Filter.objects.get(pk=ale_experiment_id)
            min_cut = seq.views.common.get_experiment_min_cutoff(ale_experiment_id)
            max_cut = seq.views.common.get_experiment_max_cutoff(ale_experiment_id)
            ignored_gene_list = seq.views.common.get_experiment_ignored_genes(ale_experiment_id)
            initial_data = {"min_cutoff": min_cut, "max_cutoff": max_cut, "ignored_genes": ignored_gene_list}
            new_entry = FilterForm(initial=initial_data)
            if f is not None:
                print "Got the filter: ", f
            else:
                print "F is None"

        except:
            print "Failed to get"

            f = FilterForm()
            new_entry = FilterForm()
            save_it = f.save(commit=False)
            save_it.pk = ale_experiment_id
            save_it.save()
            f = Filter.objects.get(pk=ale_experiment_id)

    context = Context({
        "form": new_entry,
        "data": f,
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

