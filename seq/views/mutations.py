import time
from django.http import HttpResponse
from django.template import loader
from django.utils.safestring import mark_safe
from django.core.serializers.json import DjangoJSONEncoder
from django_ajax.decorators import ajax
import seq.views.common
from seq.views import mutation_table_builder
from seq.util import get_all_observed_muations_filtered, get_reseq_ordered_dict
from seq.models import ResequencingExperiment
from common.util import get_user_context
from common.constants import REFSEQ_COLUMN_IN_MUT_TABLE
from ale import permissions, models
from filter.models import AleExperimentFilter
from filter.util import get_global_filter
from aleinfo.views import show_amplifiction_data
import json
import common.constants
from logs.aledb_logger import user_extra, join_extras
import logging

__author__ = 'pphaneuf'


logger = logging.getLogger(__name__)


def amplification_data(request):
    logger.info("amplification mutation usage", user_extra(request))
    try:
        start_time = time.clock()
        context = get_user_context(request.user)
        experiment = seq.views.common.get_ale_experiment(request)

        exp_name = experiment.project.name + ": " + experiment.name
        ale_no = seq.views.common.get_ale_id(request)
        sample_type = seq.views.common.get_sample_type(request)
        aleid_ale_id_list = seq.views.common.get_aleid_ale_id_list(experiment.ale_id, True)

        ordered_reseq_dict = get_reseq_ordered_dict(experiment.ale_id, ale_no, sample_type, request)

        table_header = mutation_table_builder.get_table_header(request.user, ordered_reseq_dict, experiment)

        table_body = _get_table_body(experiment, ordered_reseq_dict, request.user, filter_type="NOT_AMP")

        hidden_columns = request.GET.get('hidden_columns', "")

        template = loader.get_template("base_table_template.html")

        context.update({"ales": aleid_ale_id_list,
                        "ale_experiment_name": exp_name,
                        "ale_no": ale_no,
                        "sample_type": sample_type,
                        "ale_experiment_id": experiment.ale_id,
                        "table_body": mark_safe(json.dumps(table_body, cls=DjangoJSONEncoder)),
                        "title": exp_name + " Mutations",
                        "table_header": table_header,
                        "template_header": "Mutations",
                        "hidden_columns": hidden_columns,
                        "refseq_column": REFSEQ_COLUMN_IN_MUT_TABLE,
                        "tag_dropdown": common.constants.TAGS
                        })
        logger.info("mutation performance",
                    extra=join_extras(user_extra(request), {"time taken": time.clock() - start_time}))

        return HttpResponse(template.render(context, request), content_type="text/html")
    except Exception as e:
        logger.exception("amplifications broke", extra=user_extra(request))
        template = loader.get_template("500.html")
        context['err_message'] = str(e)
        return HttpResponse(template.render(context, request), content_type="text/html")


def mutation_table(request):
    logger.info("mutation usage", user_extra(request))
    try:
        start_time = time.clock()
        context = get_user_context(request.user)
        experiment = seq.views.common.get_ale_experiment(request)

        exp_name = experiment.project.name + ": " + experiment.name
        ale_no = seq.views.common.get_ale_id(request)
        sample_type = seq.views.common.get_sample_type(request)
        aleid_ale_id_list = seq.views.common.get_aleid_ale_id_list(experiment.ale_id, True)

        ordered_reseq_dict = get_reseq_ordered_dict(experiment.ale_id, ale_no, sample_type, request)

        table_header = mutation_table_builder.get_table_header(request.user, ordered_reseq_dict, experiment)

        table_body = _get_table_body(experiment, ordered_reseq_dict, request.user, filter_type="AMP")

        hidden_columns = request.GET.get('hidden_columns', "")

        template = loader.get_template("base_table_template.html")

        context.update({"ales": aleid_ale_id_list,
                        "ale_experiment_name": exp_name,
                        "ale_no": ale_no,
                        "sample_type": sample_type,
                        "ale_experiment_id": experiment.ale_id,
                        "table_body": mark_safe(json.dumps(table_body, cls=DjangoJSONEncoder)),
                        "title": exp_name + " Mutations",
                        "table_header": table_header,
                        "template_header": "Mutations",
                        "hidden_columns": hidden_columns,
                        "refseq_column": REFSEQ_COLUMN_IN_MUT_TABLE,
                        "tag_dropdown": common.constants.TAGS
                        })
        logger.info("mutation performance", extra=join_extras(user_extra(request), {"time taken": time.clock() - start_time}))

        return HttpResponse(template.render(context, request), content_type="text/html")
    except Exception as e:
        logger.exception("mutations broke", extra=user_extra(request))
        template = loader.get_template("500.html")
        context['err_message'] = str(e)
        return HttpResponse(template.render(context, request), content_type="text/html")


def _get_table_body(experiment, ordered_reseq_dict, user, filter_type = None):
    obs_mutations = get_all_observed_muations_filtered(experiment.ale_id, filter_type)
    return mutation_table_builder.get_mutation_table_body(user, obs_mutations, ordered_reseq_dict, experiment)


def mutation_table(request):
    template = loader.get_template("evidence/evidence.html")
    context = get_user_context(request.user)
    return HttpResponse(template.render(context, request), content_type="text/html")


@ajax
def add_to_global_filter(request):
    if permissions.can_add_global_filter(request.user):
        mut_id = request.POST['mut_id']
        gfilter = get_global_filter()
        global_filter_ignored_mutations = gfilter.ignored_mutations + "," + mut_id
        gfilter.ignored_mutations = global_filter_ignored_mutations
        gfilter.save()
        return 'ok'
    else:
        return "User doesn't have permission to edit global filter"


@ajax
def add_to_exp_filter(request):
    try:
        mut_id = request.POST['mut_id']
        experiment_id = request.POST['experiment_id']
        experiment = models.AleExperiment.objects.get(ale_id=experiment_id)
        if not experiment:
            return "Invalid experiment id: " + experiment_id
        if permissions.can_add_experiment_filter(request.user, experiment):
            ale_exp_filter, created = AleExperimentFilter.objects.get_or_create(ale_experiment_id=experiment_id)
            ale_exp_filter.ignored_mutations = ale_exp_filter.ignored_mutations + "," + mut_id
            ale_exp_filter.save()
            return 'ok'
        else:
            return "User doesn't have permission to edit experiment filter"
    except Exception as ex:
        return ex


@ajax
def save_mut_tag(request):
    mut_id = request.POST['mut_id']
    selected_tag = request.POST.get('tag_name')
    mutation = seq.models.Mutation.objects.get(id=mut_id)
    if mutation.tags:
        tag_list = mutation.tags.split(',')
        if selected_tag in tag_list:
            tag_list.remove(selected_tag)
        else:
            tag_list.append(selected_tag)
        mutation.tags = ','.join(tag_list)
    else:
        mutation.tags = selected_tag
    mutation.save()
    return 'ok'


@ajax
def save_rep_tag(request):
    rep_id = request.POST.get('rep_id')
    replicate = models.TechnicalReplicate.objects.get(id=rep_id)
    if replicate.tags:
        selected_tag = request.POST.get('tag_name')
        tag_list = replicate.tags.split(',')
        if selected_tag in tag_list:
            tag_list.remove(selected_tag)
        else:
            tag_list.append(selected_tag)
        replicate.tags = ','.join(tag_list)
    else:
        replicate.tags = request.POST.get('tag_name')
    replicate.save()
    replicate.save()
    return 'ok'
