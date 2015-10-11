from django.http import HttpResponse

from django.contrib.auth.decorators import login_required

from django.template import Context, loader

from django.utils.safestring import mark_safe

from ale.models import AleExperiment
from ale.models import KeyMutation

from seq.models import ResequencingExperiment
from seq.models import Mutation
from seq.models import ObservedMutation

import aleinfo.settings as settings

from seq.views import common

from builder.key_mutations import get_key_mutations


__author__ = 'pphaneuf'


HTML_MUTATION_TABLE_ROW = """<td>%d %s<a href="javascript:void(0)" class="shut" style="float:right;display:none;" onclick="deleteRow.call(this)"><img src="/static/DataTables/media/images/close-icon.gif" width="12" height="11"></a></td>"""
HTML_MUTATION_TABLE_HEADER = """<tr><td>Mutation</td><td>Gene</td><td>Protein change</td>"""
HTML_MUTATION_TABLE_EXPERIMENT_HEADER = """<a href="%s">%s</a>"""
HTML_CHECKBOX = """<td><input type="checkbox" class="cb" name=%s /><br>%s</td>"""
HTML_EMPTY_MUTATION_CELL = """<td class="false"></td>"""

EXPERIMENT_MAPPING_FILTERING_SHOW_FLAG = "show"
EXPERIMENT_MAPPING_FILTERING_REMOVE_FLAG = "remove"

# TODO: this constant also defined in builder/key_mutations. Needs to be defined once and accessible by all apps.
STARTING_STRAIN_ALE_ID = 0


# TODO: this implementation shares much with mutations.py; refactored shared implementations into common.py

@login_required
def key_mutations(request):

    ale_experiment_id = common.get_ale_experiment_id(request)

    ale_number = _get_ale_number(request)

    seq_experiment_queryset = _get_seq_experiment_queryset(ale_experiment_id)

    seq_experiment_ordered_dict = common.get_experiment_ordered_dict(request)

    seq_experiment_ordered_dict = _filter_out_starting_strain_seq_experiment(seq_experiment_ordered_dict)

    seq_experiment_ordered_dict = common.filter_checked_flasks(request, seq_experiment_ordered_dict)

    table_header = _get_table_header(seq_experiment_ordered_dict)

    table_body = _get_table_body(seq_experiment_ordered_dict, request)

    template = loader.get_template("table_template.html")

    context = Context({"experiments": seq_experiment_queryset,
                       "ale_no": ale_number,
                       "experiment_id": ale_experiment_id,
                       "table_body": mark_safe(table_body),
                       "title": "Mutation table",
                       "table_header": mark_safe(table_header)})

    return HttpResponse(template.render(context))


def _filter_out_starting_strain_seq_experiment(seq_experiment_ordered_dict):

    key_to_delete_found = False

    for key, value in seq_experiment_ordered_dict.iteritems():

        if value.ale_id == STARTING_STRAIN_ALE_ID:

            key_to_delete = key

            key_to_delete_found = True

    if key_to_delete_found:

        del seq_experiment_ordered_dict[key_to_delete]

    return seq_experiment_ordered_dict


def _get_ale_number(request):

    ale_number = request.GET.get(common.REQUEST_ALE_NUMBER)
    ale_number = None if ale_number is None or ale_number == "all" else int(ale_number)

    return ale_number


def _get_seq_experiment_queryset(ale_experiment_id):

    if ale_experiment_id is not None:

        experiment = AleExperiment.objects.get(ale_id=ale_experiment_id)

        experiment_queryset = experiment.aleid_set.only("ale_id")

    else:

        experiment_queryset = ResequencingExperiment.objects.all()

    filtered_experiment_queryset = experiment_queryset.exclude(ale_id=STARTING_STRAIN_ALE_ID)

    return filtered_experiment_queryset


def _get_table_header(seq_experiment_dict):

    table_header = HTML_MUTATION_TABLE_HEADER

    experiment_urls = common.get_experiment_urls(seq_experiment_dict)

    for seq_experiment_id in seq_experiment_dict:

        seq_experiment = seq_experiment_dict[seq_experiment_id]

        sample_name = common.get_sample_name(seq_experiment)

        mutation_identifier = HTML_MUTATION_TABLE_EXPERIMENT_HEADER % (experiment_urls[seq_experiment_id],
                                                                       sample_name)

        table_header += HTML_CHECKBOX % (
            seq_experiment.id,
            mutation_identifier)

    table_header += "</tr>"

    return table_header


