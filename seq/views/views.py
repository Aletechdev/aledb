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


# Provide a table showing frequencies of each observed mutation in the lineage
def lineage_table(request):
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
    template = loader.get_template("lineage.html")
    context = Context({"table_body": mark_safe(table_body)})
    return HttpResponse(template.render(context))


def mutation_summary(request):
    experiments = common.get_seq_experiments(request)
    experiments_no_pop = [e for e in experiments if e.isolate.__unicode__().find("POP") == -1]
    experiment_set = dict((i, set(Mutation.objects.filter(
        pk__in=ObservedMutation.objects.filter(sequencing_experiment_id=e.id).values_list("mutation", flat=True)))) for
                          i, e in enumerate(experiments_no_pop))
    muts = set()
    for s in experiment_set.values():
        muts = muts | s

    # Generates a binary matrix whose rows are mutations,
    # columns are experiments, and values are either 1 or 0
    # depending on whether the mutation present in the experiment
    matrix = dict((m, [int(m in l) for l in experiment_set.values()]) for m in muts)

    # Mutation categories
    mut_seen_in_all = list()
    mut_seen_in_multiple = list()
    mut_seen_in_one = list()
    mut_reappeared = list()
    mut_replaced = dict()

    # An algorithm that checks if a mutation is replaced by a different
    # mutation in the same gene
    def replaced(mutation):
        replaced = False
        s = matrix.get(mutation)
        ind = s.index(1)
        for m in muts:
            if ind < matrix.get(m).index(1):
                replaced = True
                mut_replaced[mutation] = m
                break
        return replaced

    # Classify all mutations into the five categories
    for m in muts:
        s = matrix.get(m)
        if sum(s) == len(s):
            mut_seen_in_all.append(m)
        elif sum(s) > 1 & sum(s) < len(s):
            s_str = ''
            for i in s:
                s_str += str(i)
            if s_str.find('11') != -1:
                mut_seen_in_multiple.append(m)
            else:
                mut_reappeared.append(m)
        elif sum(s) == 1:
            if not replaced(m):
                mut_seen_in_one.append(m)

    # HTML display
    present_in_all = ""
    for m in mut_seen_in_all:
        if m.reference_error:
            present_in_all += """<p class="reference_error">%d %s<br></p>""" % (m.position, m.sequence_change)
        else:
            present_in_all += "<p>%d %s<br></p>" % (m.position, m.sequence_change)
    present_in_multiple = ""
    for m in mut_seen_in_multiple:
        present_in_multiple += "<p>%d %s<br></p>" % (m.position, m.sequence_change)
    present_in_one = ""
    for m in mut_seen_in_one:
        present_in_one += "<p>%d %s<br></p>" % (m.position, m.sequence_change)
    reappeared = ""
    for m in mut_reappeared:
        reappeared += "<p>%d %s<br></p>" % (m.position, m.sequence_change)
    replaced = ""
    for m, r in zip(mut_replaced.keys(), mut_replaced.values()):
        replaced += "<p>%d %s: replaced by %d %s<br></p>" % (
        m.position, m.sequence_change, r.position, r.sequence_change)

    template = loader.get_template("summary.html")
    context = Context({"present_in_all": mark_safe(present_in_all),
                       "present_in_multiple": mark_safe(present_in_multiple),
                       "present_in_one": mark_safe(present_in_one),
                       "reappeared": mark_safe(reappeared),
                       "replaced": mark_safe(replaced),
                       })
    return HttpResponse(template.render(context))
