from filter.models import AleExperimentFilter, GlobalFilter
from seq.models import Mutation, ObservedMutation
from django.core.exceptions import ObjectDoesNotExist
from ale.models import AleExperiment
from genes.util import get_gene_list

__author__ = 'Patrick Phaneuf'

NO_BREAK_STRING_CODE = u'\xa0'

MODEL_TO_FILTER_MAPPINGS = {"protein": "protein_change",
                            "type": "mutation_type",
                            "sequence": "sequence_change",
                            "position": "position",
                            "gene": "gene"}

DELETE_ROW_BOX = """<td><img src="/static/close-icon.gif" onclick="delete_row(%d)" width="12" height="11" style="float:right; cursor:pointer"></td>"""

TABLE_HEADER = "<tr><td></td><td>Position</td><td>Mutation Type</td><td>Sequence Change</td><td>Gene</td><td>Function</td><td>Product</td><td>GO Process</td><td>GO Component</td><td>Protein change</td></tr>"


def filter_observed_mutations(observed_mutation_queryset, filter_settings=None):
    if filter_settings is None:
        return _filter_observed_mutations(observed_mutation_queryset)
    else:  # Ideally, we don't use the else, though have it for backwards compatibility.
        return _filter_observed_mutations_given_filter_settings(observed_mutation_queryset, filter_settings)


def _filter_observed_mutations(observed_mutation_queryset):
    # May have to deal with corner case that filter settings is still None
    # if filter_settings is None:
    #     ignored_genes = None
    #     ignored_mutations = None
    #     starting_strain_mutations = []
    #     min_cutoff = 0
    #     max_cutoff = 100
    ale_exp_qryset = AleExperiment.objects.filter(
        ale_id__in=ObservedMutation.objects.all().values(
            "sequencing_experiment__tech_rep__isolate__flask__ale_id__ale_experiment"))
    output_obs_mut_qryset = ObservedMutation.objects.none()
    for ale_exp in ale_exp_qryset:
        ale_exp_filter_settings = AleExperimentFilter.objects.get(ale_experiment__ale_id=ale_exp.ale_id)
        ale_exp_obs_mut_qryset = ObservedMutation.objects.all().filter(
            sequencing_experiment__tech_rep__isolate__flask__ale_id__ale_experiment__ale_id=ale_exp.ale_id)
        ale_exp_obs_mut_qryset = _filter_observed_mutations_given_filter_settings(ale_exp_obs_mut_qryset,
                                                                                  ale_exp_filter_settings)
        output_obs_mut_qryset = output_obs_mut_qryset | ale_exp_obs_mut_qryset
    return output_obs_mut_qryset

def _filter_observed_mutations_given_filter_settings(observed_mutation_queryset, filter_settings):
    ignored_genes = filter_settings.ignored_genes
    ignored_mutations = filter_settings.ignored_mutations
    starting_strain_mutations = filter_settings.starting_strain_mutations.split(',')
    if starting_strain_mutations == ['']:
        starting_strain_mutations = []
    min_cutoff = filter_settings.min_cutoff
    max_cutoff = filter_settings.max_cutoff

    ignored_genes = _append_global_filter_ignored_genes(ignored_genes)
    observed_mutation_queryset = _ignored_genes_filter(observed_mutation_queryset, ignored_genes)
    observed_mutation_queryset = _ignored_muts_filter(observed_mutation_queryset, ignored_mutations,
                                                      starting_strain_mutations)
    observed_mutation_queryset = _frequency_filter(observed_mutation_queryset, min_cutoff, max_cutoff)

    return observed_mutation_queryset


def _append_global_filter_ignored_genes(ignored_genes):
    ignored_genes = _clean_ignored_genes_list(ignored_genes)
    global_filter = get_global_filter()
    global_ignored_genes = global_filter.ignored_genes.replace(' ', '').replace('\n', '').replace('\r', '').split(',')

    if ignored_genes == ['']:
        if global_ignored_genes != ['']:
            ignored_genes = global_ignored_genes
        else:
            ignored_genes = []
    else:
        if global_ignored_genes != ['']:
            ignored_genes += global_ignored_genes

    return ignored_genes


def _ignored_genes_filter(observed_mutation_queryset, ignored_genes):
    if ignored_genes:
        if len(ignored_genes) > 0 and ignored_genes[0] is not '':
            ignored_mutation_id_list = []
            for observed_mutation in observed_mutation_queryset:
                gene_list = get_gene_list(observed_mutation.mutation.gene)
                if set(gene_list).issubset(set(ignored_genes)):
                    ignored_mutation_id_list.append(observed_mutation.mutation.id)
            if ignored_mutation_id_list:
                observed_mutation_queryset = observed_mutation_queryset.exclude(mutation__id__in=ignored_mutation_id_list)
    return observed_mutation_queryset


def _ignored_muts_filter(observed_mutation_queryset, ignored_mutations, starting_strain_mutations):
    global_filter = get_global_filter()
    global_ignored_mutations = global_filter.ignored_mutations
    global_ignored_mutations = clean_ignored_mutation_id_list(global_ignored_mutations)
    ignored_mutations = clean_ignored_mutation_id_list(ignored_mutations)
    ignored_mutation_list = global_ignored_mutations + ignored_mutations + starting_strain_mutations
    observed_mutation_queryset = observed_mutation_queryset.exclude(mutation_id__in=ignored_mutation_list)
    return observed_mutation_queryset


def is_number(s):
    try:
        int(s)
        return True
    except ValueError:
        return False


