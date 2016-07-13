import seq.models

import aleinfo.settings

import os

import seq.views.common

import json

import re

from enum import Enum


EXPERIMENT_MAPPING_FILTERING_SHOW_FLAG = "show"

EXPERIMENT_MAPPING_FILTERING_REMOVE_FLAG = "remove"

HTML_MUTATION_TABLE_ROW = """<td><a href="javascript:void(0)" style="float:right" onclick="deleteRow.call(this)"><img src="/static/DataTables/media/images/close-icon.gif" width="12" height="11"></a></td>"""

HTML_MUTATION_TABLE_HEADER = """<tr><td></td><td>Position</td><td>Mutation Type</td><td>Sequence Change</td><td>Gene</td><td>Protein change</td>"""

HTML_MUTATION_TABLE_EXPERIMENT_HEADER = """<a href="%s">%s</a>"""

HTML_CHECKBOX = """<td><input type="checkbox" class="cb" name=%s /><br>%s</td>"""

HTML_EMPTY_MUTATION_CELL = """<td id="empty"></td>"""

HTML_MUTATION_PRESENT_FALSE_CELL_HTML = """<td class="false">%d/%d</td>"""

HTML_MUTATION_PRESENT_TRUE_CELL_HTML = """<td id="true"><a href="%s">%.2f</a></td>"""

non_decimal = re.compile(r'[^\d.]+')


if hasattr(aleinfo.settings, seq.views.common.SETTINGS_SEQUENCING_URL):
    reseqencing_report_url = aleinfo.settings.sequencing_url
else:
    reseqencing_report_url = seq.views.common.DEFAULT_RESEQ_REPORT_URL


def get_table_header(reseq_dict):

    table_header = HTML_MUTATION_TABLE_HEADER

    experiment_urls = _get_experiment_urls(reseq_dict)

    for seq_experiment_id in reseq_dict:

        seq_experiment = reseq_dict[seq_experiment_id]

        sample_name = seq.views.common.get_sample_name(seq_experiment)

        mutation_identifier = HTML_MUTATION_TABLE_EXPERIMENT_HEADER % (experiment_urls[seq_experiment_id],
                                                                       sample_name)

        table_header += HTML_CHECKBOX % (
            seq_experiment.id,
            mutation_identifier)

    table_header += "</tr>"

    return table_header


# TODO: Refactor. The observed mutations argument may
# reference to a seq_experiment that doesn't exist due to checkbox filtering.
# This makes this function very confusing.
def get_table_body(reseq_dict,
                   observed_mutations_queryset,
                   filter_settings=None,
                   filter_mutation_id_list=None,
                   table_type=None):

    mutation_queryset = seq.views.common.get_mutation_queryset_from_observed_mutation_queryset(observed_mutations_queryset)

    mutation_index_dict = dict((id, i) for i, id in enumerate(mutation_queryset.values_list("id", flat=True)))

    experiment_url_dict = _get_experiment_urls(reseq_dict)

    experiment_id_idx_mapping_dict = _get_experiment_id_idx_mapping_dict(reseq_dict)

    # Initialize all sample mutation table cells as empty.
    table_entry_list = _initialize_table(experiment_id_idx_mapping_dict, mutation_queryset)

    # Populating table_entry_list
    for observed_mutation in observed_mutations_queryset:

        if filter_mutation_id_list is not None and observed_mutation.mutation.id in filter_mutation_id_list:
            continue

        if not _filter_mutation(filter_settings, observed_mutation):

            new_entry = _get_table_mutation_entry(observed_mutation, experiment_url_dict)

            if new_entry is not None and observed_mutation.sequencing_experiment_id in reseq_dict.keys():
                table_entry_list[mutation_index_dict[observed_mutation.mutation_id]][experiment_id_idx_mapping_dict[observed_mutation.sequencing_experiment_id]] = new_entry

    #Populating table body
    table_body = ""

    for mutation in mutation_queryset:

        if _contains_mutation(table_entry_list[mutation_index_dict[mutation.id]]):

            table_row = "<tr>"

            if mutation.reference_error:    # TODO: what is going on here? What is 'reference_error'?
                # table_row += """<td class="reference_error">%d %s</td>""" % (mutation.position, mutation.sequence_change)
                continue

            else:
                table_row += HTML_MUTATION_TABLE_ROW

            table_row += "<td>%s</td>" % mutation.position
            table_row += "<td>%s</td>" % mutation.mutation_type
            table_row += "<td>%s</td>" % mutation.sequence_change
            table_row += "<td><a href=/ale_analytics/gene?g=%s>%s</a></td>" % (mutation.gene, mutation.gene)
            if table_type is TableType.gene_table:
                try:
                    table_row += "<td><a onclick=\"zoomTo(%d)\">%s</a></td>" \
                                 % (int(non_decimal.sub('', mutation.protein_change)), mutation.protein_change)
                except:
                    table_row += "<td>%s</td>" % mutation.protein_change
            else:
                table_row += "<td>%s</td>" % mutation.protein_change
            table_row += "".join(table_entry_list[mutation_index_dict[mutation.id]])
            table_row += "</tr>"

            table_body += table_row + "\n"

    return table_body


