from django.shortcuts import render

# Create your views here.
import re
from django.http import HttpResponse
from ale.permissions import can_view_experiment
from seq.models import ObservedMutation
from seq.util import get_matching_observed_mutation_ids, get_all_observed_mutations_filtered, \
    get_mutations_from_observed_muations
from common.util import get_user_context
from stats.util import get_reseq_experiment_info_list
from django.template import loader
from logs.aledb_logger import user_extra
import logging

logger = logging.getLogger(__name__)

DATA_MOUNT_LOCATION = '/data/aledata/'
LINK_START_SUBSTRING = 'href="'
IMAGE_START_SUBSTRING = 'img src="'


def raw_file_serve(request):
    sample = 'sample_location'
    observed_mutation_id = request.GET.get('observed_mut_id')

    observed_mutation = ObservedMutation.objects.get(id=observed_mutation_id)


def update_breseq_html_locations(html_content, base_url):
    #it's only a breseq issue for now
    return html_content.replace(IMAGE_START_SUBSTRING, IMAGE_START_SUBSTRING + '/aledata' +  str(base_url) + 'evidence/').replace(LINK_START_SUBSTRING, LINK_START_SUBSTRING + '/aledata' + base_url + 'evidence/')


def get_neighbor_ids(current_mutation, experiment_id):
    #next_mutation_id = ObservedMutation.objects.filter(id__gt=current_mutation.id).order_by('id').first().id
    previous_mutation_id = ObservedMutation.objects.filter(id__lt=current_mutation.id).order_by('id').last().id
    list_observed_muts = get_matching_observed_mutation_ids(current_mutation.mutation.id, experiment_id)
    ind = list_observed_muts.index(current_mutation.id)
    if ind > 0:
        left_mutation_id = list_observed_muts[ind - 1]
    else:
        left_mutation_id = None
    if ind < len(list_observed_muts)-1:
        right_mutation_id = list_observed_muts[ind + 1]
    else:
        right_mutation_id = None
    next_mutation_id = get_next_mutation(current_mutation.mutation, experiment_id)
    if next_mutation_id:
        next_observed_mutation = get_matching_observed_mutation_ids(next_mutation_id, experiment_id)[0]
    else:
        next_observed_mutation = None

    neighbors = {'next': next_observed_mutation,
                 'prev': previous_mutation_id,
                 'left': left_mutation_id,
                 'right': right_mutation_id,
                 'sibling_mutation_ids': list_observed_muts,
                 'index': ind}
    return neighbors


def get_next_mutation(current_mutation, experiment_id):
    mutations = get_mutations_from_observed_muations(get_all_observed_mutations_filtered(experiment_id))
    list_muts = sorted(mutations, key=lambda x: x.position)
    ind = list_muts.index(current_mutation)
    if ind+1 == len(list_muts):
        return None
    else:
        return list_muts[ind+1].id


def evidence(request, *args, **kwargs):
    request_details = str(request)

    logger.info("evidence request " + request_details, extra=user_extra(request))

    #evidence_location = '/data' + request.GET.get('location') #kwargs['evidence_location']
    observed_mutation_id = request.GET.get('observed_mut_id')
    observed_mutation = ObservedMutation.objects.get(id=observed_mutation_id)

    breseq_evidence_location = str(observed_mutation.evidence).split('\">')[0]
    breseq_evidence_location = re.sub(r'^.*?evidence', 'evidence', breseq_evidence_location)
    gatk_evidence_location = 'evidence/' + observed_mutation.gatk_evidence
    resequencing_experiment = observed_mutation.sequencing_experiment
    sample = resequencing_experiment.sample_name
    experiment = observed_mutation.sequencing_experiment.ale_experiment
    experiment_name = experiment.name
    project = experiment.project
    project_name = project.name
    experiments_info_list = get_reseq_experiment_info_list([resequencing_experiment])
    try:
        orig_breseq_html = open(DATA_MOUNT_LOCATION + resequencing_experiment.location + breseq_evidence_location, 'r').read()
        evidence_html_breseq = update_breseq_html_locations(orig_breseq_html, '/' + str(resequencing_experiment.location))

    except:
        evidence_html_breseq = "N/A"
    
    try:
        evidence_html_gatkcnvnator = open(DATA_MOUNT_LOCATION + resequencing_experiment.gatk_location + gatk_evidence_location, 'r').read()
    except:
        evidence_html_gatkcnvnator = "N/A"
    
    template = loader.get_template("evidence/evidence.html")

    neighbor_mutation_ids = get_neighbor_ids(observed_mutation, experiment.ale_id)

    context = get_user_context(request.user)
    context.update({
        'project_name': project_name,
        'ale_experiment_name': experiment.name,
        'ale_experiment_id': experiment.ale_id,
        "ale_project_name": experiment.project.name,
        "ale_project_id": experiment.project.id,
        'sample': sample,
        'experiments_info_list': experiments_info_list,
        'evidence_html_breseq': evidence_html_breseq,
        'evidence_html_gatkcnvnator': evidence_html_gatkcnvnator,
        'mutation_id': observed_mutation.mutation.id,
        'next_mutation_id': neighbor_mutation_ids["next"],
        'prev_mutation_id': neighbor_mutation_ids["prev"],
        'left_mutation_id': neighbor_mutation_ids["left"],
        'right_mutation_id': neighbor_mutation_ids["right"],
        'sibling_mutation_ids': neighbor_mutation_ids["sibling_mutation_ids"],
        'index': neighbor_mutation_ids["index"]

    })

    return HttpResponse(template.render(context, request))
