from django.http import HttpResponse
from django.template import Context, loader
from django.utils.safestring import mark_safe
from django.contrib.auth.decorators import login_required

from seq.models import *
from ale.models import *
import aleinfo.settings as settings

EXPERIMENT_LIST_TEMPLATE = "experiment_view.html"

DEFAULT_RESEQ_REPORT_URL = "http://localhost/sequencing/"

REQUEST_ALE_EXPERIMENT_ID = "ale_experiment_id"
REQUEST_ALE_NUMBER = "ale_no"
REQUEST_ALL = "all"

HTML_MUTATION_TABLE_HEADER = """<tr><td>Mutation</td><td>Gene</td><td>Protein change</td>"""
HTML_MUTATION_TABLE_ROW = """<td>%d %s<a href="javascript:void(0)" class="shut" style="float:right;display:none;" onclick="deleteRow.call(this)"><img src="/static/DataTables/media/images/close-icon.gif" width="12" height="11"></a></td>"""
CHECKBOX_HTML = """<td><input type="checkbox" class="cb" name=%s /><br>%s</td>"""

EXPERIMENT_MAPPING_FILTERING_SHOW_FLAG = "show"
EXPERIMENT_MAPPING_FILTERING_REMOVE_FLAG = "remove"

MUTATION_PRESENT_FALSE_CELL_HTML = """<td class="false">%d/%d</td>"""
MUTATION_PRESENT_TRUE_CELL_HTML = """<td class="true">%s</td>"""

EVIDENCE_DIR = "evidence/"


if hasattr(settings, "sequencing_url"):
    reseqencing_report_url = settings.sequencing_url
else:
    reseqencing_report_url = DEFAULT_RESEQ_REPORT_URL


def _get_seq_experiments(request):
    """return a list of seq experiments for a given ALE"""

    ale_experiment_selector = _get_ale_experiment_selector(request)

    ale_no_selector = _get_ale_number_selector(request)

    experiments = ResequencingExperiment.objects.raw(
        """SELECT reseq_id AS id FROM id_mapping WHERE
        reseq_id IS NOT NULL %s %s
        ORDER BY ale_no, flask_no, isolate_no ASC;""" % (ale_experiment_selector, ale_no_selector))

    return experiments


def _get_ale_experiment_selector(request):

    ale_experiment_id = request.GET.get(REQUEST_ALE_EXPERIMENT_ID)
    if ale_experiment_id is None or ale_experiment_id == REQUEST_ALL:
        ale_experiment_selector = ""
    else:
        ale_experiment_selector = "AND experiment_id = %d" % int(ale_experiment_id)

    return ale_experiment_selector


def _get_ale_number_selector(request):

    ale_no = request.GET.get(REQUEST_ALE_NUMBER)
    if ale_no is None or ale_no == REQUEST_ALL:
        ale_no_selector = ""
    else:
        ale_no_selector = "AND ale_no = %d" % int(ale_no)

    return ale_no_selector


@login_required
def index(request):
    """display a list of ales with links to the resequencing"""

    experiments = AleExperiment.objects.all()

    template = loader.get_template("index.html")

    context = Context({"experiments": experiments,
                       "seq_url": reseqencing_report_url})

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


@login_required
def mutation_table(request):

    experiment_ids = _get_experiment_id(request)

    ale_number = _get_ale_number(request)

    experiment_list = _get_experiment_list(experiment_ids)

    experiment_mapping = _get_experiment_mapping(request)

    filtered_experiment_mapping = _filter_checked_flasks(request, experiment_mapping)

    table_header = _get_table_header(filtered_experiment_mapping)

    table_body = _get_table_body(filtered_experiment_mapping, request)

    template = loader.get_template("table_template.html")

    context = Context({"experiments": experiment_list,
                       "ale_no": ale_number,
                       "experiment_id": experiment_ids,
                       "table_body": mark_safe(table_body),
                       "title": "Mutation table",
                       "table_header": mark_safe(table_header)})

    return HttpResponse(template.render(context))


@login_required
def isolate_list(request):
    ale_experiment_id = request.GET.get(REQUEST_ALE_EXPERIMENT_ID)
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


def _get_experiment_info_list(experiments):
    experiments_info_list = []

    for experiment in experiments:
        mc_list = UnassignedMissingCoverageEvidence.objects.filter(sequencing_experiment_id=experiment.id)

        mapped_read_count = int((experiment.percentage_mapped / 100) * experiment.reads)

        # Using tuple because immutable; mc_list must remain associated with particular experiment.
        experiment_info_tuple = (experiment, mc_list, mapped_read_count)

        experiments_info_list.append(experiment_info_tuple)

    return experiments_info_list


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
            _create_table_entry(observed, experiment_urls)
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


def _get_experiment_urls(experiment_mapping):

    experiment_urls = dict((i.id, reseqencing_report_url + i.location) for i in experiment_mapping.values())

    return experiment_urls


def _get_observed_mutations(experiment_mapping):

    observed_mutations = ObservedMutation.objects.filter(sequencing_experiment_id__in=experiment_mapping.keys())

    return observed_mutations


def _get_table_header(experiment_mapping):

    table_header = HTML_MUTATION_TABLE_HEADER

    experiment_urls = _get_experiment_urls(experiment_mapping)

    for checked_experiment_id in sorted(experiment_mapping):

        experiment = experiment_mapping[checked_experiment_id]

        sample_name = experiment.isolate.flask.ale_id.ale_experiment.name
        sample_name += " "
        sample_name += experiment.get_isolate_name().replace("_", " ")

        mutation_identifier = """<a href="%s">%s</a>""" % (experiment_urls[checked_experiment_id], sample_name)

        table_header += CHECKBOX_HTML % (
            experiment.id,
            mutation_identifier)

    table_header += "</tr>"

    return table_header