def _frequency_filter(observed_mutation_queryset, min_cutoff, max_cutoff):
    observed_mutation_queryset = observed_mutation_queryset.filter(frequency__gte=min_cutoff / 100, frequency__lte=max_cutoff / 100)
    return observed_mutation_queryset


def get_filter_settings(ale_experiment_id):
    filter_settings, created = AleExperimentFilter.objects.get_or_create(ale_experiment_id=ale_experiment_id)
    return filter_settings


def clean_ignored_mutation_id_list(ignored_mutation_id_list, deleted_mutation_id=None):

    if not ignored_mutation_id_list:
        return []

    if ignored_mutation_id_list.startswith(','):
        ignored_mutation_id_list = ignored_mutation_id_list[1:]

    ignored_mutation_id_list = ignored_mutation_id_list.split(",")

    new_list = []

    for mut_id in ignored_mutation_id_list:

        if mut_id in new_list or is_number(mut_id) is False or not _mutation_exists(mut_id):
            continue

        if deleted_mutation_id is None or mut_id != deleted_mutation_id:
            new_list.append(mut_id)

    return new_list


def _clean_ignored_genes_list(ignored_genes):

    if not ignored_genes:
        return []

    if ignored_genes.endswith(','):
        ignored_genes = ignored_genes[:-1]

    if ignored_genes.startswith(','):
        ignored_genes = ignored_genes[1:]

    ignored_genes = ignored_genes.replace(" ", "").replace('\n', '').replace('\r', '').split(',')
    cleaned_list = []

    for gene in ignored_genes:

        if gene == '' or not gene:
            continue

        cleaned_list.append(gene)

    return cleaned_list


def get_ignored_mutations(filter_form_model):

    table_body = ""

    ignored_mutation_id_list = filter_form_model.ignored_mutations

    ignored_mutation_id_list = clean_ignored_mutation_id_list(ignored_mutation_id_list)

    for mut_id in ignored_mutation_id_list:
        try:
            mutation = Mutation.objects.get(id=mut_id)
        except ObjectDoesNotExist:
            continue

        table_row = '<tr id="%s">' % mutation.id
        table_row += DELETE_ROW_BOX % mutation.id
        table_row += "<td>%s</td>" % format(int(mutation.position), ',d')
        table_row += "<td>%s</td>" % mutation.mutation_type
        table_row += "<td>%s</td>" % mutation.sequence_change
        table_row += "<td><a href=/gene?g=%s>%s</a></td>" % (mutation.gene, mutation.gene)
        table_row += "<td>%s</td>" % ("" if mutation.function is None else mutation.function)
        table_row += "<td>%s</td>" % ("" if mutation.product is None else mutation.product)
        table_row += "<td>%s</td>" % ("" if mutation.go_process is None else mutation.go_process)
        table_row += "<td>%s</td>" % ("" if mutation.go_component is None else mutation.go_component)
        table_row += "<td>%s</td>" % mutation.protein_change
        table_row += "</tr>"
        table_body += table_row

    if table_body is None:
        table_body = []

    return table_body, ignored_mutation_id_list


# TODO: should no longer use this; rather use filter_observed_mutations()
def filter_obs_muts(obs_mut_queryset, ale_experiment_list='all'):
    # Input of obs_mut_queryset
    # Get ALE exps (redundant since ALE experiments can be pulled from obs_mut_queryset quickly using ORM. This is done at the end of search.views._get_obs_muts).
    if ale_experiment_list == 'all':
        ale_exp_queryset = AleExperiment.objects.all()
    else:
        ale_exp_queryset = AleExperiment.objects.filter(ale_id__in=ale_experiment_list)
    # Get global mutation filter.
    global_filter = get_global_filter()
    # For each ALE exp of obs_mut_queryset
    for exp in ale_exp_queryset:
        # Get ALE exp filter settings
        filter_settings = get_filter_settings(exp.ale_id)
        # Filter out obs_muts that aren't within upper and lower thresholds according to specific ALE exp.
        obs_mut_queryset = obs_mut_queryset.exclude(
            sequencing_experiment__tech_rep__isolate__flask__ale_id__ale_experiment__ale_id=exp.ale_id,
            frequency__lt=filter_settings.min_cutoff / 100,
            frequency__gt=filter_settings.max_cutoff / 100)
        # Filter out obs_muts according to MUTS in global filter and each ALE exp filter.
        ignored_mut_list = clean_ignored_mutation_id_list(filter_settings.ignored_mutations +
                                                           global_filter.ignored_mutations +
                                                           "," + filter_settings.starting_strain_mutations)
        for mut_id in ignored_mut_list:
            obs_mut_queryset = obs_mut_queryset.exclude(
                sequencing_experiment__tech_rep__isolate__flask__ale_id__ale_experiment__ale_id=exp.ale_id,
                mutation_id=mut_id)

        # Filter out obs_muts according to GENES in global filter and each ALE exp filter.
        ignored_genes = _clean_ignored_genes_list(filter_settings.ignored_genes + "," + global_filter.ignored_genes)
        for gene in ignored_genes:
            obs_mut_queryset = obs_mut_queryset.exclude(
                sequencing_experiment__tech_rep__isolate__flask__ale_id__ale_experiment__ale_id=exp.ale_id,
                mutation__gene__contains=gene)

    return obs_mut_queryset


def _mutation_exists(mut_id):
    try:
        Mutation.objects.get(id=mut_id)
        return True
    except ObjectDoesNotExist:
        return False


def get_global_filter():
    global_filter, created = GlobalFilter.objects.get_or_create(id=1)
    return global_filter
