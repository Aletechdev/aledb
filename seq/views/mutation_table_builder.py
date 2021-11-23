from django.conf import settings
from django.contrib.auth.models import User
import seq.views.common
import re
from enum import Enum
from django.utils.html import strip_tags
from seq.util import get_ecocyc_gene_list
from filter.util import filter_observed_mutations
from genes.util import get_gene_list
from common.constants import TAGS, ROW_TAGS, COLUMN_TAGS, HTML_MUTATION_TABLE_HEADER
from ale.models import TechnicalReplicate, AleExperiment
from ale.permissions import can_add_global_filter, can_add_experiment_filter


EXPERIMENT_MAPPING_FILTERING_SHOW_FLAG = "show"
EXPERIMENT_MAPPING_FILTERING_REMOVE_FLAG = "remove"
HTML_MUTATION_TABLE_ROW = """<a href="javascript:void(0)" style="float:right" onclick="deleteRow.call(this)"><img src="/static/img/close-icon.gif" width="12" height="11"></a>"""
HTML_EMPTY_MUTATION_CELL = """<span class="empty"></span>"""
HTML_MUTATION_PRESENT_FALSE_CELL_HTML = """<span class="false">%d/%d</span>"""
HTML_MUTATION_PRESENT_TRUE_CELL_HTML = """<a class="true" href="%s">%.2f</a>/<a class="true" href="%s" target="_blank">%.2f</a>"""

EXPANDABLE_COLUMN_PLUS_SIGN = """<i onclick="expand_collapse_gene_entry(this)" class="fa fa-plus pull-left" aria-hidden="true" data-toggle="collapse" data-target="#%s"></i>"""
EXPANDABLE_GENE_ENTRY = """<div class="collapse pull-left" id="%s">%s</div>"""
non_decimal = re.compile(r'[^\d.]+')
evidence = re.compile(r'[A-Z]\d+[A-Z]')
REP_DROPDOWN = '<div class="dropdown tag_dropdown"><button class="btn btn-default btn-xs dropdown-toggle" type="button" id="dropdownMenu2" data-toggle="dropdown" aria-haspopup="true" aria-expanded="true">' \
             '<i class="fa fa-tags" aria-hidden="true"></i>' \
             '</button>' \
             '<ul class="dropdown-menu" aria-labelledby="dropdownMenu1">' \
             '%s' \
             '</ul>'
REP_TAG = '</div><div class="tag_dropdown">%s</div>'

# the dropdown cell in the mutation table
_menu_item_save_to_global_filter = """<li><a onclick="save_to_global_filter(%d)" style="cursor:pointer">Save to Global Filter</a></li>"""
_menu_item_save_to_experiment_filter = """<li><a onclick="save_to_experiment_filter(%d, %d)" style="cursor:pointer">Save to Experiment Filter</a></li>"""
_table_cell_dropdown_template = """<div class="dropdown">
  <button class="btn btn-default btn-xs dropdown-toggle" type="button" id="dropdownMenu1" data-toggle="dropdown" aria-haspopup="true" aria-expanded="true">
    <i class="fa fa-filter" aria-hidden="true"></i>
  </button>
  <ul class="dropdown-menu" aria-labelledby="dropdownMenu1">
    %s
  </ul>
</div>"""


def _build_table_cell_for_dropdown(mutation, ale_experiment):
    """Returns a <div> element containing the drop down menu for each row
    in the mutation table.

    NOTE: this is a temporary solution for implementing #425 until the
    mutation table component rendering is refactored
    """

    menuitems = ''
    # all tables have a 'Save to Global Filter' menuitem
    #menuitems = _menu_item_save_to_global_filter % (mutation.id)

    # some other tables have a 'Save to Experiment Filter' menuitem
    if ale_experiment:
        menuitems += _menu_item_save_to_experiment_filter % (ale_experiment.ale_id, mutation.id)

    return _table_cell_dropdown_template % (menuitems + _get_tag_filter_dropdown_entries(mutation.id))


class TableType(Enum):
    GENE_TABLE = 1
    ENRICHMENT_MUTATIONS = 2
    FIXATING_MUTATIONS = 3
    SEARCH = 4
    SHARED = 5
    # COMBINE = 6
    # COMBINE_ENRICHMENT_MUTATIONS = 7
    # COMBINE_FIXATION_MUTATIONS = 8


if hasattr(settings, seq.views.common.SETTINGS_SEQUENCING_URL):
    resequencing_report_url = settings.SEQUENCING_URL
else:
    resequencing_report_url = seq.views.common.DEFAULT_RESEQ_REPORT_URL


