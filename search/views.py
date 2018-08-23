from django.http import HttpResponse
from django.utils.safestring import mark_safe
from django.template import loader
from django.shortcuts import render
from seq.models import ObservedMutation, Mutation
from ale.models import AleExperiment
from django.db.models import Q
import operator, collections
from seq.models import ResequencingExperiment
from functools import reduce
from seq.views import mutation_table_builder
from common.util import check_hidden_columns_and_filters, get_all_ale_exps, get_recent_ale_exps
from django.core.serializers.json import DjangoJSONEncoder
import json
from filter.util import get_filtered_observed_mutations_queryset
from logs.aledb_logger import get_logger,user_extra,all_get_extra


log = get_logger("aledbLogger")


def search(request):

    joined_extras = {**all_get_extra(request),**user_extra(request)}

    log.info("search terms", extra=joined_extras)
    check_hidden_columns_and_filters(request, None)
    obs_mut_qryset = _get_obs_mut_qryset(request)
    reseq_dict = _get_ordered_reseq_dict(obs_mut_qryset)
    if reseq_dict is None or obs_mut_qryset is None:
        return render(request, 'search.html', {'error': True,
                                               "experiments": get_all_ale_exps(),
                                               "recent_experiments": get_recent_ale_exps()})

    table_header = mutation_table_builder.get_table_header(request, reseq_dict)
    table_body = mutation_table_builder.get_table_body(request,
                                                       reseq_dict,
                                                       obs_mut_qryset,
                                                       table_type=mutation_table_builder.TableType.SEARCH)
    last_search = _get_last_search(request)
    template = loader.get_template("search.html")
    context = {"table_body": mark_safe(json.dumps(table_body, cls=DjangoJSONEncoder)),
               "title": "Search Results",
               "table_header": mark_safe(table_header),
               "last_search": last_search,
               "mutation_count": len(table_body),
               "observed_mutation_count": obs_mut_qryset.count(),
               "experiments": get_all_ale_exps(),
               "recent_experiments": get_recent_ale_exps()}



    return HttpResponse(template.render(context, request), content_type="text/html")


# TODO: roll _get_search_ale_exp_params into _get_search_params.
def _get_obs_mut_qryset(request):

    search_include_param_list, search_exclude_param_list = _get_search_params(request)
    if not search_include_param_list: return None
    mut_qryset = _get_mut_qryset(search_include_param_list, search_exclude_param_list)
    obs_mut_qryset = ObservedMutation.objects.filter(mutation__in=mut_qryset)

    ale_exp_to_include, ale_exp_to_exclude = _get_search_ale_exp_params(request)
    if ale_exp_to_exclude:
        obs_mut_qryset = obs_mut_qryset.exclude(
            sequencing_experiment__tech_rep__isolate__flask__ale_id__ale_experiment__ale_id__in=ale_exp_to_exclude)
    if ale_exp_to_include:
        obs_mut_qryset = obs_mut_qryset.filter(
            sequencing_experiment__tech_rep__isolate__flask__ale_id__ale_experiment__ale_id__in=ale_exp_to_include)

    obs_mut_qryset = get_filtered_observed_mutations_queryset(obs_mut_qryset)

    return obs_mut_qryset


def _get_ordered_reseq_dict(obs_muts_qryset):
    if not obs_muts_qryset: return None
    reseq_qryset = ResequencingExperiment.objects.select_related(
        'tech_rep__isolate__flask__ale_id__ale_experiment'
    ).order_by(
        'tech_rep__isolate__flask__ale_id__ale_experiment__name',
        'tech_rep__isolate__flask__ale_id__ale_id',
        'tech_rep__isolate__flask__flask_number',
        'tech_rep__isolate__isolate_number',
        'tech_rep__tech_rep_number'
    ).filter(mutations__observedmutation__in=obs_muts_qryset)
    reseq_ordered_dict = collections.OrderedDict((reseq.id, reseq) for reseq in reseq_qryset)
    return reseq_ordered_dict


def _get_last_search(request):
    last_search = {
        'q': request.GET['q'],
        'min': request.GET['min'],
        'max': request.GET['max'],
        'mut': request.GET['mut'],
        'seq': request.GET['seq'],
        'prot': request.GET['prot'],
        'ale': request.GET['ale']
    }
    return last_search


def _get_search_params(request):

    include_argument_list = []
    exclude_argument_list = []

    _add_genes_to_query(request, include_argument_list, exclude_argument_list)

    _add_min_and_max_to_query(request, include_argument_list)

    _add_mutation_change_to_query(request, include_argument_list, exclude_argument_list)

    _add_sequence_change_to_query(request, include_argument_list, exclude_argument_list)

    _add_protein_change_to_query(request, include_argument_list, exclude_argument_list)

    return include_argument_list, exclude_argument_list


