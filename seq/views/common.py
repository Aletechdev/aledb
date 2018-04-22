import ale.common
import ale.models
import seq.models
from common.constants import REQUEST_ALE_EXPERIMENT_ID, REQUEST_ALE_ID


__author__ = 'Patrick Phaneuf'


SETTINGS_SEQUENCING_URL = "SEQUENCING_URL"

MUTATION_TYPE_LIST = ['SNP', 'SUB', 'DEL', 'INS', 'MOB', 'AMP', 'CON', 'INV', 'Unannotated']

# Don't change these names since they match with Breseq's HTML annotations and used when parsing.
FUNCTIONAL_CHANGE_TYPE_LIST = ['intergenic', 'noncoding', 'pseudogene', 'snp_type_synonymous', 'snp_type_nonsynonymous', 'Unannotated']

COLORS = ['#FF851B', '#2ECC40', '#0074D9', '#FFDC00', '#7FDBFF', '#B7337A', '#B10DC9', '#111111', '#85144b']

DEFAULT_COLOR = '#AAAAAA'


def _set_colors(length):
    temp = COLORS[:length]
    temp.append(DEFAULT_COLOR)
    return temp


GENE_COLORS = _set_colors(len(MUTATION_TYPE_LIST) - 1)
SEQ_COLORS = _set_colors(len(FUNCTIONAL_CHANGE_TYPE_LIST) - 1)

# TODO: change all instance of 'seq_experiment' to 'reseq'


def get_ales(experiment_ids, exclude_starting_strain=False):

    if experiment_ids is not None:

        experiment = ale.models.AleExperiment.objects.get(ale_id=experiment_ids)

        experiment_queryset = experiment.aleid_set.only("ale_id")

    else:

        experiment_queryset = seq.models.ResequencingExperiment.objects.all()

    if exclude_starting_strain:

        experiment_queryset = experiment_queryset.exclude(ale_id=ale.common.STARTING_STRAIN_ALE_ID)

    experiment_queryset_list = [exp.ale_id for exp in experiment_queryset]

    return experiment_queryset_list


def get_ale_id(request):
    ale_id = request.GET.get(REQUEST_ALE_ID)
    ale_id = None if ale_id is None or ale_id == "all" else int(ale_id)
    return ale_id


def get_ale_experiment_id(request):
    # Get the full list of ale experiments for the ale number of interest
    exp_id = request.GET.get(REQUEST_ALE_EXPERIMENT_ID)
    exp_id = None if exp_id is None or exp_id == "all" else int(exp_id)
    return exp_id


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
