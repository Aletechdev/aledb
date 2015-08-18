from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.template import Context, loader
from django.utils.safestring import mark_safe

import aleinfo.settings as settings

from seq.models import *


# TODO: this URL is defined here and in seq/views.py; find a way to define in one place.
DEFAULT_RESEQ_REPORT_URL = "http://localhost/sequencing/"

TEMPLATE_LOCATION = "mutation_db_browser/table_template.html"

HTML_MUTATION_TABLE_HEADER = """<tr><td>Mutation</td><td>Gene</td><td>Protein change</td>"""

if hasattr(settings, "sequencing_url"):
    reseqencing_report_url = settings.sequencing_url
else:
    reseqencing_report_url = DEFAULT_RESEQ_REPORT_URL


@login_required
def mutations_db_browser(request):

    experiment_mapping = _get_experiment_mapping()

    table_header = _get_table_heater(experiment_mapping)

    table_body = _get_table_body(experiment_mapping)

    template = loader.get_template(TEMPLATE_LOCATION)
    context = Context({"experiments": _get_all_reseq_experiments(),
                       "ale_no": None,
                       "experiment_id": None,
                       "table_body": mark_safe(table_body),
                       "title": "Mutation Table",
                       "table_header": mark_safe(table_header)})

    return HttpResponse(template.render(context))


def _get_table_heater(experiment_mapping):

    table_header = HTML_MUTATION_TABLE_HEADER

    for checked_experiment_id in sorted(experiment_mapping):

        experiment = experiment_mapping[checked_experiment_id]

        mutation_identifier = experiment.isolate.flask.ale_id.ale_experiment.name\
                              + " "\
                              + experiment.get_isolate_name().replace("_", " ")

        table_header += """<td><input type="checkbox" class="cb" name=%s /><br>%s</td>""" % (
            experiment.id,
            mutation_identifier)

    table_header += "</tr>"

    return table_header


def _get_table_body(experiment_mapping):

    observed_mutations = _get_all_observed_mutations(experiment_mapping)

    mutations = Mutation.objects.filter(pk__in=observed_mutations.values_list("mutation", flat=True))
    mutation_mapping = dict((id, i) for i, id in enumerate(mutations.values_list("id", flat=True)))

    experiment_urls = _get_experiment_urls(experiment_mapping)

    table_entries = [["""<td class="false"></td>"""] * len(experiment_mapping) for i in range(len(mutations))]

    experiment_mapping = dict((o, i) for i, o in enumerate(sorted(experiment_mapping.keys())))

    for observed_mutation in observed_mutations:

        new_entry = _make_table_entry(observed_mutation, experiment_urls)

        if new_entry is not None:
            table_entries[mutation_mapping[observed_mutation.mutation_id]][
                experiment_mapping[observed_mutation.sequencing_experiment_id]] = new_entry

    table_body = ""

    for mutation in mutations:
        table_row = "<tr>"

        table_row += """<td>%d %s<a href="javascript:void(0)" class="shut" style="float:right;display:none;" onclick="deleteRow.call(this)"><img src="/static/DataTables/media/images/close-icon.gif" width="12" height="11"></a></td>""" % (
            mutation.position, mutation.sequence_change)

        table_row += "<td>%s</td>" % mutation.gene
        table_row += "<td>%s</td>" % mutation.protein_change
        table_row += "".join(table_entries[mutation_mapping[mutation.id]])
        table_row += "</tr>"
        table_body += table_row + "\n"

    return table_body


def _get_experiment_urls(experiment_mapping):
    experiment_urls = dict((i.id, reseqencing_report_url + i.location) for i in experiment_mapping.values())

    return experiment_urls


def _get_all_reseq_experiments():
    return ResequencingExperiment.objects.all()


def _get_experiment_mapping():
    all_reseq_experiments = _get_all_reseq_experiments()

    experiment_mapping = dict((o.id, o) for o in all_reseq_experiments)

    return experiment_mapping


def _get_all_observed_mutations(experiment_mapping):
    observed_mutations = ObservedMutation.objects.filter(sequencing_experiment_id__in=experiment_mapping.keys())

    return observed_mutations


def _make_table_entry(observed, experiment_urls):
    if observed.breseq_present:
        table_entry = """<td class="true">%s</td>""" % observed.evidence.replace("evidence/",
                                                                                 experiment_urls[
                                                                                     observed.sequencing_experiment_id] + "/evidence/")

    elif observed.present is False:
        table_entry = """<td class="false">%d/%d</td>""" % (observed.mutated_reads,
                                                            observed.wt_reads)

    return table_entry
