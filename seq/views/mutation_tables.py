import collections

from django.http import HttpResponse

from django.contrib.auth.decorators import login_required

from django.template import Context, loader

from django.utils.safestring import mark_safe

from ale.models import *    # TODO: only import necessary models.
from seq.models import *    # TODO: only import necessary models.

import aleinfo.settings as settings

from seq.views import common


HTML_MUTATION_TABLE_ROW = """<td>%d %s<a href="javascript:void(0)" class="shut" style="float:right;display:none;" onclick="deleteRow.call(this)"><img src="/static/DataTables/media/images/close-icon.gif" width="12" height="11"></a></td>"""
HTML_MUTATION_TABLE_HEADER = """<tr><td>Mutation</td><td>Gene</td><td>Protein change</td>"""
HTML_MUTATION_TABLE_EXPERIMENT_HEADER = """<a href="%s">%s</a>"""
HTML_CHECKBOX = """<td><input type="checkbox" class="cb" name=%s /><br>%s</td>"""
HTML_EMPTY_MUTATION_CELL = """<td class="false"></td>"""

EXPERIMENT_MAPPING_FILTERING_SHOW_FLAG = "show"
EXPERIMENT_MAPPING_FILTERING_REMOVE_FLAG = "remove"


if hasattr(settings, common.SETTINGS_SEQUENCING_URL):
    reseqencing_report_url = settings.sequencing_url
else:
    reseqencing_report_url = common.DEFAULT_RESEQ_REPORT_URL


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


def _get_experiment_id(request):

    # Get the full list of ale experiments for the ale number of interest
    experiment_ids = request.GET.get(common.REQUEST_ALE_EXPERIMENT_ID)
    experiment_ids = None if experiment_ids is None or experiment_ids == "all" else int(experiment_ids)

    return experiment_ids


def _get_ale_number(request):

    ale_number = request.GET.get(common.REQUEST_ALE_NUMBER)
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

    seq_experiments = common.get_seq_experiments(request)

    experiment_mapping = collections.OrderedDict((seq_experiment.id, seq_experiment) for seq_experiment in seq_experiments)

    return experiment_mapping


def _filter_checked_flasks(request, experiment_mapping):

    experiment_mapping = _show_checked_flasks(request, experiment_mapping)

    experiment_mapping = _remove_checked_flasks(request, experiment_mapping)

    return experiment_mapping


def _get_table_header(experiment_mapping):

    table_header = HTML_MUTATION_TABLE_HEADER

    experiment_urls = _get_experiment_urls(experiment_mapping)

    for checked_experiment_id in experiment_mapping:

        experiment = experiment_mapping[checked_experiment_id]

        sample_name = _get_sample_name(experiment)

        mutation_identifier = HTML_MUTATION_TABLE_EXPERIMENT_HEADER % (experiment_urls[checked_experiment_id],
                                                                       sample_name)

        table_header += HTML_CHECKBOX % (
            experiment.id,
            mutation_identifier)

    table_header += "</tr>"

    return table_header


def _get_sample_name(experiment):

    sample_name = experiment.isolate.flask.ale_id.ale_experiment.name
    sample_name += " "
    sample_name += experiment.get_isolate_name().replace("_", " ")

    return sample_name


def _get_experiment_id_idx_mapping(experiment_mapping):

    experiment_id_idx_mapping = dict((reseq_exp_id, idx) for idx, reseq_exp_id in enumerate(experiment_mapping.keys()))

    return experiment_id_idx_mapping


def _get_table_body(experiment_mapping, request):

    observed_mutations = _get_observed_mutations(experiment_mapping)

    mutations = Mutation.objects.filter(pk__in=observed_mutations.values_list("mutation", flat=True))
    mutation_mapping = dict((id, i) for i, id in enumerate(mutations.values_list("id", flat=True)))

    experiment_urls = _get_experiment_urls(experiment_mapping)

    experiment_id_idx_mapping = _get_experiment_id_idx_mapping(experiment_mapping)

    # TODO: figure out what this is.
    extra_validation = False if request.GET.get("novalid") else True

    # Initialize all sample mutation table cells as empty.
    table_entries = [[HTML_EMPTY_MUTATION_CELL] * len(experiment_id_idx_mapping) for idx in range(len(mutations))]

    # Populating table_entries
    for observed_mutation in observed_mutations:

        # TODO: figure out what this is.
        # sometimes we do not want the extra validation
        if not extra_validation and not observed_mutation.breseq_present:
            continue

        new_entry = common.get_table_mutation_entry(observed_mutation, experiment_urls)

        if new_entry is not None:
            table_entries[mutation_mapping[observed_mutation.mutation_id]][experiment_id_idx_mapping[observed_mutation.sequencing_experiment_id]] = new_entry

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
        table_row += "".join(table_entries[mutation_mapping[mutation.id]])
        table_row += "</tr>"

        table_body += table_row + "\n"

    return table_body


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


def _get_experiment_urls(experiment_mapping):

    experiment_urls = dict((i.id, reseqencing_report_url + i.location) for i in experiment_mapping.values())

    return experiment_urls


def _get_observed_mutations(experiment_mapping):

    observed_mutations = ObservedMutation.objects.filter(sequencing_experiment_id__in=experiment_mapping.keys())

    return observed_mutations
