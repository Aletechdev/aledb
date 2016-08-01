# TODO: All resources being pulled from seq app could possibly be stored in a common dir.

from django.http import HttpResponse

from django.contrib.auth.decorators import login_required

from django.template import Context, loader

from django.utils.safestring import mark_safe

import seq.views.common

import seq.views.mutation_table_builder

import seq.models

from filter import mutation_filter

__author__ = 'Patrick Phaneuf'

REQUEST_ASCENDING_FREQ_FILTER = 'asndflt'


# TODO: very similar to common_mutations page workflow. Should consolidate somehow.
@login_required
def fixation(request):
    ale_experiment_name = seq.views.common.get_ale_experiment_name(request)
    ale_experiment_id = seq.views.common.get_ale_experiment_id(request)
    ale_number = seq.views.common.get_ale_number(request)
    ale_queryset = seq.views.common.get_ales(ale_experiment_id, True)
    is_ascending_freq_filter = _is_ascending_freq_filter(request)

    # TODO: shouldn't have to include param 'include_starting_strain=True', since this is intended to default to
    # False for pages such as this, where we don't want to see the wild type, though we currently must include it
    # so as to filter out the mutations when choosing specific ALEs within the experiment. This means that there is
    # a disconnect between filtering methodologies that needs to be reconciled.
    ordered_reseq_dict = seq.views.common.get_ordered_reseq_dict(request, include_starting_strain=True)

    wt_id = seq.views.common.get_wt_reseq_id(ordered_reseq_dict)  # Must happen before filtering out wt reseq.
    ordered_reseq_dict = seq.views.common.filter_out_wt_reseq(ordered_reseq_dict)
    ordered_reseq_dict = seq.views.mutation_table_builder.filter_checked_flasks(request, ordered_reseq_dict)

    table_header = seq.views.mutation_table_builder.get_table_header(ordered_reseq_dict)

    filter_settings = mutation_filter.get_filter_settings(ale_experiment_id)

    ref_strain_mutation_list = seq.views.common.get_all_observed_mutations([wt_id])
    ref_strain_mutation_id_list = [observed_mutation.mutation.id for observed_mutation in ref_strain_mutation_list]

    observed_mutation_queryset = _get_experiment_fixating_observed_mutation_queryset(ordered_reseq_dict, is_ascending_freq_filter)

    table_body = seq.views.mutation_table_builder.get_table_body(ordered_reseq_dict,
                                                                 observed_mutation_queryset,
                                                                 filter_settings,
                                                                 ref_strain_mutation_id_list)

    # TODO: currently pulling this from the seq app. Need to put this template in a centralized location.
    template = loader.get_template("table_template.html")

    context = Context({"ales": ale_queryset,
                       "ale_experiment_name": ale_experiment_name,
                       "ale_no": ale_number,
                       "experiment_id": ale_experiment_id,
                       "table_body": mark_safe(table_body),
                       "title": "Fixating Mutations",
                       "table_header": mark_safe(table_header),
                       "is_ascending_freq_filter": is_ascending_freq_filter,
                       "template_header": "Fixating Mutations"})

    return HttpResponse(template.render(context))


def _is_ascending_freq_filter(request):

    ret_val = False

    if request.GET.get(REQUEST_ASCENDING_FREQ_FILTER) is not None:
        ret_val = True

    return ret_val


def _get_experiment_fixating_observed_mutation_queryset(ordered_reseq_dict, is_only_ascending=False):

    fixating_mutation_queryset = _get_experiment_fixated_mutation_queryset(ordered_reseq_dict)

    fixating_observed_mutation_queryset = _get_fixating_observed_mutation_queryset(fixating_mutation_queryset, ordered_reseq_dict.keys())

    if is_only_ascending:
        fixating_observed_mutation_queryset = _filter_for_ascending_freq(fixating_observed_mutation_queryset)

    return fixating_observed_mutation_queryset


def _filter_for_ascending_freq(fixating_observed_mutation_queryset):

    fixated_mutation_freq_dict = {}
    for observed_mutation in fixating_observed_mutation_queryset:
        mutation_id = observed_mutation.mutation.id
        if mutation_id in fixated_mutation_freq_dict.keys():
            fixated_mutation_freq_dict[mutation_id].append(observed_mutation)
        else:
            fixated_mutation_freq_dict[mutation_id] = [observed_mutation]

    mutation_id_exclude_list = _get_descending_freq_mutation_id_list(fixated_mutation_freq_dict)

    fixating_observed_mutation_queryset = fixating_observed_mutation_queryset.exclude(mutation_id__in=mutation_id_exclude_list)

    return fixating_observed_mutation_queryset


# TODO: this can be unit tested.
def _get_descending_freq_mutation_id_list(fixated_mutation_freq_dict):
    mutation_id_exclude_list = []

    for mutation_id, observed_mutation_list in fixated_mutation_freq_dict.items():

        observed_mutation_list = _filter_mutations_from_same_flask(observed_mutation_list)

        observed_mutation_list.sort(key=lambda x: x.sequencing_experiment.flask_number)

        current_observed_mutation_frequency = 0
        for observed_mutation in observed_mutation_list:
            if observed_mutation.frequency >= current_observed_mutation_frequency:
                current_observed_mutation_frequency = observed_mutation.frequency
            else:
                mutation_id_exclude_list.append(mutation_id)
                break

    return mutation_id_exclude_list


