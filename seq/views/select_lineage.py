from django.contrib.auth.decorators import login_required

from django.template import Context, loader

from django.http import HttpResponse

from seq.views import common

from ale.models import *  # TODO: only import necessary models.

from django.utils.safestring import mark_safe

__author__ = 'pphaneuf'


# Provide a table showing frequencies of each observed mutation in the lineage
@login_required
def select_lineage(request):
    experiments = common.get_seq_experiments(request)
    ale_experiment_id = int(request.GET.get(common.REQUEST_ALE_EXPERIMENT_ID))
    table_body = ""
    experiment_set = dict((e.ale_id, set()) for e in experiments)
    for i in experiment_set:
        for e in experiments:
            if e.ale_id == i:
                experiment_set.get(i).add(e)
    for ale_no in sorted(experiment_set):
        table_row = "<tr>"
        lineage_name = list(experiment_set.get(ale_no)).__getitem__(0).get_isolate_name().split('_')[0];  # lineage name
        table_row += """<td><a href="summary?ale_experiment_id=%d&ale_no=%d">%s</a></td>""" % (
            ale_experiment_id, ale_no, lineage_name)
        # Need to work on this later
        table_row += "<td>%d</td>" % len(
            Flask.objects.filter(flask_number__in=dict((e.flask_number, e) for e in experiment_set.get(ale_no)),
                                 ale_id__ale_id=ale_no))
        table_row += "<td>%d</td>" % len(experiment_set.get(ale_no))
        table_row += "</tr>"
        table_body += table_row + "\n"
    template = loader.get_template("select_lineage.html")
    context = Context({"table_body": mark_safe(table_body)})
    return HttpResponse(template.render(context))

    # return HttpResponse("under construction")
