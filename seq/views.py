from django.http import HttpResponse
from django.template import Context, loader
from django.utils.safestring import mark_safe
from django.contrib.auth.decorators import login_required

from seq.models import *
from ale.models import *
import aleinfo.settings as settings

EXPERIMENT_LIST_TEMPLATE = "experiment_view.html"

DEFAULT_RESEQ_REPORT_URL = "http://localhost/sequencing/"

if hasattr(settings, "sequencing_url"):
    reseqencing_report_url = settings.sequencing_url
else:
    reseqencing_report_url = DEFAULT_RESEQ_REPORT_URL


def _get_seq_experiments(request):
    """return a list of seq experiments for a given ALE"""

    ale_experiment_id = request.GET.get("ale_experiment_id")

    if ale_experiment_id is None or ale_experiment_id == "all":

        ale_experiment_selector = ""

    else:

        ale_experiment_selector = "AND experiment_id = %d" % int(ale_experiment_id)

    ale_no = request.GET.get("ale_no")

    if ale_no is None or ale_no == "all":

        ale_no_selector = ""

    else:

        ale_no_selector = "AND alexperimentse_no = %d" % int(ale_no)

    experiments = ResequencingExperiment.objects.raw(
        """SELECT reseq_id AS id FROM id_mapping WHERE
        reseq_id IS NOT NULL %s %s
        ORDER BY ale_no, flask_no, isolate_no ASC;""" % (ale_experiment_selector, ale_no_selector))

    return experiments


@login_required
def index(request):
    """display a list of ales with links to the resequencing"""

    experiments = AleExperiment.objects.all()

    template = loader.get_template("index.html")

    context = Context({"experiments": experiments, "seq_url": reseqencing_report_url})

    return HttpResponse(template.render(context))


@login_required
def lists(request):
    """return a list of resequencing experiments"""

    experiments = _get_seq_experiments(request)

    # Would rather want to use something like a dictionary since an experiment is
    # unique, though an experiment is currently a structure and an integral type
    # that can be used as a key.

    experiments_info_list = _get_experiment_info_list(experiments)

    template = loader.get_template(EXPERIMENT_LIST_TEMPLATE)

    context = Context({"experiments_info_list": experiments_info_list,
                       "resequencing_report_url": reseqencing_report_url})

    return HttpResponse(template.render(context))


def _get_experiment_info_list(experiments):
    experiments_info_list = []

    for experiment in experiments:
        mc_list = UnassignedMissingCoverageEvidence.objects.filter(sequencing_experiment_id=experiment.id)

        mapped_read_count = int((experiment.percentage_mapped / 100) * experiment.reads)

        # Using tuple because immutable; mc_list must remain associated with particular experiment.
        experiment_info_tuple = (experiment, mc_list, mapped_read_count)

        experiments_info_list.append(experiment_info_tuple)

    return experiments_info_list


def make_table_entry(observed, experiment_urls):
    if observed.breseq_present:

        return """<td class="true">%s</td>""" % observed.evidence.replace("evidence/",
                                                                          experiment_urls[
                                                                              observed.sequencing_experiment_id] + "/evidence/")

    elif observed.present is False:

        return """<td class="false">%d/%d</td>""" % (observed.mutated_reads,
                                                     observed.wt_reads)


@login_required
def experiment_table(request):
    experiments = _get_seq_experiments(request)
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
            make_table_entry(observed, experiment_urls)
    table_header = """<tr><td>Experiment</td>"""
    for mutation in mutations:
        if mutation.reference_error:
            table_header += """<td class="reference_error">%d %s</td>""" % (mutation.position, mutation.sequence_change)
        else:
            table_header += """<td>%d %s</td>""" % (mutation.position, mutation.sequence_change)
    table_header += "</tr>"
    table_body = ""
    for experiment in experiments:
        table_body += """<tr><td><a href="%s">%s</a></td>""" % (
        reseqencing_report_url + experiment.location, experiment.get_isolate_name())
        for column in table_entries[experiment_mapping[experiment.id]]:
            if column is None:
                table_body += """<td class="false"></td>"""
            else:
                table_body += column
    template = loader.get_template("table_template.html")
    context = Context(
        {"table_body": mark_safe(table_body), "title": "Experiment table", "table_header": mark_safe(table_header)})
    return HttpResponse(template.render(context))


