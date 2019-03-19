import time

from django.http import HttpResponse
from django.utils.safestring import mark_safe
from django.template import loader
from django.shortcuts import render
from seq.models import ObservedMutation
from django.db.models import Q
from filter.models import GlobalFilter, AleExperimentFilter
import operator, collections
from functools import reduce
from seq.views import mutation_table_builder
from ale.utils import get_user_projects, get_strains
from common.util import check_hidden_columns_and_filters, get_user_context
from django.core.serializers.json import DjangoJSONEncoder
import json

from logs.aledb_logger import user_extra, join_extras
import logging

logger = logging.getLogger(__name__)

MUT_TYPES = ['AMP', 'CON', 'DEL', 'DUP', 'INS', 'INV', 'MOB', 'SNP', 'SUB']
STRAINS = get_strains()


def search(request):
    logger.info("search usage", extra=user_extra(request))
    try:
        context = get_user_context(request.user)
        user_projects = get_user_projects(request.user)
        context.update({"mut_types": MUT_TYPES,
                        "strains": STRAINS,
                        "projects": user_projects})
        template = loader.get_template("search/search.html")

        if not request.POST:
            return HttpResponse(template.render(context, request), content_type="text/html")

        start_time = time.clock()
        last_search = _get_last_search(request)
        context.update({"last_search": last_search})

        search_include_param_list, search_exclude_param_list, message = _get_search_params(request, user_projects)
        if message and len(message)>0:
            context.update({'message': message})
            return render(request, 'search/search.html', context)

        check_hidden_columns_and_filters(request, None)
        obs_mut_qryset = _get_obs_mut_qryset(search_include_param_list, search_exclude_param_list)
        reseq_dict, obs_mut_qryset = _get_ordered_reseq_dict(obs_mut_qryset)

        table_header = mutation_table_builder.get_table_header(request.user, reseq_dict)
        # obs_mut_qryset is already filtered
        table_body = mutation_table_builder.get_table_body(request.user,
                                                           reseq_dict,
                                                           obs_mut_qryset,
                                                           do_filter=False,
                                                           table_type=mutation_table_builder.TableType.SEARCH)

        context.update({"table_body": mark_safe(json.dumps(table_body, cls=DjangoJSONEncoder)),
                        "title": "Search Results",
                        "table_header": mark_safe(table_header),
                        "mutation_count": len(table_body),
                        "observed_mutation_count": obs_mut_qryset.count()
                        })
        logger.info("search performance", extra=join_extras(
            {"parameters": last_search},
            {"time taken": time.clock() - start_time}))
        return HttpResponse(template.render(context, request), content_type="text/html")
    except Exception as e:
        logger.exception("search broke", extra = user_extra(request))
        template = loader.get_template("500.html")
        context['err_message'] = str(e)
        return HttpResponse(template.render(context, request), content_type="text/html")


def _get_obs_mut_qryset(search_include_param_list, search_exclude_param_list):
    """
    :param request:
    :return: mutation_queryset and observed_mutation_queryset based on user request and user permission
    """
    obs_mut_qryset = _get_mut_qryset(search_include_param_list, search_exclude_param_list)
    obs_mut_qryset = _apply_filters(obs_mut_qryset)
    # obs_mut_qryset = get_filtered_observed_mutations_queryset(obs_mut_qryset, mut_queryset=mut_qryset)
    return obs_mut_qryset


def _get_ordered_reseq_dict(obs_muts_qryset):

    obs_muts_qryset = obs_muts_qryset.select_related(
        'sequencing_experiment__tech_rep__isolate__flask__ale_id__ale_experiment', 'mutation'
    ).order_by(
        'sequencing_experiment__tech_rep__isolate__flask__ale_id__ale_experiment__name',
        'sequencing_experiment__tech_rep__isolate__flask__ale_id__ale_id',
        'sequencing_experiment__tech_rep__isolate__flask__flask_number',
        'sequencing_experiment__tech_rep__isolate__isolate_number',
        'sequencing_experiment__tech_rep__tech_rep_number'
    )
    reseq_ordered_dict = collections.OrderedDict({obs_mut.sequencing_experiment.id: obs_mut.sequencing_experiment
                                                  for obs_mut in obs_muts_qryset})
    return reseq_ordered_dict, obs_muts_qryset


