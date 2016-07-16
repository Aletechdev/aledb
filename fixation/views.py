# TODO: All resources being pulled from seq app could possibly be stored in a common dir.

from django.http import HttpResponse

from django.contrib.auth.decorators import login_required

from django.template import Context, loader

from django.utils.safestring import mark_safe

import seq.views.common

import seq.views.mutation_table_builder

import seq.models

__author__ = 'Patrick Phaneuf'

import pprint


@login_required
def fixation(request):
    ale_experiment_name = seq.views.common.get_ale_experiment_name(request)
    ale_experiment_id = seq.views.common.get_ale_experiment_id(request)
    ale_queryset = seq.views.common.get_ales(ale_experiment_id, True)

    ale_number = seq.views.common.get_ale_id(request)

    ordered_reseq_dict = seq.views.common.get_ordered_reseq_dict(request)
    wt_id = seq.views.common.get_wt_reseq_id(ordered_reseq_dict)  # Must happen before filtering out wt reseq.
    ordered_reseq_dict = seq.views.common.filter_out_wt_reseq(ordered_reseq_dict)

    table_header = seq.views.mutation_table_builder.get_table_header(ordered_reseq_dict)

    ale_experiment_fixated_mutation_queryset = _get_experiment_fixated_mutation_queryset(ordered_reseq_dict)

    # TODO: currently pulling this from the seq app. Need to put this template in a centralized location.
    template = loader.get_template("table_template.html")

    context = Context({"ales": ale_queryset,
                       "ale_experiment_name": ale_experiment_name,
                       "ale_no": ale_number,
                       "experiment_id": ale_experiment_id,
                       "title": "Fixating Mutations",
                       "table_header": mark_safe(table_header),
                       "template_header": "Fixating Mutations"})

    return HttpResponse(template.render(context))


def _get_experiment_fixated_mutation_queryset(ordered_reseq_dict):
    ale_id_reseq_dict = _get_ale_id_reseq_dict(ordered_reseq_dict)

    ale_experiment_fixated_mutation_queryset = seq.models.Mutation.objects.none()

    for id_reseq_list in ale_id_reseq_dict.values():

        flask_observed_mutation_dict = {}
        for id_reseq_tuple in id_reseq_list:
            reseq_id = id_reseq_tuple[0]
            flask_number = id_reseq_tuple[1].flask_number
            flask_observed_mutation_dict[flask_number] = seq.views.common.get_all_observed_mutations([reseq_id])

        ale_fixated_mutation_queryset = _get_ale_fixated_mutation_queryset(flask_observed_mutation_dict)
        ale_experiment_fixated_mutation_queryset = ale_experiment_fixated_mutation_queryset | ale_fixated_mutation_queryset

    return ale_experiment_fixated_mutation_queryset


def _get_ale_fixated_mutation_queryset(flask_observed_mutation_dict):
    ordered_flask_number_list = sorted(flask_observed_mutation_dict.keys())

    first_flask_number = ordered_flask_number_list[0]
    last_flask_number = ordered_flask_number_list[-1]
    first_flask_observed_mutation_queryset = flask_observed_mutation_dict[first_flask_number]
    fixated_mutation_queryset = seq.views.common.get_mutation_queryset_from_observed_mutation_queryset(first_flask_observed_mutation_queryset)

    for flask_number in ordered_flask_number_list:
        flask_observed_mutation_queryset = flask_observed_mutation_dict[flask_number]
        flask_mutation_queryset = seq.views.common.get_mutation_queryset_from_observed_mutation_queryset(flask_observed_mutation_queryset)
        if flask_number == last_flask_number:
            fixated_mutation_queryset = _get_common_mutations(fixated_mutation_queryset, flask_mutation_queryset)
        else:
            fixated_mutation_queryset = _get_new_and_fixated_mutation_queryset(fixated_mutation_queryset, flask_mutation_queryset)

    return fixated_mutation_queryset


def _get_new_and_fixated_mutation_queryset(fixated_mutation_queryset, flask_mutation_queryset):
    new_observed_mutation_queryset = _get_combined_mutations(fixated_mutation_queryset, flask_mutation_queryset)
    new_observed_mutation_queryset = _get_common_mutations(new_observed_mutation_queryset, flask_mutation_queryset)
    return new_observed_mutation_queryset


def _get_combined_mutations(fixated_mutation_queryset, flask_mutation_queryset):
    return fixated_mutation_queryset | flask_mutation_queryset


def _get_common_mutations(fixated_mutation_queryset, flask_mutation_queryset):
    return fixated_mutation_queryset & flask_mutation_queryset


def _get_ale_id_reseq_dict(reseq_dict):
    ale_reseq_dict = {}
    for reseq_id, reseq in reseq_dict.items():
        if reseq.ale_id in ale_reseq_dict.keys():
            ale_reseq_dict[reseq.ale_id].append((reseq_id, reseq))
        else:
            ale_reseq_dict[reseq.ale_id] = [(reseq_id, reseq)]
    return ale_reseq_dict