def _add_genes_to_query(request, include_argument_list, exclude_argument_list):
    if 'q' in request.GET:

        gene_list = request.GET['q'].replace(" ", "").split(',')

        for mutated_gene in gene_list:
            if mutated_gene == '':
                continue
            if str(mutated_gene).startswith("-"):
                if str(mutated_gene).endswith("*"):
                    exclude_argument_list.append(Q(**{'gene__startswith': str(mutated_gene)[1:-1]}))

                elif str(mutated_gene)[1:].startswith("*"):
                    exclude_argument_list.append(Q(**{'gene__endswith': str(mutated_gene)[2:]}))

                else:
                    exclude_argument_list.append(Q(**{'gene__contains': str(mutated_gene)[1:]}))
            else:
                if str(mutated_gene).endswith("*"):
                    include_argument_list.append(Q(**{'gene__startswith': str(mutated_gene)[:-1]}))

                elif str(mutated_gene).startswith("*"):
                    include_argument_list.append(Q(**{'gene__endswith': str(mutated_gene)[1:]}))

                else:
                    include_argument_list.append(Q(**{'gene__contains': str(mutated_gene)}))


def _add_min_and_max_to_query(request, include_argument_list):
    if 'min' in request.GET and request.GET['min']:
        include_argument_list.append(Q(**{'position__gte': request.GET['min']}))

    if 'max' in request.GET and request.GET['max']:
        include_argument_list.append(Q(**{'position__lte': request.GET['max']}))


def _add_mutation_change_to_query(request, include_argument_list, exclude_argument_list):
    if 'mut' in request.GET and request.GET['mut']:
        mutation_type_list = request.GET['mut'].replace(" ", "").split(',')
        for mutation in mutation_type_list:
            if str(mutation).startswith("-"):
                exclude_argument_list.append(Q(**{'mutation_type': str(mutation)[1:].upper()}))
            else:
                include_argument_list.append(Q(**{'mutation_type': str(mutation).upper()}))


def _add_sequence_change_to_query(request, include_argument_list, exclude_argument_list):
    if 'seq' in request.GET and request.GET['seq']:
        sequence_change_list = request.GET['seq'].replace(" ", "").split(',')
        sequence_change_include = []
        sequence_change_exclude = []
        for sequence_change in sequence_change_list:

            if str(sequence_change).startswith("-"):
                sequence_change_exclude.append(Q(**{'sequence_change__contains': str(sequence_change)[1:]}))
            else:
                sequence_change_include.append(Q(**{'sequence_change__contains': str(sequence_change)}))

        if len(sequence_change_include) > 0:
            include_argument_list.append(reduce(operator.or_, sequence_change_include))

        if len(sequence_change_exclude) > 0:
            exclude_argument_list.append(reduce(operator.or_, sequence_change_exclude))


def _add_protein_change_to_query(request, include_argument_list, exclude_argument_list):
    if 'prot' in request.GET and request.GET['prot']:
        protein_change_list = request.GET['prot'].replace(" ", "").split(',')
        protein_change_include = []
        protein_change_exclude = []
        for protein_change in protein_change_list:
            if str(protein_change).startswith("-"):
                protein_change_exclude.append(Q(**{'protein_change__contains': str(protein_change)[1:]}))
            else:
                protein_change_include.append(Q(**{'protein_change__contains': str(protein_change)}))

        if len(protein_change_include) > 0:
            include_argument_list.append(reduce(operator.or_, protein_change_include))

        if len(protein_change_exclude) > 0:
            exclude_argument_list.append(reduce(operator.or_, protein_change_exclude))


def _get_search_ale_exp_params(request):
    ale_experiments_to_include = []
    ale_experiments_to_exclude = []
    if 'ale' in request.GET and request.GET['ale']:
        ale_experiment_list = request.GET['ale'].replace(" ", "").split(',')
        for ale_experiment in ale_experiment_list:
            if str(ale_experiment).startswith("-"):
                ale_experiments_to_exclude.append(AleExperiment.objects.get(name__contains=str(ale_experiment)[1:]).ale_id)
            else:
                ale_experiments_to_include.append(AleExperiment.objects.get(name__contains=str(ale_experiment)).ale_id)
    return ale_experiments_to_include, ale_experiments_to_exclude


def _get_mut_qryset(include_argument_list, exclude_argument_list):
    if len(include_argument_list) > 0:
        include_argument_list = reduce(operator.and_, include_argument_list)
    else: return None

    if len(exclude_argument_list) > 0:
        mut_qryset = Mutation.objects.filter(include_argument_list).exclude(
            reduce(operator.or_, exclude_argument_list))
    else:
        mut_qryset = Mutation.objects.filter(include_argument_list)

    return mut_qryset