def _get_last_search(request):
    last_search = {
        'gene': request.POST['gene'],
        'min_freq': request.POST['min_freq'],
        'max_freq': request.POST['max_freq'],
        'min_pos': request.POST['min_pos'],
        'max_pos': request.POST['max_pos'],
        'mut_type': request.POST['mut_type'],
        'project': request.POST['project'],
        'strain': request.POST['strain']
    }
    return last_search


def _get_search_params(request, user_projects):
    include_argument_list = []
    exclude_argument_list = []

    message = _add_position_to_query(request, include_argument_list)
    if not message:
        message = _add_freq_to_query(request, include_argument_list)
    if not message:
        _add_genes_to_query(request, include_argument_list, exclude_argument_list)
        _add_mutation_change_to_query(request, include_argument_list)
        _add_project_to_query(request, include_argument_list, user_projects)
        _add_strain_to_query(request, include_argument_list)

    if len(include_argument_list) == 0:
        message = 'Please enter search criteria'
    return include_argument_list, exclude_argument_list, message


def _add_genes_to_query(request, include_argument_list, exclude_argument_list):
    if 'gene' in request.POST:
        gene_list = request.POST['gene'].replace(" ", "").split(',')

        for mutated_gene in gene_list:
            if mutated_gene == '':
                continue
            if str(mutated_gene).startswith("-"):
                if str(mutated_gene).endswith("*"):
                    exclude_argument_list.append(Q(**{'mutation__gene__startswith': str(mutated_gene)[1:-1]}))

                elif str(mutated_gene)[1:].startswith("*"):
                    exclude_argument_list.append(Q(**{'mutation__gene__endswith': str(mutated_gene)[2:]}))

                else:
                    exclude_argument_list.append(Q(**{'mutation__gene__contains': str(mutated_gene)[1:]}))
            else:
                if str(mutated_gene).endswith("*"):
                    include_argument_list.append(Q(**{'mutation__gene__startswith': str(mutated_gene)[:-1]}))

                elif str(mutated_gene).startswith("*"):
                    include_argument_list.append(Q(**{'mutation__gene__endswith': str(mutated_gene)[1:]}))

                else:
                    include_argument_list.append(Q(**{'mutation__gene__contains': str(mutated_gene)}))


def _add_position_to_query(request, include_argument_list):
    min, max = None, None
    try:
        if 'min_pos' in request.POST and len(request.POST['min_pos'])>0:
            min = int(request.POST['min_pos'])
        if 'max_pos' in request.POST and len(request.POST['max_pos'])>0:
            max = int(request.POST['max_pos'])
        if min and max and min > max:
            return 'Invalid position: min > max'
        if min:
            include_argument_list.append(Q(**{'mutation__position__gte': min}))
        if max:
            include_argument_list.append(Q(**{'mutation__position__lte': max}))
    except Exception as ex:
        return "Invalid positions. Please enter an integer!"


def _add_freq_to_query(request, include_argument_list):
    min, max = None, None
    try:
        if 'min_freq' in request.POST and len(request.POST['min_freq'])>0:
            min = float(request.POST['min_freq'])
        if 'max_freq' in request.POST and len(request.POST['max_freq'])>0:
            max = float(request.POST['max_freq'])
        if min and max and min > max:
            return 'Invalid frequency: min > max'
        if min:
            include_argument_list.append(Q(**{'frequency__gte': min}))
        if max:
            include_argument_list.append(Q(**{'frequency__lte': max}))
    except Exception as ex:
        return "Invalid frequency. Please enter a number!"


def _add_mutation_change_to_query(request, include_argument_list):
    mut_type = request.POST['mut_type']
    if mut_type and len(mut_type) > 0:
        include_argument_list.append(Q(mutation__mutation_type=str(mut_type).upper()))


