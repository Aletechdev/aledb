from django.conf import settings
from django.contrib.auth.models import User
import seq.views.common
from filter.util import get_filtered_observed_mutations_queryset
import re
from enum import Enum
from django.utils.html import strip_tags
from seq.util import get_mut_queryset_from_obs_mut_queryset, get_ecocyc_gene_list
from genes.util import get_gene_list
from common.constants import TAGS, ROW_TAGS, COLUMN_TAGS
from ale.models import TechnicalReplicate
from filter.models import AleExperimentFilter
from ale.permissions import can_add_global_filter


EXPERIMENT_MAPPING_FILTERING_SHOW_FLAG = "show"
EXPERIMENT_MAPPING_FILTERING_REMOVE_FLAG = "remove"
HTML_MUTATION_TABLE_ROW = """<a href="javascript:void(0)" style="float:right" onclick="deleteRow.call(this)"><img src="/static/img/close-icon.gif" width="12" height="11"></a>"""
HTML_MUTATION_TABLE_HEADER = ["", "", "Tags", "Position", "Mutation Type", "Sequence Change", "Gene", "Function",
                              "Product", "GO Process", "GO Component", "Details"]
HTML_EMPTY_MUTATION_CELL = """<span class="empty"></span>"""
HTML_MUTATION_PRESENT_FALSE_CELL_HTML = """<span class="false">%d/%d</span>"""
HTML_MUTATION_PRESENT_TRUE_CELL_HTML = """<a class="true" href="%s">%.2f</a>"""

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


def _build_table_cell_for_dropdown(table_type, mutation_id, ale_experiment_id):
    """Returns a <div> element containing the drop down menu for each row
    in the mutation table.

    NOTE: this is a temporary solution for implementing #425 until the
    mutation table component rendering is refactored
    """

    menuitems = ''
    # all tables have a 'Save to Global Filter' menuitem
    menuitems = _menu_item_save_to_global_filter % (mutation_id)

    # some other tables have a 'Save to Experiment Filter' menuitem
    if (not table_type in [TableType.GENE_TABLE \
            , TableType.SEARCH \
            , TableType.SHARED \
            # , TableType.COMBINE \
            # , TableType.COMBINE_ENRICHMENT_MUTATIONS \
            # , TableType.COMBINE_FIXATION_MUTATIONS \
                           ]):
        menuitems += _menu_item_save_to_experiment_filter % (ale_experiment_id, mutation_id)

    return _table_cell_dropdown_template % (menuitems + _get_tag_filter_dropdown_entries(mutation_id))


EXPANDABLE_COLUMN_PLUS_SIGN = """<i onclick="expand_collapse_gene_entry(this)" class="fa fa-plus pull-left" aria-hidden="true" data-toggle="collapse" data-target="#%s"></i>"""
EXPANDABLE_GENE_ENTRY = """<div class="collapse pull-left" id="%s">%s</div>"""
non_decimal = re.compile(r'[^\d.]+')
evidence = re.compile(r'[A-Z]\d+[A-Z]')
TAGS_IMAGE = '<div class="dropdown tag_dropdown"><button class="btn btn-default btn-xs dropdown-toggle" type="button" id="dropdownMenu2" data-toggle="dropdown" aria-haspopup="true" aria-expanded="true">' \
             '<i class="fa fa-tags" aria-hidden="true"></i>' \
             '</button>' \
             '<ul class="dropdown-menu" aria-labelledby="dropdownMenu1">' \
             '%s' \
             '</ul>' \
             '</div><div class="tag_dropdown">%s</div>'


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