def get_table_header(user, reseq_dict, experiment: AleExperiment = None):
    base_table_header = HTML_MUTATION_TABLE_HEADER
    experiment_urls = get_experiment_root_urls(reseq_dict)
    gatk_urls = get_gatk_urls(reseq_dict)
    table_header_list = []

    for reseq_id in reseq_dict:
        reseq = reseq_dict[reseq_id]
        sample_name = reseq.ale_flask_isolate_str
        if not experiment:
            sample_name = reseq.exp_ale_flask_isolate_str

        sample_header_html = sample_name
        if reseq_id in experiment_urls.keys():
            sample_header_html = """<a href="%s" target="_blank">%s</a>"""
            sample_header_html = sample_header_html % (experiment_urls[reseq_id], sample_name)
        if can_add_global_filter(user) or can_add_experiment_filter(user, experiment):
            dropdown_html = _get_replicate_tag_dropdown_entries(reseq.tech_rep)
            sample_header_html += (REP_DROPDOWN % dropdown_html)
        current_tags = _get_rep_tags(reseq.tech_rep)
        sample_header_html += (REP_TAG % current_tags)
        table_header_list.append(sample_header_html)
    return base_table_header + table_header_list


def get_mutation_table_body(user: User, observed_mutations: [], reseq_dict, experiment: AleExperiment = None, is_gene_table: bool = False):
    mutations, table_entry_list, mutation_index_dict = get_mutation_table_data(reseq_dict, observed_mutations)

    protein_changes = {}
    table_body = []
    for mutation in mutations:
        if _contains_mutation(table_entry_list[mutation_index_dict[mutation.id]]):
            table_row = [HTML_MUTATION_TABLE_ROW]
            if can_add_global_filter(user) or can_add_experiment_filter(user, experiment):
                table_row.append(_build_table_cell_for_dropdown(mutation, experiment))
            else:
                table_row.append("""""")

            table_row.append(_get_mutation_tags(mutation.tags))
            table_row.append("" if mutation.reseq_reference is None else mutation.reseq_reference)
            table_row.append(format(mutation.position, ',d'))
            table_row.append(mutation.mutation_type)
            table_row.append(mutation.sequence_change)
            table_row.append(get_gene_table_entry(mutation))
            table_row.append("" if mutation.function is None else mutation.function)
            table_row.append("" if mutation.product is None else mutation.product)
            table_row.append("" if mutation.go_process is None else mutation.go_process)
            table_row.append("" if mutation.go_component is None else mutation.go_component)
            table_row.append(mutation.id)
            if is_gene_table:
                if evidence.search(mutation.protein_change):
                    try:
                        table_row.append("<a id=\"%s\" onclick=\"highlight_mutation(%d,%d)\" target=\"_blank\">%s</a>" %
                                         ("mutation_" + str(mutation.id),
                                          int(non_decimal.sub('', mutation.protein_change)),
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

    if is_gene_table:
        return table_body, protein_changes

    return table_body


def get_mutation_table_data(reseq_dict, observed_mutations):
    mutation_map = {obs_mut.mutation.id: obs_mut.mutation for obs_mut in observed_mutations}
    mutation_index_dict = dict((mutation_id, i) for i, mutation_id in enumerate(mutation_map.keys()))
    # resequencing_experiment urls
    experiment_url_dict = get_experiment_urls(reseq_dict)
    gatk_url_dict = get_gatk_urls(reseq_dict)
    experiment_id_idx_mapping_dict = _get_experiment_id_idx_mapping_dict(reseq_dict)
    # Initialize all sample mutation table cells as empty.
    table_entry_list = _initialize_table(experiment_id_idx_mapping_dict, mutation_index_dict)
    for observed_mutation in observed_mutations:
        new_entry = _get_table_mutation_entry(observed_mutation, experiment_url_dict, gatk_url_dict)
        if new_entry is not None and observed_mutation.sequencing_experiment_id in reseq_dict.keys():
            table_entry_list[mutation_index_dict[observed_mutation.mutation_id]][
                experiment_id_idx_mapping_dict[observed_mutation.sequencing_experiment_id]] = new_entry
    return mutation_map.values(), table_entry_list, mutation_index_dict


# reference to a seq_experiment that doesn't exist due to checkbox filtering.
# This makes this function very confusing.
def get_table_body(user: User,
                   reseq_dict,
                   observed_mutations_queryset,
                   ale_experiment=None,
                   is_gene_table=False):
    observed_mutations = filter_observed_mutations(observed_mutations_queryset)
    return get_mutation_table_body(user, observed_mutations, reseq_dict, ale_experiment, is_gene_table)


def get_gene_table_entry(mutation):
    table_entry = """<div style="width: 150px; white-space: nowrap; overflow-x: scroll;">"""
    cleaned_gene_list = get_ecocyc_gene_list(get_gene_list(mutation.gene), mutation.is_ecocyc_gene())

    if len(cleaned_gene_list) > 10:
        table_entry += EXPANDABLE_COLUMN_PLUS_SIGN % str(mutation.id)
        table_entry += EXPANDABLE_GENE_ENTRY % (str(mutation.id), ", ".join(cleaned_gene_list))
    else:
        table_entry += ", ".join(cleaned_gene_list) + "</div>"
    return table_entry


def _initialize_table(experiment_id_idx_mapping, mutations):
    return [[HTML_EMPTY_MUTATION_CELL] * len(experiment_id_idx_mapping) for _ in range(len(mutations))]


# get resequencing_experiment urls
def get_experiment_urls(reseq_dict):
    # experiment_urls = dict((i.id, resequencing_report_url + i.location) for i in reseq_dict.values())
    experiment_urls = {}
    for reseq in reseq_dict.values():
        if reseq.location != "":
            experiment_urls[reseq.id] = resequencing_report_url + reseq.location
    return experiment_urls


def get_experiment_root_urls(reseq_dict):
    # experiment_urls = dict((i.id, resequencing_report_url + i.location) for i in reseq_dict.values())
    experiment_urls = {}
    for reseq in reseq_dict.values():
        if reseq.experiment_location != "":
            experiment_urls[reseq.id] = resequencing_report_url + reseq.experiment_location + '/' + reseq.sample_name + '.html'
    return experiment_urls


def get_gatk_urls(reseq_dict):
    # experiment_urls = dict((i.id, resequencing_report_url + i.location) for i in reseq_dict.values())
    gatk_urls = {}
    for reseq in reseq_dict.values():
        if reseq.location != "":
            gatk_urls[reseq.id] = resequencing_report_url + reseq.gatk_location
    return gatk_urls


def _get_experiment_id_idx_mapping_dict(seq_experiment_dict):
    experiment_id_idx_mapping = dict((reseq_exp_id, idx) for idx, reseq_exp_id in enumerate(seq_experiment_dict.keys()))
    return experiment_id_idx_mapping


def _get_table_mutation_entry(observed_mutation, experiment_url_dict, gatk_url_dict):
    table_entry = ""
    if observed_mutation.breseq_present or observed_mutation.gatk_present:
        #there's a chance for null values in frequency
        if observed_mutation.sequencing_experiment_id in experiment_url_dict:
            url = experiment_url_dict[observed_mutation.sequencing_experiment_id]
            evidence_url = url + _find_between(observed_mutation.evidence, "\"", "\"")
            gatk_url = gatk_url_dict[observed_mutation.sequencing_experiment_id]
            gatk_evidence = gatk_url + 'evidence/' + str(observed_mutation.mutation.position) + '.html'

            if observed_mutation.mutation.mutation_type == "AMP" or (observed_mutation.mutation.mutation_type == "DEL" and int(observed_mutation.mutation.feature_length) > 190):
                gatk_cnv_evidence = gatk_url + 'coverage_evidence/' + str(observed_mutation.mutation.position) + '.png'
                table_entry = HTML_MUTATION_PRESENT_TRUE_CELL_HTML % (evidence_url, float(observed_mutation.frequency),
                                                                      gatk_cnv_evidence,
                                                                      float(observed_mutation.frequency_gatk))
            else:
                table_entry = HTML_MUTATION_PRESENT_TRUE_CELL_HTML % (evidence_url, float(observed_mutation.frequency),
                                                                  gatk_evidence, float(observed_mutation.frequency_gatk))

        else:
            table_entry = """<span class="true">%.2f/%.2f</span>""" % (observed_mutation.frequency, observed_mutation.frequency_gatk)

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
    except:
        return ""


def _get_mutation_tags(tags):
    html = ''
    if tags:
        for tag in tags.split(','):
            html += '<span class="fa-stack">%s<font style="font-size:0px">%s</font></span>' % (TAGS[tag], tag)
    return html


def _get_tag_filter_dropdown_entries(mutation_id):
    html = ''
    for tag in ROW_TAGS:
        html += '<li><a onclick="add_tag(\'%s\', %d, this)" style="cursor:pointer">Toggle Tag: %s %s</a></li>' % (
        tag, mutation_id, tag, TAGS[tag])

    return html


def _get_replicate_tag_dropdown_entries(replicate: TechnicalReplicate):
    dropdown_html = ''
    for tag in COLUMN_TAGS:
        image = TAGS[tag]
        dropdown_html += '<li><a onclick="add_tag_to_replicate(\'%s\', %d, this)">Toggle Tag: %s %s</a></li>' % (
        tag, replicate.id, tag, image)
    return dropdown_html


def _get_rep_tags(replicate: TechnicalReplicate):
    tags = replicate.tags;
    current_tags = ''
    for tag in COLUMN_TAGS:
        image = TAGS[tag]
        if tags and tag in tags:
            current_tags += '<span class="fa-stack">%s<font style="font-size:0px">%s</font></span>' % (image, tag)
        else:
            current_tags += '<span class="fa-stack" style="display:none">%s<font style="font-size:0px">%s</font></span>' % (image, tag)
    return current_tags