def _add_project_to_query(request, include_argument_list, user_projects):
    if request.POST['project']:
        project_id = request.POST['project']
        include_argument_list.append(Q(sequencing_experiment__tech_rep__isolate__flask__ale_id__ale_experiment__project_id=project_id))
    elif not request.user.is_superuser:
        project_ids = [proj.id for proj in user_projects]
        include_argument_list.append(
            Q(sequencing_experiment__tech_rep__isolate__flask__ale_id__ale_experiment__project_id__in=project_ids))


def _add_strain_to_query(request, include_argument_list):
    strain = request.POST['strain']
    if strain and len(strain) > 0:
        include_argument_list.append(Q(sequencing_experiment__tech_rep__isolate__flask__ale_id__strain=strain))


def _get_mut_qryset(include_argument_list, exclude_argument_list):
    include_argument_list = reduce(operator.and_, include_argument_list)
    if len(exclude_argument_list) > 0:
        exclude_argument_list = reduce(operator.or_, exclude_argument_list)
        mut_qryset = ObservedMutation.objects.filter(include_argument_list).exclude(exclude_argument_list)
    else:
        mut_qryset = ObservedMutation.objects.filter(include_argument_list)

    return mut_qryset


def _apply_filters(observed_mutation_queryset):
    query_filters = _get_global_filters()
    _get_experiment_filters(observed_mutation_queryset, query_filters)
    observed_mutation_queryset.exclude(query_filters)
    return observed_mutation_queryset


def _get_global_filters():
    filters = GlobalFilter.objects.all()
    ignored_genes = []
    ignored_mutations = []
    q_queris = Q()
    for f in filters:
        if f.ignored_genes:
            ignored_genes = ignored_genes + f.ignored_genes.split(',')
        if f.ignored_mutations:
            ignored_mutations = ignored_mutations + f.ignored_mutations.split(',')
    for ignored_gene in ignored_genes:
        if len(ignored_genes) > 0:
            q_queris.add(Q(mutation__gene__contains=ignored_gene), Q.OR)
    q_queris.add(Q(mutation__id__in=ignored_mutations), Q.OR)
    return q_queris


def _get_experiment_filters(observed_mutation_queryset, query_filters):
    exp_filters = AleExperimentFilter.objects.filter(ale_experiment_id__in=observed_mutation_queryset.values(
        "sequencing_experiment__tech_rep__isolate__flask__ale_id__ale_experiment_id"))

    for exp_filter in exp_filters:
        q_queries = Q(
            sequencing_experiment__tech_rep__isolate__flask__ale_id__ale_experiment__ale_id=exp_filter.ale_experiment_id)
        q_filters = Q()
        if exp_filter.min_cutoff and exp_filter.min_cutoff > 0:
            q_filters.add(Q(frequency__lt=exp_filter.min_cutoff / 100), Q.OR)
        if exp_filter.max_cutoff and exp_filter.max_cutoff < 100:
            q_filters.add(Q(frequency__gt=exp_filter.max_cutoff / 100), Q.OR)

        ignored_mutations = []
        if exp_filter.ignored_mutations and len(exp_filter.ignored_mutations) > 0:
            ignored_mutations += exp_filter.ignored_mutations.split(',')
        if exp_filter.starting_strain_mutations and len(exp_filter.starting_strain_mutations) > 0:
            ignored_mutations += exp_filter.starting_strain_mutations.split(',')
        ignored_mutations = _clean_mut_list(ignored_mutations)
        if len(ignored_mutations) > 0:
            q_filters.add(Q(mutation__id__in=ignored_mutations), Q.OR)
        if exp_filter.ignored_genes and len(exp_filter.ignored_genes) > 0:
            ignored_genes = exp_filter.ignored_genes.split(',')
            for ignored_gene in ignored_genes:
                if len(ignored_genes) > 0:
                    q_filters.add(Q(mutation__gene__contains=ignored_gene), Q.OR)
        q_queries.add(q_filters, Q.AND)
        query_filters.add(q_queries, Q.OR)

    return query_filters


def _clean_mut_list(mut_id_list):
    return [mut_id for mut_id in mut_id_list if len(mut_id)>0]