def get_table_header(user, reseq_dict, table_type=None):
    base_table_header = HTML_MUTATION_TABLE_HEADER
    experiment_urls = get_experiment_urls(reseq_dict)
    table_header_list = []

    for reseq_id in reseq_dict:
        reseq = reseq_dict[reseq_id]
        sample_name = reseq.exp_ale_flask_isolate_str
        current_tags, dropdown_html = _get_tag_replicate_dropdown_entries(reseq.tech_rep)

        sample_header_html = sample_name
        if reseq_id in experiment_urls.keys():
            sample_header_html = """<a href="%s">%s</a>"""
            sample_header_html = sample_header_html % (experiment_urls[reseq_id], sample_name)

        if can_add_global_filter(user):
            table_header_list.append(sample_header_html + (TAGS_IMAGE % (dropdown_html, current_tags)))
        else:
            table_header_list.append(sample_header_html)

    return base_table_header + table_header_list

def get_mutation_table_data(reseq_dict, observed_mutations):
    mutation_map = {obs_mut.mutation.id: obs_mut.mutation for obs_mut in observed_mutations}
    mutation_index_dict = dict((mutation_id, i) for i, mutation_id in enumerate(mutation_map.keys()))
    # resequencing_experiment urls
    experiment_url_dict = get_experiment_urls(reseq_dict)
    experiment_id_idx_mapping_dict = _get_experiment_id_idx_mapping_dict(reseq_dict)
    # Initialize all sample mutation table cells as empty.
    table_entry_list = _initialize_table(experiment_id_idx_mapping_dict, mutation_index_dict)
    for observed_mutation in observed_mutations:
        new_entry = _get_table_mutation_entry(observed_mutation, experiment_url_dict)
        if new_entry is not None and observed_mutation.sequencing_experiment_id in reseq_dict.keys():
            table_entry_list[mutation_index_dict[observed_mutation.mutation_id]][
                experiment_id_idx_mapping_dict[observed_mutation.sequencing_experiment_id]] = new_entry
    return mutation_map.values(), table_entry_list, mutation_index_dict


def get_mutation_table_queryset_and_entry_list(reseq_dict, observed_mutations_queryset, do_filter=True):
    # print("reseq_dict", len(reseq_dict))
    obs_mut_qryset = observed_mutations_queryset
    if do_filter:
        obs_mut_qryset = get_filtered_observed_mutations_queryset(observed_mutations_queryset)
    mut_qryset = get_mut_queryset_from_obs_mut_queryset(obs_mut_qryset)
    mutation_index_dict = dict(
        (mutation_id, i) for i, mutation_id in enumerate(mut_qryset.values_list("id", flat=True)))
    # resequencing_experiment urls
    experiment_url_dict = get_experiment_urls(reseq_dict)
    experiment_id_idx_mapping_dict = _get_experiment_id_idx_mapping_dict(reseq_dict)

    # Initialize all sample mutation table cells as empty.
    table_entry_list = _initialize_table(experiment_id_idx_mapping_dict, mut_qryset)

    # Populating table_entry_list
    unique_mut_obs_mut_dict = dict()  # hold one obs mutation for each mutation
    # make sure related objects loaded
    obs_mut_qryset = obs_mut_qryset.select_related(
        'sequencing_experiment__tech_rep__isolate__flask__ale_id__ale_experiment',
        'mutation'
    )
    for observed_mutation in obs_mut_qryset:
        new_entry = _get_table_mutation_entry(observed_mutation, experiment_url_dict)
        if new_entry is not None and observed_mutation.sequencing_experiment_id in reseq_dict.keys():
            table_entry_list[mutation_index_dict[observed_mutation.mutation_id]][
                experiment_id_idx_mapping_dict[observed_mutation.sequencing_experiment_id]] = new_entry
        mutation_id = observed_mutation.mutation_id
        if mutation_id not in unique_mut_obs_mut_dict:
            unique_mut_obs_mut_dict[observed_mutation.mutation.id] = observed_mutation
    # return mut_qryset, table_entry_list, mutation_index_dict, get_unique_obs_mut_queryset_from_obs_mut_queryset(obs_mut_qryset)
    return mut_qryset, table_entry_list, mutation_index_dict, unique_mut_obs_mut_dict