def _get_experiment_id_idx_mapping(seq_experiment_dict):

    experiment_id_idx_mapping = dict((reseq_exp_id, idx) for idx, reseq_exp_id in enumerate(seq_experiment_dict.keys()))

    return experiment_id_idx_mapping


def _get_table_body(seq_experiment_dict, request):

    ale_experiment_id = common.get_ale_experiment_id(request)
    key_mutation_queryset = KeyMutation.objects.filter(ale_experiment_id=ale_experiment_id)

    observed_mutations_query_set = _get_observed_key_mutations(seq_experiment_dict, key_mutation_queryset)

    mutations = Mutation.objects.filter(pk__in=observed_mutations_query_set.values_list("mutation", flat=True))
    mutation_dict = dict((id, i) for i, id in enumerate(mutations.values_list("id", flat=True)))

    experiment_urls = common.get_experiment_urls(seq_experiment_dict)

    experiment_id_idx_mapping = _get_experiment_id_idx_mapping(seq_experiment_dict)

    # TODO: figure out what this is.
    extra_validation = False if request.GET.get("novalid") else True

    # Initialize all sample mutation table cells as empty.
    table_entries = [[HTML_EMPTY_MUTATION_CELL] * len(experiment_id_idx_mapping) for idx in range(len(mutations))]

    # Populating table_entries
    for observed_mutation in observed_mutations_query_set:

        # TODO: figure out what this is.
        # sometimes we do not want the extra validation
        if not extra_validation and not observed_mutation.breseq_present:
            continue

        new_entry = common.get_table_mutation_entry(observed_mutation, experiment_urls)

        if new_entry is not None:
            table_entries[mutation_dict[observed_mutation.mutation_id]][experiment_id_idx_mapping[observed_mutation.sequencing_experiment_id]] = new_entry

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
        table_row += "".join(table_entries[mutation_dict[mutation.id]])
        table_row += "</tr>"

        table_body += table_row + "\n"

    return table_body


def _show_checked_flasks(request, seq_experiment_dict):

    query_string = request.GET.get(EXPERIMENT_MAPPING_FILTERING_SHOW_FLAG)
    if query_string is not None:
        checked_experiment_ids = query_string.encode('latin_1').replace("{", "").replace("}", "")
        if checked_experiment_ids != "":
            checked_experiment_id_list = [int(i) for i in checked_experiment_ids.split(",") if i != ""]
            checked_experiment_ids = seq_experiment_dict.keys()
            for checked_experiment_id in checked_experiment_ids:
                if checked_experiment_id not in checked_experiment_id_list:
                    del seq_experiment_dict[checked_experiment_id]

    return seq_experiment_dict


def _remove_checked_flasks(request, seq_experiment_dict):

    query_string = request.GET.get(EXPERIMENT_MAPPING_FILTERING_REMOVE_FLAG)
    if query_string is not None:
        checked_experiment_ids = query_string.encode('latin_1').replace("{", "").replace("}", "")
        if checked_experiment_ids != "":
            for checked_experiment_id in checked_experiment_ids.split(","):
                if checked_experiment_id != "":
                    del seq_experiment_dict[int(checked_experiment_id)]

    return seq_experiment_dict


def _get_observed_key_mutations(seq_experiment_dict, key_mutation_queryset):

    # 2 filters for the queryset:
    # 1) get observed_mutations that are contained within the seq_experiment_dict,
    # 2) get observed_mutations that reference to the key_mutation_queryset
    # TODO: refactor

    seq_experiment_observed_mutation_queryset = ObservedMutation.objects.filter(sequencing_experiment_id__in=seq_experiment_dict.keys())

    key_mutation_id_list = []

    for key_mutation in key_mutation_queryset:

        key_mutation_id_list.append(key_mutation.mutation_id)

    key_mutation_observed_mutation_queryset = seq_experiment_observed_mutation_queryset.filter(mutation_id__in=key_mutation_id_list)

    return key_mutation_observed_mutation_queryset