@login_required
def mutation_table(request):
    experiments = _get_seq_experiments(request)

    # Get the full list of ale experiments for the ale number of interest
    experiment_id = request.GET.get("ale_experiment_id")
    print(experiment_id)

    experiment_id = None if experiment_id is None or experiment_id == "all" else int(experiment_id)
    print(experiment_id)

    ale_no = request.GET.get("ale_no")
    print(ale_no)

    ale_no = None if ale_no is None or ale_no == "all" else int(ale_no)
    print(ale_no)

    if experiment_id is not None:
        experiment = AleExperiment.objects.get(ale_id=experiment_id)
        list_of_experiments = experiment.aleid_set.only("ale_id")
    else:
        list_of_experiments = ResequencingExperiment.objects.all()

    print(list_of_experiments)

    extra_validation = False if request.GET.get("novalid") else True
    print(extra_validation)

    # experiment_mapping = dict((o.id, o) for i, o in enumerate(experiments) if o.isolate.__unicode__().find("POP")==-1)
    experiment_mapping = dict((o.id, o) for o in experiments)
    # print(experiment_mapping)

    # Show checked flasks only
    query_string = request.GET.get("show")
    if query_string is not None:
        checked_experiment_ids = query_string.encode('latin_1').replace("{", "").replace("}", "")
        if checked_experiment_ids != "":
            checked_experiment_id_list = [int(i) for i in checked_experiment_ids.split(",") if i != ""]
            checked_experiment_ids = experiment_mapping.keys()
            for checked_experiment_id in checked_experiment_ids:
                if checked_experiment_id not in checked_experiment_id_list:
                    del experiment_mapping[checked_experiment_id]

    # Remove checked flasks
    query_string = request.GET.get("remove")
    if query_string is not None:
        checked_experiment_ids = query_string.encode('latin_1').replace("{", "").replace("}", "")
        if checked_experiment_ids != "":
            for checked_experiment_id in checked_experiment_ids.split(","):
                if checked_experiment_id != "":
                    del experiment_mapping[int(checked_experiment_id)]

    # cache the urls of the experiment location
    experiment_urls = dict((i.id, reseqencing_report_url + i.location) for i in experiment_mapping.values())
    observed_mutations = ObservedMutation.objects.filter(sequencing_experiment_id__in=experiment_mapping.keys())
    mutations = Mutation.objects.filter(pk__in=observed_mutations.values_list("mutation", flat=True))
    mutation_mapping = dict((id, i) for i, id in enumerate(mutations.values_list("id", flat=True)))
    table_header = """<tr><td>Mutation</td><td>Gene</td><td>Protein change</td>"""

    for checked_experiment_id in sorted(experiment_mapping):
        experiment = experiment_mapping[checked_experiment_id]
        # Add checkbox to each column
        table_header += """<td><input type="checkbox" class="cb" name=%s /><br>%s</td>""" % (
        experiment.id, experiment.get_isolate_name().replace("_", " "))
    table_header += "</tr>"
    table_entries = [["""<td class="false"></td>"""] * len(experiment_mapping) for i in range(len(mutations))]

    experiment_mapping = dict((o, i) for i, o in enumerate(sorted(experiment_mapping.keys())))

    for observed in observed_mutations:
        # sometimes we do not want the extra validation
        if not extra_validation and not observed.breseq_present:
            continue
        new_entry = make_table_entry(observed, experiment_urls)
        if new_entry is not None:
            table_entries[mutation_mapping[observed.mutation_id]][
                experiment_mapping[observed.sequencing_experiment_id]] = new_entry
    table_body = ""
    for mutation in mutations:
        table_row = "<tr>"
        if mutation.reference_error:
            # table_row += """<td class="reference_error">%d %s</td>""" % (mutation.position, mutation.sequence_change)
            continue
        else:
            table_row += """<td>%d %s<a href="javascript:void(0)" class="shut" style="float:right;display:none;" onclick="deleteRow.call(this)"><img src="/static/DataTables/media/images/close-icon.gif" width="12" height="11"></a></td>""" % (
            mutation.position, mutation.sequence_change)
        table_row += "<td>%s</td>" % (mutation.gene)
        table_row += "<td>%s</td>" % (mutation.protein_change)
        table_row += "".join(table_entries[mutation_mapping[mutation.id]])
        table_row += "</tr>"
        table_body += table_row + "\n"

    template = loader.get_template("table_template.html")
    context = Context({"experiments": list_of_experiments,
                       "ale_no": ale_no,
                       "experiment_id": experiment_id,
                       "table_body": mark_safe(table_body),
                       "title": "Mutation table",
                       "table_header": mark_safe(table_header)})

    return HttpResponse(template.render(context))


@login_required
def isolate_list(request):
    ale_experiment_id = request.GET.get("ale_experiment_id")
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


# Provide a table showing frequencies of each observed mutation in the lineage
def lineage_table(request):
    experiments = _get_seq_experiments(request)
    ale_experiment_id = int(request.GET.get("ale_experiment_id"))
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
    experiments = _get_seq_experiments(request)
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
        replaced += "<p>%d %s: repalced by %d %s<br></p>" % (
        m.position, m.sequence_change, r.position, r.sequence_change)

    template = loader.get_template("summary.html")
    context = Context({"present_in_all": mark_safe(present_in_all),
                       "present_in_multiple": mark_safe(present_in_multiple),
                       "present_in_one": mark_safe(present_in_one),
                       "reappeared": mark_safe(reappeared),
                       "replaced": mark_safe(replaced),
                       })
    return HttpResponse(template.render(context))
