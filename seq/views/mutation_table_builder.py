import aleinfo.settings

import os

import seq.views.common

from filter.util import filter_mutations

import re

from enum import Enum

from django.utils.html import strip_tags

from common.db_util import get_mutation_queryset_from_obs_mut_queryset

from genes.util import get_gene_list

from common.constants import TAGS


EXPERIMENT_MAPPING_FILTERING_SHOW_FLAG = "show"

EXPERIMENT_MAPPING_FILTERING_REMOVE_FLAG = "remove"

HTML_MUTATION_TABLE_ROW = """<a href="javascript:void(0)" style="float:right" onclick="deleteRow.call(this)"><img src="/static/close-icon.gif" width="12" height="11"></a>"""

HTML_MUTATION_TABLE_HEADER = ["", "", "Tags", "Position", "Mutation Type", "Sequence Change", "Gene", "Function", "Product", "GO Process", "GO Component", "Protein change"]

HTML_MUTATION_TABLE_EXPERIMENT_HEADER = """<a href="%s">%s</a>"""

HTML_EMPTY_MUTATION_CELL = """<span class="empty"></span>"""

HTML_MUTATION_PRESENT_FALSE_CELL_HTML = """<span class="false">%d/%d</span>"""

HTML_MUTATION_PRESENT_TRUE_CELL_HTML = """<a class="true" href="%s">%.2f</a>"""

SAVE_MUTATION_TO_FILTER_CELL_HTML = """<div class="dropdown">
  <button class="btn btn-default btn-xs dropdown-toggle" type="button" id="dropdownMenu1" data-toggle="dropdown" aria-haspopup="true" aria-expanded="true">
    <i class="fa fa-filter" aria-hidden="true"></i>
  </button>
  <ul class="dropdown-menu" aria-labelledby="dropdownMenu1">
    <li><a onclick="save_to_global_filter(%d)" style="cursor:pointer">Save to Global Filter</a></li>
    <li><a onclick="save_to_experiment_filter(%d, %d)" style="cursor:pointer">Save to Experiment Filter</a></li>
    %s
  </ul>
</div>"""

SAVE_TO_GLOBAL_FILTER_ONLY = """<div class="dropdown">
  <button class="btn btn-default btn-xs dropdown-toggle" type="button" id="dropdownMenu1" data-toggle="dropdown" aria-haspopup="true" aria-expanded="true">
    <i class="fa fa-filter" aria-hidden="true"></i>
  </button>
  <ul class="dropdown-menu" aria-labelledby="dropdownMenu1">
    <li><a onclick="save_to_global_filter(%d)" style="cursor:pointer">Save to Global Filter</a></li>
    %s
  </ul>
</div>
"""

GENE_ENTRY_HTML_LINK = """<a href=/gene?g=%s>%s</a>"""

EXPANDABLE_COLUMN_PLUS_SIGN = """<i onclick="expand_collapse_gene_entry(this)" class="fa fa-plus pull-left" aria-hidden="true" data-toggle="collapse" data-target="#%s"></i>"""

EXPANDABLE_GENE_ENTRY = """<div class="collapse pull-left" id="%s">%s</div>"""

non_decimal = re.compile(r'[^\d.]+')

evidence = re.compile(r'[A-Z]\d+[A-Z]')


class TableType(Enum):
    GENE_TABLE = 1
    ENRICHMENT_MUTATIONS = 2
    FIXATING_MUTATIONS = 3
    SEARCH = 4
    SHARED = 5
    COMPARE = 6
    COMPARE_ENRICHEMENT_MUTATIONS = 7
    COMPARE_FIXATION_MUTATIONS = 8


if hasattr(aleinfo.settings, seq.views.common.SETTINGS_SEQUENCING_URL):
    reseqencing_report_url = aleinfo.settings.sequencing_url
else:
    reseqencing_report_url = seq.views.common.DEFAULT_RESEQ_REPORT_URL


def get_table_header(reseq_dict, table_type=None):

    if table_type == TableType.ENRICHMENT_MUTATIONS or table_type == TableType.FIXATING_MUTATIONS:
        base_table_header = [""] + HTML_MUTATION_TABLE_HEADER
    else:
        base_table_header = HTML_MUTATION_TABLE_HEADER

    experiment_urls = get_experiment_urls(reseq_dict)

    table_header_list = []

    for seq_experiment_id in reseq_dict:

        reseq = reseq_dict[seq_experiment_id]

        sample_name = reseq.aleexp_ale_flask_isolate_str

        table_header_list += [HTML_MUTATION_TABLE_EXPERIMENT_HEADER % (experiment_urls[seq_experiment_id], sample_name)]

    return base_table_header + table_header_list