def _create_table_entry(observed, experiment_urls):

    if observed.breseq_present:
        table_entry = MUTATION_PRESENT_TRUE_CELL_HTML % observed.evidence.replace(EVIDENCE_DIR,
                                                                                  experiment_urls[observed.sequencing_experiment_id] + EVIDENCE_DIR)

    elif observed.present is False:
        table_entry = MUTATION_PRESENT_FALSE_CELL_HTML % (observed.mutated_reads,
                                                          observed.wt_reads)

    return table_entry


def _get_table_body(experiment_mapping, request):

    observed_mutations = _get_observed_mutations(experiment_mapping)

    # print(observed_mutations)

    mutations = Mutation.objects.filter(pk__in=observed_mutations.values_list("mutation", flat=True))
    mutation_mapping = dict((id, i) for i, id in enumerate(mutations.values_list("id", flat=True)))

    experiment_urls = _get_experiment_urls(experiment_mapping)

    experiment_mapping = dict((o, i) for i, o in enumerate(sorted(experiment_mapping.keys())))

    extra_validation = False if request.GET.get("novalid") else True

    table_entries = [["""<td class="false"></td>"""] * len(experiment_mapping) for i in range(len(mutations))]

    # Populating table_entries
    for observed_mutation in observed_mutations:

        # sometimes we do not want the extra validation
        if not extra_validation and not observed_mutation.breseq_present:
            continue

        new_entry = _create_table_entry(observed_mutation, experiment_urls)

        if new_entry is not None:
            table_entries[mutation_mapping[observed_mutation.mutation_id]][
                experiment_mapping[observed_mutation.sequencing_experiment_id]] = new_entry

    #Populating table body
    table_body = ""

    for mutation in mutations:

        table_row = "<tr>"

        if mutation.reference_error:    # TODO: what is going on here? What is 'reference_error'?
            # table_row += """<td class="reference_error">%d %s</td>""" % (mutation.position, mutation.sequence_change)
            continue

        else:
            table_row += HTML_MUTATION_TABLE_ROW % (
                mutation.position,
                mutation.sequence_change)

        table_row += "<td>%s</td>" % mutation.gene
        table_row += "<td>%s</td>" % mutation.protein_change

        observed_mutation_frequency = _get_observed_mutation_freq(observed_mutations_query_set=observed_mutations,
                                                                  mutation=mutation)

        table_row += "<td>%s</td>" % (observed_mutation_frequency * 100)

        table_row += "</tr>"

        table_body += table_row + "\n"

    return table_body


def _get_observed_mutation_freq(observed_mutations_query_set,
                                mutation):

    observed_mutation = observed_mutations_query_set.filter(mutation_id=mutation.id)

    # Should only be one ObservedMutation in QuerySet.
    # Find a way to check for this.
    observed_mutation_frequency = observed_mutation[0].frequency

    return observed_mutation_frequency


def _get_experiment_id(request):

    # Get the full list of ale experiments for the ale number of interest
    experiment_ids = request.GET.get(REQUEST_ALE_EXPERIMENT_ID)
    experiment_ids = None if experiment_ids is None or experiment_ids == "all" else int(experiment_ids)

    return experiment_ids


def _get_ale_number(request):

    ale_number = request.GET.get(REQUEST_ALE_NUMBER)
    ale_number = None if ale_number is None or ale_number == "all" else int(ale_number)

    return ale_number


def _get_experiment_list(experiment_ids):

    if experiment_ids is not None:
        experiment = AleExperiment.objects.get(ale_id=experiment_ids)
        experiment_list = experiment.aleid_set.only("ale_id")
    else:
        experiment_list = ResequencingExperiment.objects.all()

    return experiment_list


def _get_experiment_mapping(request):

    experiments = _get_seq_experiments(request)

    experiment_mapping = dict((o.id, o) for o in experiments)

    return experiment_mapping


def _show_checked_flasks(request, experiment_mapping):

    query_string = request.GET.get(EXPERIMENT_MAPPING_FILTERING_SHOW_FLAG)
    if query_string is not None:
        checked_experiment_ids = query_string.encode('latin_1').replace("{", "").replace("}", "")
        if checked_experiment_ids != "":
            checked_experiment_id_list = [int(i) for i in checked_experiment_ids.split(",") if i != ""]
            checked_experiment_ids = experiment_mapping.keys()
            for checked_experiment_id in checked_experiment_ids:
                if checked_experiment_id not in checked_experiment_id_list:
                    del experiment_mapping[checked_experiment_id]

    return experiment_mapping


def _remove_checked_flasks(request, experiment_mapping):

    query_string = request.GET.get(EXPERIMENT_MAPPING_FILTERING_REMOVE_FLAG)
    if query_string is not None:
        checked_experiment_ids = query_string.encode('latin_1').replace("{", "").replace("}", "")
        if checked_experiment_ids != "":
            for checked_experiment_id in checked_experiment_ids.split(","):
                if checked_experiment_id != "":
                    del experiment_mapping[int(checked_experiment_id)]

    return experiment_mapping


def _filter_checked_flasks(request, experiment_mapping):

    experiment_mapping = _show_checked_flasks(request, experiment_mapping)

    experiment_mapping = _remove_checked_flasks(request, experiment_mapping)

    return experiment_mapping


# Provide a table showing frequencies of each observed mutation in the lineage
def lineage_table(request):
    experiments = _get_seq_experiments(request)
    ale_experiment_id = int(request.GET.get(REQUEST_ALE_EXPERIMENT_ID))
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