def get_mutation_table_queryset_and_entry_list_for_export(reseq_dict, observed_mutations_queryset, exp_id, do_filter=True):
    """
    By R. Cai
    Add function specifically for mutation export.  It does not need to get observed mutations
    that is used to extract strain information to decide if gene link is needed)
    :param reseq_dict:
    :param observed_mutations_queryset:
    :param do_filter
    :return: mut_qryset, table_entry_list, mutation_index_dict
    """
    obs_mut_qryset = observed_mutations_queryset
    if do_filter:
        filter_settings = AleExperimentFilter.objects.filter(ale_experiment__ale_id=exp_id).first()
        obs_mut_qryset = get_filtered_observed_mutations_queryset(observed_mutations_queryset, filter_settings)
    mut_qryset = get_mut_queryset_from_obs_mut_queryset(obs_mut_qryset)
    mutation_index_dict = dict(
        (mutation_id, i) for i, mutation_id in enumerate(mut_qryset.values_list("id", flat=True)))
    experiment_url_dict = get_experiment_urls(reseq_dict)
    experiment_id_idx_mapping_dict = _get_experiment_id_idx_mapping_dict(reseq_dict)

    # Initialize all sample mutation table cells as empty.
    table_entry_list = _initialize_table(experiment_id_idx_mapping_dict, mut_qryset)

    # Populating table_entry_list
    for observed_mutation in obs_mut_qryset:
        new_entry = _get_table_mutation_entry(observed_mutation, experiment_url_dict)
        if new_entry is not None and observed_mutation.sequencing_experiment_id in reseq_dict.keys():
            table_entry_list[mutation_index_dict[observed_mutation.mutation_id]][
                experiment_id_idx_mapping_dict[observed_mutation.sequencing_experiment_id]] = new_entry
    return mut_qryset, table_entry_list, mutation_index_dict