def _initialize_table(experiment_id_idx_mapping, mutations):
    return [[HTML_EMPTY_MUTATION_CELL] * len(experiment_id_idx_mapping) for _ in range(len(mutations))]


def _get_experiment_urls(seq_experiment_dict):

    experiment_urls = dict((i.id, reseqencing_report_url + i.location) for i in seq_experiment_dict.values())

    return experiment_urls


def _get_experiment_id_idx_mapping_dict(seq_experiment_dict):

    experiment_id_idx_mapping = dict((reseq_exp_id, idx) for idx, reseq_exp_id in enumerate(seq_experiment_dict.keys()))

    return experiment_id_idx_mapping


def _filter_mutation(filter_settings, observed_mutation):

    filter_mutation = _is_filter_on_gene(filter_settings, observed_mutation) \
                      or _is_filter_on_freq(filter_settings, observed_mutation) \
                      or _is_filter_on_mutation(filter_settings, observed_mutation)

    return filter_mutation


def _is_filter_on_mutation(filter_settings, observed_mutation):

    is_filter_on_mutation = False

    if filter_settings is not None:

        if filter_settings.ignored_mutations != "":

            filter_mutation_list = json.loads(filter_settings.ignored_mutations)

            for filter_mutation in filter_mutation_list:

                if observed_mutation.mutation.position == filter_mutation["position"] and observed_mutation.mutation.sequence_change == filter_mutation["sequence"] and observed_mutation.mutation.mutation_type == filter_mutation["type"]:
                    is_filter_on_mutation = True
                    break

    return is_filter_on_mutation


def _is_filter_on_gene(filter_settings, observed_mutation):
    is_filter_on_gene = False

    if filter_settings is not None:

        filtered_gene_list = filter_settings.ignored_genes.replace(" ", "").split(',')

        if observed_mutation.mutation.gene in filtered_gene_list:
            is_filter_on_gene = True

    return is_filter_on_gene


def _is_filter_on_freq(filter_settings, observed_mutation):
    is_filter_on_freq = True

    # Creating up defaults.
    if filter_settings is not None:
        minimum_mutation_frequency = float(filter_settings.min_cutoff) / 100
        maximum_mutation_frequency = float(filter_settings.max_cutoff) / 100
    else:
        minimum_mutation_frequency = 0.0
        maximum_mutation_frequency = 1.0

    if minimum_mutation_frequency <= observed_mutation.frequency <= maximum_mutation_frequency:
        is_filter_on_freq = False

    return is_filter_on_freq


def _get_table_mutation_entry(observed_mutation, experiment_url_dict):

    table_entry = ""

    if observed_mutation.breseq_present and observed_mutation.sequencing_experiment_id in experiment_url_dict:

        url = experiment_url_dict[observed_mutation.sequencing_experiment_id]

        if observed_mutation.mutation.mutation_type == "DUP":

            base_name = os.path.basename(os.path.dirname(os.path.dirname(url)))

            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(url)))

            dup_url = base_dir + "/dups/" + base_name + "/" + base_name + ".html"

            table_entry = HTML_MUTATION_PRESENT_TRUE_CELL_HTML % (dup_url, float(observed_mutation.frequency))

        else:
            evidence_url = url + _find_between(observed_mutation.evidence, "\"", "\"")
            table_entry = HTML_MUTATION_PRESENT_TRUE_CELL_HTML % (evidence_url, float(observed_mutation.frequency))

    # TODO: Figure out what this is supposed to do.
    elif observed_mutation.present is False:

        table_entry = HTML_MUTATION_PRESENT_FALSE_CELL_HTML % (observed_mutation.mutated_reads,
                                                               observed_mutation.wt_reads)

    return table_entry


def _contains_mutation(filtered_observed_mutations_row):

    contains_mutation = False

    for observed_mutation_entry in filtered_observed_mutations_row:
        if "true" in observed_mutation_entry:
            contains_mutation = True

    return contains_mutation


def _find_between(s, first, last):
    try:
        start = s.index(first) + len(first)
        end = s.index(last, start)
        return s[start:end]
    except ValueError:
        return ""


def filter_checked_flasks(request, seq_experiment_dict):

    seq_experiment_dict = _show_checked_flasks(request, seq_experiment_dict)

    seq_experiment_dict = _remove_checked_flasks(request, seq_experiment_dict)

    return seq_experiment_dict


def _show_checked_flasks(request, seq_experiment_dict):

    query_string = request.GET.get(EXPERIMENT_MAPPING_FILTERING_SHOW_FLAG)

    if query_string is not None:

        checked_experiment_ids = str(query_string).replace("{", "").replace("}", "")

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

        checked_experiment_ids = str(query_string).replace("{", "").replace("}", "")

        if checked_experiment_ids != "":

            for checked_experiment_id in checked_experiment_ids.split(","):

                if checked_experiment_id != "":

                    del seq_experiment_dict[int(checked_experiment_id)]

    return seq_experiment_dict


class TableType(Enum):
    gene_table = 1
