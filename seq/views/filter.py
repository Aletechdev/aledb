__author__ = 'dgosting'

from django.http import HttpResponse

from django.template import Context, loader

from django.contrib.auth.decorators import login_required

import aleinfo.settings as settings

from seq.views import common

from django import forms

from bs4 import BeautifulSoup as soup

INDEX_TEMPLATE = "filter.html"

if hasattr(settings, common.SETTINGS_SEQUENCING_URL):
    reseqencing_report_url = settings.sequencing_url
else:
    reseqencing_report_url = common.DEFAULT_RESEQ_REPORT_URL


class minForm(forms.Form):
    filter_field = forms.IntegerField(max_value=100, label="Minimum % Cutoff ", min_value=0, initial=20)


class maxForm(forms.Form):
    filter_field = forms.IntegerField(max_value=100, label="Maximum % Cutoff ", min_value=0, initial=100)

class ignoreGenesForm(forms.Form):
    filter_field = forms.CharField()



@login_required
def filter(request):
    ale_experiment_name = common.get_ale_experiment_name(request)

    template = loader.get_template(INDEX_TEMPLATE)

    ignored_genes = ["test", "other", 'first']

    context = Context({
        "minform": minForm(),
        "maxform": maxForm(),
        "gene_form": ignoreGenesForm(),
        "ignored_genes": ignored_genes,
        "ale_experiment_name": ale_experiment_name
    })

    return HttpResponse(template.render(context))


def filter_table(table, min_cutoff=0.20, max_cutoff=1.00, ignore_gene_list = []):
    ignore_gene_list = ["icd"]
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