def get_mutation_table_body(user: User, observed_mutations: [], reseq_dict, table_type: str):
    mutations, table_entry_list, mutation_index_dict = get_mutation_table_data(reseq_dict, observed_mutations)

    protein_changes = {}
    table_body = []
    for observed_mutation in observed_mutations:
        mutation = observed_mutation.mutation
        if _contains_mutation(table_entry_list[mutation_index_dict[observed_mutation.mutation.id]]):
            table_row = [HTML_MUTATION_TABLE_ROW]
            if can_add_global_filter(user):
                table_row.append(_build_table_cell_for_dropdown(table_type, mutation.id, observed_mutation.get_experiment_id(), ))
            else:
                table_row.append("""""")

            table_row.append(_get_mutation_tags(mutation.tags))
            table_row.append(format(mutation.position, ',d'))
            table_row.append(mutation.mutation_type)
            table_row.append(mutation.sequence_change)
            table_row.append(get_gene_table_entry(observed_mutation))
            table_row.append("" if mutation.function is None else mutation.function)
            table_row.append("" if mutation.product is None else mutation.product)
            table_row.append("" if mutation.go_process is None else mutation.go_process)
            table_row.append("" if mutation.go_component is None else mutation.go_component)

            if table_type is TableType.GENE_TABLE:
                if evidence.search(mutation.protein_change):
                    try:
                        table_row.append("<a id=\"%s\" onclick=\"highlight_mutation(%d,%d)\">%s</a>" %
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

    if table_type is TableType.GENE_TABLE:
        return table_body, protein_changes

    return table_body


# TODO: Refactor. The observed mutations argument may
# reference to a seq_experiment that doesn't exist due to checkbox filtering.
# This makes this function very confusing.
def get_table_body(user: User,
                   reseq_dict,
                   observed_mutations_queryset,
                   ale_experiment_id=None,
                   table_type=None,
                   do_filter=True):
    mutation_queryset, \
    table_entry_list, \
    mutation_index_dict, \
    filtered_observed_mutation_dict = get_mutation_table_queryset_and_entry_list(
        reseq_dict, observed_mutations_queryset, do_filter=do_filter)

    protein_changes = {}  # For calculating distances on the genes page only

    # Populating table body
    table_body = []
    for mut_id, observed_mutation in filtered_observed_mutation_dict.items():
        mutation = observed_mutation.mutation
        if _contains_mutation(table_entry_list[mutation_index_dict[mut_id]]):
            table_row = [HTML_MUTATION_TABLE_ROW]
            if can_add_global_filter(user):
                table_row.append(_build_table_cell_for_dropdown(table_type, mutation.id, ale_experiment_id, ))
            else:
                table_row.append("""""")

            table_row.append(_get_mutation_tags(mutation.tags))
            table_row.append(format(mutation.position, ',d'))
            table_row.append(mutation.mutation_type)
            table_row.append(mutation.sequence_change)
            table_row.append(get_gene_table_entry(observed_mutation))
            table_row.append("" if mutation.function is None else mutation.function)
            table_row.append("" if mutation.product is None else mutation.product)
            table_row.append("" if mutation.go_process is None else mutation.go_process)
            table_row.append("" if mutation.go_component is None else mutation.go_component)

            if table_type is TableType.GENE_TABLE:
                if evidence.search(mutation.protein_change):
                    try:
                        table_row.append("<a id=\"%s\" onclick=\"highlight_mutation(%d,%d)\">%s</a>" %
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

    if table_type is TableType.GENE_TABLE:
        return table_body, protein_changes

    return table_body


def get_gene_table_entry(observed_mutation):
    need_links = True
    strain = observed_mutation.sequencing_experiment.tech_rep.isolate.flask.ale_id.strain
    # RC - hard coded???
    if strain != "511145":
        need_links = False

    table_entry = """<div style="width:150px">"""
    cleaned_gene_list = get_gene_list(observed_mutation.mutation.gene)
    if need_links:
        cleaned_gene_list = get_ecocyc_gene_list(get_gene_list(observed_mutation.mutation.gene))

    if len(cleaned_gene_list) > 10:
        table_entry += EXPANDABLE_COLUMN_PLUS_SIGN % str(observed_mutation.mutation.id)
        table_entry += EXPANDABLE_GENE_ENTRY % (str(observed_mutation.mutation.id), ", ".join(cleaned_gene_list))
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


def _get_experiment_id_idx_mapping_dict(seq_experiment_dict):
    experiment_id_idx_mapping = dict((reseq_exp_id, idx) for idx, reseq_exp_id in enumerate(seq_experiment_dict.keys()))
    return experiment_id_idx_mapping


def _get_table_mutation_entry(observed_mutation, experiment_url_dict):
    table_entry = ""
    if observed_mutation.breseq_present:
        if observed_mutation.sequencing_experiment_id in experiment_url_dict:
            url = experiment_url_dict[observed_mutation.sequencing_experiment_id]
            evidence_url = url + _find_between(observed_mutation.evidence, "\"", "\"")
            table_entry = HTML_MUTATION_PRESENT_TRUE_CELL_HTML % (evidence_url, float(observed_mutation.frequency))
        else:
            table_entry = """<span class="true">%.2f</span>""" % observed_mutation.frequency

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


def _get_tag_replicate_dropdown_entries(replicate: TechnicalReplicate):
    # tags = TechnicalReplicate.objects.get(id=replicate_id).tags
    tags = replicate.tags;

    current_tags = ''

    dropdown_html = ''

    for tag in COLUMN_TAGS:

        image = TAGS[tag]

        dropdown_html += '<li><a onclick="add_tag_to_replicate(\'%s\', %d, this)">Toggle Tag: %s %s</a></li>' % (
        tag, replicate.id, tag, image)

        if tags and tag in tags:

            current_tags += '<span class="fa-stack">%s<font style="font-size:0px">%s</font></span>' % (image, tag)

        else:

            current_tags += '<span class="fa-stack" style="display:none">%s<font style="font-size:0px">%s</font></span>' % (
            image, tag)

    return current_tags, dropdown_html
