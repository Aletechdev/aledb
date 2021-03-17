import ale.common
import ale.models
from ale.models import AleExperiment
from ale.permissions import can_view_project
from common.constants import REQUEST_ALE_EXPERIMENT_ID, REQUEST_ALE_ID, REQUEST_SAMPLE_TYPE
from django.http import Http404, HttpResponseForbidden, HttpResponseBadRequest


__author__ = 'Patrick Phaneuf'


SETTINGS_SEQUENCING_URL = "SEQUENCING_URL"

UNANNOTATED = 'unannotated'
MUTATION_TYPE_LIST = ['SNP', 'SUB', 'DEL', 'INS', 'MOB', 'AMP', 'CON', 'INV', UNANNOTATED]

# Don't change these names since they match with Breseq's HTML annotations and used when parsing.
FUNCTIONAL_CHANGE_TYPE_LIST = ['intergenic', 'noncoding', 'pseudogene', 'nonsynonymous', 'synonymous', UNANNOTATED]

COLORS = ['#FF851B', '#2ECC40', '#0074D9', '#FFDC00', '#7FDBFF', '#B7337A', '#B10DC9', '#111111', '#85144b']

DEFAULT_COLOR = '#AAAAAA'


def _set_colors(length):
    temp = COLORS[:length]
    temp.append(DEFAULT_COLOR)
    return temp


GENE_COLORS = _set_colors(len(MUTATION_TYPE_LIST) - 1)
SEQ_COLORS = _set_colors(len(FUNCTIONAL_CHANGE_TYPE_LIST) - 1)

# TODO: change all instance of 'seq_experiment' to 'reseq'


def get_aleid_ale_id_list(experiment_id, exclude_starting_strain=False):
    if experiment_id:
        aleid_queryset = ale.models.AleId.objects.filter(ale_experiment__ale_id=experiment_id)
    else:
        aleid_queryset = ale.models.AleId.objects.all()

    if exclude_starting_strain:
        aleid_queryset = aleid_queryset.exclude(ale_id=ale.common.STARTING_STRAIN_ALE_ID)
    return aleid_queryset.values_list("ale_id", flat=True)


def get_ale_id(request):
    ale_id = request.GET.get(REQUEST_ALE_ID)
    ale_id = None if ale_id is None or ale_id == "all" else int(ale_id)
    return ale_id

def get_sample_type(request):
    sample_type = request.GET.get(REQUEST_SAMPLE_TYPE)
    if sample_type == "all":
        sample_type = None
    return sample_type

def get_ale_experiment(request):
    """
    Parse experiment id and validate permission
    :param request:
    :return: experiment or raise exception
    """
    exp_id = request.GET.get(REQUEST_ALE_EXPERIMENT_ID)
    experiment = AleExperiment.objects.get(ale_id=exp_id)
    if experiment:
        if can_view_project(request.user, experiment.project):
            return experiment
    raise ValueError("You don't have permission to view the experiment")


def get_ale_experiment_name(request):

    ale_experiment_id = request.GET.get(REQUEST_ALE_EXPERIMENT_ID)

    ale_experiment_name = "All ALE Experiments"

    if ale_experiment_id is not None and ale_experiment_id != "all":

        ale_experiment = ale.models.AleExperiment.objects.filter(ale_id=ale_experiment_id)

        # TODO: should only ever be returning 1 experiment. Implement error handling for more than one returned.
        ale_experiment_name = ale_experiment[0].name

    return ale_experiment_name


def filter_out_wt_reseq(reseq_ordered_dict):
    for key, value in reseq_ordered_dict.items():
        if value.ale_id == ale.common.STARTING_STRAIN_ALE_ID:
            del reseq_ordered_dict[key]
            break
    return reseq_ordered_dict


def get_wt_reseq_id(seq_experiment_ordered_dict):

    wt_id = None

    for key, value in seq_experiment_ordered_dict.items():

        if value.ale_id == ale.common.STARTING_STRAIN_ALE_ID:

            wt_id = key

    return wt_id
