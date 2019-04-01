import time

from django.http import HttpResponse
from django.utils.safestring import mark_safe
from django.template import loader
from django.shortcuts import render
from seq.models import ObservedMutation
from django.db.models import Q
import operator, collections, common
from functools import reduce
from seq.views import mutation_table_builder
from ale.utils import get_user_projects, get_strains
from filter.util import filter_observed_mutations
from common.util import get_user_context
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

        if not request.GET:
            return render(request, 'search/search.html', context)

        start_time = time.clock()
        last_search = _get_last_search(request)
        context.update({"last_search": last_search})

        search_include_param_list, search_exclude_param_list, message = _get_search_params(request, user_projects)

        if len(search_include_param_list) == 0 or (message and len(message) > 0):
            context.update({'message': message})
            return render(request, 'search/search.html', context)

        hidden_columns = request.GET.get('hidden_columns', "")
        observed_mutations = _get_observed_mutations(search_include_param_list, search_exclude_param_list)
        reseq_dict = collections.OrderedDict({obs_mut.sequencing_experiment.id: obs_mut.sequencing_experiment
                                                  for obs_mut in observed_mutations})

        table_header = mutation_table_builder.get_table_header(request.user, reseq_dict)
        # obs_mut_qryset is already filtered
        table_body = mutation_table_builder.get_mutation_table_body(request.user,
                                                                    observed_mutations,
                                                                    reseq_dict)

        context.update({"table_body": mark_safe(json.dumps(table_body, cls=DjangoJSONEncoder)),
                        "title": "Search Results",
                        "table_header": mark_safe(table_header),
                        "mutation_count": len(table_body),
                        "observed_mutation_count": len(observed_mutations),
                        "tag_dropdown": common.constants.TAGS
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


def _get_observed_mutations(search_include_param_list, search_exclude_param_list):
    """
    :param request:
    :return: mutation_queryset and observed_mutation_queryset based on user request and user permission
    """
    obs_mut_qryset = _get_mut_qryset(search_include_param_list, search_exclude_param_list)
    observed_mutations = filter_observed_mutations(obs_mut_qryset)
    return observed_mutations


def _get_last_search(request):
    last_search = {}
    if request.GET['project']:
        project = int(request.GET['project'])
    else:
        project = ''
    if request.GET:
        last_search = {
            'gene': request.GET['gene'],
            'min_freq': request.GET['min_freq'],
            'max_freq': request.GET['max_freq'],
            'min_pos': request.GET['min_pos'],
            'max_pos': request.GET['max_pos'],
            'mut_type': request.GET['mut_type'],
            'project': project,
            'strain': request.GET['strain']
        }
    return last_search


def _get_search_params(request, user_projects):
    include_argument_list = []
    exclude_argument_list = []
    message = _add_position_to_query(request, include_argument_list)
    if not message:
        message = _add_freq_to_query(request, include_argument_list)
    if not message:
        has_gene = _add_genes_to_query(request, include_argument_list, exclude_argument_list)
        _add_mutation_change_to_query(request, include_argument_list)
        _add_strain_to_query(request, include_argument_list)
        has_project = _add_project_to_query(request, include_argument_list, user_projects)
        if not has_project and not has_gene:
            message = 'Please enter search criteria - genetic target or project'
    return include_argument_list, exclude_argument_list, message


def _add_genes_to_query(request, include_argument_list, exclude_argument_list):
    if 'gene' in request.GET:
        gene_list = request.GET['gene'].replace(" ", "").split(',')
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
        return True
    return False


def _add_position_to_query(request, include_argument_list):
    min, max = None, None
    try:
        if 'min_pos' in request.GET and len(request.GET['min_pos'])>0:
            min = int(request.GET['min_pos'])
        if 'max_pos' in request.GET and len(request.GET['max_pos'])>0:
            max = int(request.GET['max_pos'])
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
        if 'min_freq' in request.GET and len(request.GET['min_freq'])>0:
            min = float(request.GET['min_freq'])
        if 'max_freq' in request.GET and len(request.GET['max_freq'])>0:
            max = float(request.GET['max_freq'])
        if min and max and min > max:
            return 'Invalid frequency: min > max'
        if min:
            include_argument_list.append(Q(**{'frequency__gte': min}))
        if max:
            include_argument_list.append(Q(**{'frequency__lte': max}))
    except Exception as ex:
        return "Invalid frequency. Please enter a number!"


def _add_mutation_change_to_query(request, include_argument_list):
    mut_type = request.GET['mut_type']
    if mut_type and len(mut_type) > 0:
        include_argument_list.append(Q(mutation__mutation_type=str(mut_type).upper()))


def _add_project_to_query(request, include_argument_list, user_projects):
    """
    :param request:
    :param include_argument_list:
    :param user_projects:
    :return: True if there is project param and the project is valid, else FALSE
    """
    if request.GET['project']:
        project_id = request.GET['project']
        ok = int(project_id) in [proj.id for proj in user_projects]
        if ok:
            include_argument_list.append(Q(sequencing_experiment__tech_rep__isolate__flask__ale_id__ale_experiment__project_id=project_id))
        return ok
    elif not request.user.is_superuser:
        project_ids = [proj.id for proj in user_projects]
        include_argument_list.append(
            Q(sequencing_experiment__tech_rep__isolate__flask__ale_id__ale_experiment__project_id__in=project_ids))
    return False


def _add_strain_to_query(request, include_argument_list):
    strain = request.GET['strain']
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