# TODO: this can be unit tested.
def _filter_mutations_from_same_flask(observed_mutation_list):

    filtered_observed_mutation_list = []

    same_flask_observed_mutation_dict = {}
    for observed_mutation_idx in range(len(observed_mutation_list)):
        flask_number = observed_mutation_list[observed_mutation_idx].sequencing_experiment.flask_number
        if flask_number in same_flask_observed_mutation_dict.keys():
            same_flask_observed_mutation_dict[flask_number].append(observed_mutation_idx)
        else:
            same_flask_observed_mutation_dict[flask_number] = [observed_mutation_idx]

    for observed_mutation_idx_list in same_flask_observed_mutation_dict.values():

        if len(observed_mutation_idx_list) == 1:
            observed_mutation_idx = observed_mutation_idx_list[0]
            filtered_observed_mutation_list.append(observed_mutation_list[observed_mutation_idx])
        else:
            max_freq_idx = observed_mutation_idx_list[0]  # Default
            max_freq = 0
            for observed_mutation_idx in observed_mutation_idx_list:
                current_freq = observed_mutation_list[observed_mutation_idx].frequency
                if current_freq > max_freq:
                    max_freq = current_freq
                    max_freq_idx = observed_mutation_idx
            filtered_observed_mutation_list.append(observed_mutation_list[max_freq_idx])

    return filtered_observed_mutation_list


def _get_fixating_observed_mutation_queryset(fixating_mutation_queryset, reseq_id_list):
    fixating_mutation_id_list = [fixating_mutation.id for fixating_mutation in fixating_mutation_queryset]
    all_observed_mutation_queryset = seq.models.ObservedMutation.objects.filter(sequencing_experiment_id__in=reseq_id_list)
    fixating_observed_mutation_queryset = all_observed_mutation_queryset.filter(mutation_id__in=fixating_mutation_id_list)

    return fixating_observed_mutation_queryset


def _get_experiment_fixated_mutation_queryset(ordered_reseq_dict):

    ale_id_reseq_dict = _get_ale_id_reseq_dict(ordered_reseq_dict)

    ale_experiment_fixated_mutation_queryset = seq.models.Mutation.objects.none()

    for id_reseq_list in ale_id_reseq_dict.values():

        flask_isolate_mutation_dict = {}
        for id_reseq_tuple in id_reseq_list:
            reseq_id = id_reseq_tuple[0]
            flask_number = id_reseq_tuple[1].flask_number
            isolate_number = id_reseq_tuple[1].isolate.isolate_number

            observed_mutation_queryset = seq.views.common.get_all_observed_mutations([reseq_id])
            mutation_queryset = seq.views.common.get_mutation_queryset_from_observed_mutation_queryset(observed_mutation_queryset)
            flask_isolate_mutation_dict[(flask_number, isolate_number)] = mutation_queryset

        flask_mutation_dict = _get_flask_mutation_dict(flask_isolate_mutation_dict)

        ale_fixated_mutation_queryset = _get_ale_fixated_mutation_queryset(flask_mutation_dict)
        ale_experiment_fixated_mutation_queryset = ale_experiment_fixated_mutation_queryset | ale_fixated_mutation_queryset

    return ale_experiment_fixated_mutation_queryset


# Combines all of the isolate mutations of one flask into a single queryset representing the mutations of the flask.
def _get_flask_mutation_dict(flask_isolate_mutation_dict):
    flask_mutation_dict = {}

    for flask_isolate_id, mutation_queryset in flask_isolate_mutation_dict.items():

        flask_id = flask_isolate_id[0]
        if flask_id not in flask_mutation_dict.keys():
            flask_mutation_dict[flask_id] = mutation_queryset
        else:
            flask_mutation_dict[flask_id] = flask_mutation_dict[flask_id] | mutation_queryset

    return flask_mutation_dict


def _get_ale_fixated_mutation_queryset(flask_mutation_dict):

    ordered_flask_number_list = sorted(flask_mutation_dict.keys())

    first_flask_number = ordered_flask_number_list[0]
    last_flask_number = ordered_flask_number_list[-1]

    fixated_mutation_queryset = flask_mutation_dict[first_flask_number]

    for flask_number in ordered_flask_number_list:

        flask_mutation_queryset = flask_mutation_dict[flask_number]

        if flask_number == last_flask_number:
            fixated_mutation_queryset = _get_common_mutations(fixated_mutation_queryset, flask_mutation_queryset)
        else:
            fixated_mutation_queryset = _get_new_and_fixated_mutation_queryset(fixated_mutation_queryset, flask_mutation_queryset)

    return fixated_mutation_queryset


def _get_new_and_fixated_mutation_queryset(fixated_mutation_queryset, flask_mutation_queryset):
    new_mutation_queryset = _get_combined_mutations(fixated_mutation_queryset, flask_mutation_queryset)
    new_mutation_queryset = _get_common_mutations(new_mutation_queryset, flask_mutation_queryset)
    return new_mutation_queryset


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
