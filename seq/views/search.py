from django.http import HttpResponse

from django.utils.safestring import mark_safe

from django.contrib.auth.decorators import login_required

from django.template import loader

from django.shortcuts import render

import seq.models

import seq.views.common

from ale.models import AleExperiment

from django.db.models import Q

import operator

from functools import reduce

from seq.views import mutation_table_builder

from common.db_util import get_all_ale_experiments, get_recent_experiments

from common.util import check_hidden_columns_and_filters

from django.core.serializers.json import DjangoJSONEncoder

import json


@login_required
def search(request):

    error = False

    check_hidden_columns_and_filters(request, None)

    if 'q' in request.GET:

        gene_query = request.GET['q']

        if _is_query_empty(gene_query):

            error = True

        else:

            reseq_dict, observed_mutations_with_gene_queryset = _get_seq_exp(request)

            if reseq_dict is None or observed_mutations_with_gene_queryset is None:
                return render(request, 'search.html', {'error': True})

            table_header = mutation_table_builder.get_table_header(reseq_dict)

            table_body = mutation_table_builder.get_table_body(reseq_dict,
                                                               observed_mutations_with_gene_queryset,
                                                               table_type=mutation_table_builder.TableType.SEARCH)

            last_search = _get_last_search(request)

            template = loader.get_template("search.html")

            context = {"table_body": mark_safe(json.dumps(table_body, cls=DjangoJSONEncoder)),
                       "title": "Search Results",
                       "table_header": mark_safe(table_header),
                       "last_search": last_search,
                       "experiments": get_all_ale_experiments(),
                       "recent_experiments": get_recent_experiments()}

            return HttpResponse(template.render(context))

    return render(request, 'search.html', {'error': error,
                                           "experiments": get_all_ale_experiments(),
                                           "recent_experiments": get_recent_experiments()})


def _is_query_empty(query):

    is_query_empty = False

    if not query:

        is_query_empty = True

    return is_query_empty


# TODO: Refactor. seq.views.common.py probably also need to be refactored along with this.
def _get_seq_exp(request):

    include_argument_list, exclude_argument_list = _get_search_query_arguments(request)

    ale_experiments_to_include, ale_experiments_to_exclude = _get_ale_experiment_arguments(request)

    mutations_with_gene_queryset = _get_django_search_query(include_argument_list, exclude_argument_list)

    observed_mutation_queryset = seq.models.ObservedMutation.objects.filter(mutation__in=mutations_with_gene_queryset)

    if ale_experiments_to_exclude:
        observed_mutation_queryset = observed_mutation_queryset.exclude(
            sequencing_experiment__tech_rep__isolate__flask__ale_id__ale_experiment__ale_id__in=ale_experiments_to_exclude)

    if ale_experiments_to_include:
        observed_mutation_queryset = observed_mutation_queryset.filter(
            sequencing_experiment__tech_rep__isolate__flask__ale_id__ale_experiment__ale_id__in=ale_experiments_to_include)

    reseq_dict = {}

    for observed_mutation in observed_mutation_queryset:

            reseq_dict[observed_mutation.sequencing_experiment.id] = observed_mutation.sequencing_experiment

    return reseq_dict, observed_mutation_queryset


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


def _get_search_query_arguments(request):

    include_argument_list = []
    exclude_argument_list = []

    _add_genes_to_query(request, include_argument_list, exclude_argument_list)

    _add_min_and_max_to_query(request, include_argument_list)

    _add_mutation_change_to_query(request, include_argument_list, exclude_argument_list)

    _add_sequence_change_to_query(request, include_argument_list, exclude_argument_list)

    _add_protein_change_to_query(request, include_argument_list, exclude_argument_list)

    return include_argument_list, exclude_argument_list


def _add_genes_to_query(request, include_argument_list, exclude_argument_list):
    if request.GET['q']:

        gene_list = request.GET['q'].replace(" ", "").split(',')

        for mutated_gene in gene_list:
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
    if request.GET['min']:
        include_argument_list.append(Q(**{'position__gte': request.GET['min']}))

    if request.GET['max']:
        include_argument_list.append(Q(**{'position__lte': request.GET['max']}))


def _add_mutation_change_to_query(request, include_argument_list, exclude_argument_list):
    if request.GET['mut']:
        mutation_type_list = request.GET['mut'].replace(" ", "").split(',')
        for mutation in mutation_type_list:
            if str(mutation).startswith("-"):
                exclude_argument_list.append(Q(**{'mutation_type': str(mutation)[1:].upper()}))
            else:
                include_argument_list.append(Q(**{'mutation_type': str(mutation).upper()}))


def _add_sequence_change_to_query(request, include_argument_list, exclude_argument_list):
    if request.GET['seq']:
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
    if request.GET['prot']:
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


def _get_ale_experiment_arguments(request):
    ale_experiments_to_include = []
    ale_experiments_to_exclude = []
    if request.GET['ale']:
        ale_experiment_list = request.GET['ale'].replace(" ", "").split(',')
        for ale_experiment in ale_experiment_list:
            if str(ale_experiment).startswith("-"):
                ale_experiments_to_exclude.append(AleExperiment.objects.get(name__contains=str(ale_experiment)[1:]).ale_id)
            else:
                ale_experiments_to_include.append(AleExperiment.objects.get(name__contains=str(ale_experiment)).ale_id)
    return ale_experiments_to_include, ale_experiments_to_exclude


def _get_django_search_query(include_argument_list, exclude_argument_list):
    if len(include_argument_list) > 0:
        include_argument_list = reduce(operator.and_, include_argument_list)
    else:
        return None

    if len(exclude_argument_list) > 0:
        mutations_with_gene_queryset = seq.models.Mutation.objects.filter(include_argument_list).exclude(
            reduce(operator.or_, exclude_argument_list))
    else:
        mutations_with_gene_queryset = seq.models.Mutation.objects.filter(include_argument_list)

    return mutations_with_gene_queryset