# TODO: Refactor. The observed mutations argument may
# reference to a seq_experiment that doesn't exist due to checkbox filtering.
# This makes this function very confusing.
def get_table_body(reseq_dict,
                   observed_mutations_queryset,
                   ale_experiment_id=None,
                   filter_settings=None,
                   table_type=None):

    observed_mutations_queryset = filter_mutations(observed_mutations_queryset, filter_settings)

    mutation_queryset = get_mutation_queryset_from_obs_mut_queryset(observed_mutations_queryset)

    mutation_index_dict = dict((mutation_id, i) for i, mutation_id in enumerate(mutation_queryset.values_list("id", flat=True)))

    experiment_url_dict = get_experiment_urls(reseq_dict)

    experiment_id_idx_mapping_dict = _get_experiment_id_idx_mapping_dict(reseq_dict)

    # Initialize all sample mutation table cells as empty.
    table_entry_list = _initialize_table(experiment_id_idx_mapping_dict, mutation_queryset)

    # Populating table_entry_list
    for observed_mutation in observed_mutations_queryset:

        new_entry = _get_table_mutation_entry(observed_mutation, experiment_url_dict)

        if new_entry is not None and observed_mutation.sequencing_experiment_id in reseq_dict.keys():
            table_entry_list[mutation_index_dict[observed_mutation.mutation_id]][experiment_id_idx_mapping_dict[observed_mutation.sequencing_experiment_id]] = new_entry

    protein_changes = {}  # For calculating distances on the genes page only

    # Populating table body
    table_body = []

    for mutation in mutation_queryset:

        if _contains_mutation(table_entry_list[mutation_index_dict[mutation.id]]):

            table_row = [HTML_MUTATION_TABLE_ROW]
            if table_type == TableType.GENE_TABLE or \
                            table_type == TableType.SEARCH or \
                            table_type == TableType.SHARED or \
                            table_type == TableType.COMPARE or \
                            table_type == TableType.COMPARE_ENRICHEMENT_MUTATIONS or \
                            table_type == TableType.COMPARE_FIXATION_MUTATIONS:
                table_row.append(SAVE_TO_GLOBAL_FILTER_ONLY % (mutation.id, _get_tag_filter_dropdown_entries(mutation.id)))
            else:
                table_row.append(SAVE_MUTATION_TO_FILTER_CELL_HTML % (mutation.id, ale_experiment_id, mutation.id, _get_tag_filter_dropdown_entries(mutation.id)))

            if table_type == TableType.ENRICHMENT_MUTATIONS or table_type == TableType.COMPARE_ENRICHEMENT_MUTATIONS:
                table_row.append("<a href=/enrichment/shared?mutation_id=%s>shared</a>" % mutation.id)
            elif table_type == TableType.FIXATING_MUTATIONS or table_type == TableType.COMPARE_FIXATION_MUTATIONS:
                table_row.append("<a href=/fixation/shared?mutation_id=%s>shared</a>" % mutation.id)

            table_row.append(_get_tags(mutation.tags))
            table_row.append(format(mutation.position, ',d'))
            table_row.append(mutation.mutation_type)
            table_row.append(mutation.sequence_change)
            table_row.append(_get_gene_table_entry(mutation))
            table_row.append("" if mutation.function is None else mutation.function)
            table_row.append("" if mutation.product is None else mutation.product)
            table_row.append("" if mutation.go_process is None else mutation.go_process)
            table_row.append("" if mutation.go_component is None else mutation.go_component)

            if table_type is TableType.GENE_TABLE:
                if evidence.search(mutation.protein_change):
                    try:
                        table_row.append("<a id=\"%s\" onclick=\"highlight_mutation(%d,%d)\">%s</a>" %
                                         ("mutation_" + str(mutation.id), int(non_decimal.sub('', mutation.protein_change)),
                                          int(mutation.id), mutation.protein_change))
                        protein_changes[mutation.id] = strip_tags(mutation.protein_change)
                    except:
                        table_row.append(mutation.protein_change)
                else:
                    table_row.append(mutation.protein_change)
            else:
                table_row.append(mutation.protein_change)
            table_row += table_entry_list[mutation_index_dict[mutation.id]]

            table_body.append(table_row)

    if table_type is TableType.GENE_TABLE:
        return table_body, protein_changes

    return table_body


def _get_gene_table_entry(mutation):

    # table_entry = """<td style="width:150px">"""

    table_entry = """<div style="width:150px">"""

    original_gene_list = mutation.gene.split(',')

    cleaned_gene_list = get_gene_list(mutation.gene)

    gene_links = [GENE_ENTRY_HTML_LINK % (gene, original_gene_list[idx]) for idx, gene in enumerate(cleaned_gene_list)]

    if len(cleaned_gene_list) > 10:

        # first_gene = GENE_ENTRY_HTML_LINK % (cleaned_gene_list[0], original_gene_list[0])

        # last_gene = GENE_ENTRY_HTML_LINK % (cleaned_gene_list[-1], original_gene_list[-1])

        table_entry += EXPANDABLE_COLUMN_PLUS_SIGN % str(mutation.id)

        # table_entry += """<div class="pull-left"> %s ... %s</div>""" % (first_gene, last_gene)

        table_entry += EXPANDABLE_GENE_ENTRY % (str(mutation.id), ", ".join(gene_links))

    else:

        table_entry += ", ".join(gene_links) + "</div>"

    return table_entry


def _initialize_table(experiment_id_idx_mapping, mutations):
    return [[HTML_EMPTY_MUTATION_CELL] * len(experiment_id_idx_mapping) for _ in range(len(mutations))]


def get_experiment_urls(reseq_dict):

    experiment_urls = dict((i.id, reseqencing_report_url + i.location) for i in reseq_dict.values())

    return experiment_urls


def _get_experiment_id_idx_mapping_dict(seq_experiment_dict):

    experiment_id_idx_mapping = dict((reseq_exp_id, idx) for idx, reseq_exp_id in enumerate(seq_experiment_dict.keys()))

    return experiment_id_idx_mapping


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


def _get_tags(tags):

    html = ''

    if tags:

        for tag in tags.split(','):

            html += TAGS[tag]

    return html


def _get_tag_filter_dropdown_entries(mutation_id):

    html = ''

    for key, value in TAGS.items():

        html += '<li><a onclick="add_tag(\'%s\', %d)" style="cursor:pointer">Add Tag: %s %s</a></li>' % (key, mutation_id, key, value)

    return html


def get_tag_toggle_dropdown_entries():

    html = ''

    for key, value in TAGS.items():

        html += '<li><a onclick="filter_tag(\'%s\')" style="cursor:pointer">Show Tag: %s %s</a></li>' % (key, key, value)

    return html
