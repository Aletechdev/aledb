from django.http import HttpResponse

from django.contrib.auth.decorators import login_required

import seq.views.common

__author__ = 'Patrick Phaneuf'

import pprint
@login_required
def fixation(request):

    ale_experiment_name = seq.views.common.get_ale_experiment_name(request)
    ale_experiment_id = seq.views.common.get_ale_experiment_id(request)

    ordered_reseq_dict = seq.views.common.get_ordered_reseq_dict(request)
    wt_id = seq.views.common.get_wt_reseq_id(ordered_reseq_dict)  # Must happen before filtering out wt reseq.
    ordered_reseq_dict = seq.views.common.filter_out_wt_reseq(ordered_reseq_dict)

    ale_id_reseq_dict = _get_ale_id_reseq_dict(ordered_reseq_dict)

    # DEBUG START
    id_reseq_list = ale_id_reseq_dict[1]
    flask_observed_mutation_dict = {}
    for id_reseq_tuple in id_reseq_list:
        reseq_id = id_reseq_tuple[0]
        flask_number = id_reseq_tuple[1].flask_number
        flask_observed_mutation_dict[flask_number] = seq.views.common.get_observed_mutations([reseq_id])
    # pprint.pprint(flask_observed_mutation_dict)

    asdf = _get_ale_fixated_mutation_queryset(flask_observed_mutation_dict)

    # DEBUG END

    return HttpResponse()


def _get_ale_fixated_mutation_queryset(flask_observed_mutation_dict):

    ordered_flask_number_list = sorted(flask_observed_mutation_dict.keys())

    first_flask_number = ordered_flask_number_list[0]
    fixated_observed_mutation_queryset = flask_observed_mutation_dict[first_flask_number].all()
    for flask_number in ordered_flask_number_list:
        flask_observed_mutation_queryset = flask_observed_mutation_dict[flask_number]
        fixated_observed_mutation_queryset = fixated_observed_mutation_queryset.all() | flask_observed_mutation_queryset.all()
        fixated_observed_mutation_queryset = fixated_observed_mutation_queryset.all() & flask_observed_mutation_queryset.all()
        print()
        for a in fixated_observed_mutation_queryset:
            print(a.mutation.gene)

    return fixated_observed_mutation_queryset


def _get_fixated_mutation_queryset(current_fixated_mutation_queryset, flask_observed_mutation_queryset):
        new_fixated_observed_mutation_queryset = _get_new_mutations(current_fixated_mutation_queryset, flask_observed_mutation_queryset)
        new_fixated_observed_mutation_queryset = _remove_non_fixating_mutations(new_fixated_observed_mutation_queryset, flask_observed_mutation_queryset)
        return new_fixated_observed_mutation_queryset


def _get_new_mutations(current_fixated_mutation_queryset, flask_observed_mutation_queryset):
    return current_fixated_mutation_queryset.all() | flask_observed_mutation_queryset.all()


def _remove_non_fixating_mutations(current_fixated_mutation_queryset, flask_observed_mutation_queryset):
    return current_fixated_mutation_queryset.all() & flask_observed_mutation_queryset.all()


def _get_ale_id_reseq_dict(reseq_dict):
    ale_reseq_dict = {}
    for reseq_id, reseq in reseq_dict.items():
        if reseq.ale_id in ale_reseq_dict.keys():
            ale_reseq_dict[reseq.ale_id].append((reseq_id, reseq))
        else:
            ale_reseq_dict[reseq.ale_id] = [(reseq_id, reseq)]
    return ale_reseq_dict
