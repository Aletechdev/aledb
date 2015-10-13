# TODO: obsolete functionality; needs to be removed.


from django.http import HttpResponse

from django.template import Context, loader

from django.utils.safestring import mark_safe

from django.contrib.auth.decorators import login_required

from seq.models import *
from ale.models import *

import aleinfo.settings as settings

from seq.views import common


if hasattr(settings, common.SETTINGS_SEQUENCING_URL):
    reseqencing_report_url = settings.sequencing_url
else:
    reseqencing_report_url = common.DEFAULT_RESEQ_REPORT_URL


@login_required
def isolate_list(request):
    ale_experiment_id = request.GET.get(common.REQUEST_ALE_EXPERIMENT_ID)
    if ale_experiment_id is None:
        isolates = Isolate.objects.all()
    else:
        ale_experiment_id = int(ale_experiment_id)
        isolates = Isolate.objects.raw(
            """SELECT isolate_id AS id FROM id_mapping WHERE
            experiment_id=%d;""" % ale_experiment_id)
        """return a list of resequencing experiments"""
    template = loader.get_template("isolate_view.html")
    context = Context({"isolates": isolates, "seq_url": reseqencing_report_url})
    return HttpResponse(template.render(context))


@login_required
def experiment_table(request):
    experiments = common.get_seq_experiments(request)
    extra_validation = False if request.GET.get("novalid") else True
    experiment_mapping = dict((o.id, i) for i, o in enumerate(experiments))
    # cache the urls of the experiment location
    experiment_urls = dict((i.id, reseqencing_report_url + i.location) for i in experiments)
    observed_mutations = ObservedMutation.objects.filter(sequencing_experiment_id__in=experiment_mapping.keys())
    mutations = Mutation.objects.filter(pk__in=observed_mutations.values_list("mutation", flat=True))
    mutation_mapping = dict((id, i) for i, id in enumerate(mutations.values_list("id", flat=True)))
    table_entries = [[None] * len(mutation_mapping) for i in experiment_mapping]
    for observed in observed_mutations:
        # sometimes we do not want the extra validation
        if not extra_validation and not observed.breseq_present:
            continue
        table_entries[experiment_mapping[observed.sequencing_experiment_id]][mutation_mapping[observed.mutation_id]] = \
            common.get_table_mutation_entry(observed, experiment_urls)
    table_header = """<tr><td>Experiment</td>"""
    for mutation in mutations:
        if mutation.reference_error:
            table_header += """<td class="reference_error">%d %s</td>""" % (mutation.position, mutation.sequence_change)
        else:
            table_header += """<td>%d %s</td>""" % (mutation.position, mutation.sequence_change)
    table_header += "</tr>"
    table_body = ""
    for experiment in experiments:
        table_body += """<tr><td><a href="%s">%s</a></td>""" % (reseqencing_report_url + experiment.location, experiment.get_isolate_name())
        for column in table_entries[experiment_mapping[experiment.id]]:
            if column is None:
                table_body += """<td class="false"></td>"""
            else:
                table_body += column
    template = loader.get_template("table_template.html")
    context = Context(
        {"table_body": mark_safe(table_body), "title": "Experiment table", "table_header": mark_safe(table_header)})
    return HttpResponse(template.render(context))
