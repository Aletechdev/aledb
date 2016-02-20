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


class filterForm(forms.Form):
    filter_field = forms.IntegerField(max_value=100, label="Minimum % Cutoff ", min_value=0, initial=5)

@login_required
def filter(request):
    ale_experiment_name = common.get_ale_experiment_name(request)

    template = loader.get_template(INDEX_TEMPLATE)

    context = Context({
        "form": filterForm(),
        "ale_experiment_name": ale_experiment_name
    })

    return HttpResponse(template.render(context))


def filter_table(table, cutoff=0.05):

    soup_table = soup(table, from_encoding='utf-8')
    filtered_table = ""
    rows = soup.find_all(soup_table, 'tr')
    for row in rows:
        table_row = "<tr>"
        cell = row.find_all('td')
        matches = 0
        for entry in cell:
            entry.find_all('class')
            text = entry.get_text()
            try:
                element = float(text)
                if element > cutoff:
                    matches += 1
                    table_row += entry.encode('utf-8')
            except ValueError:
                table_row += entry.encode('utf-8')
        table_row += "</tr>"
        if matches <= 1:
            continue
        filtered_table += table_row + "\n"

    return filtered_table
