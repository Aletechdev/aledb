from django.shortcuts import render

# Create your views here.
import re
from django.http import HttpResponse
from ale.permissions import can_view_experiment
from seq.models import ObservedMutation
from common.util import get_user_context
from django.template import loader
from logs.aledb_logger import user_extra
import logging

logger = logging.getLogger(__name__)

DATA_MOUNT_LOCATION = '/data/aledata/'


def evidence(request, *args, **kwargs):
    request_details = str(request)

    logger.info("evidence request " + request_details, extra=user_extra(request))

    #evidence_location = '/data' + request.GET.get('location') #kwargs['evidence_location']
    mut_caller = request.GET.get('mut_caller')
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
    #if mut_caller == 'gatkcnvnator':
    try:
        evidence_html_breseq = open(DATA_MOUNT_LOCATION + resequencing_experiment.location + breseq_evidence_location, 'r').read
    except:
        evidence_html_breseq = ""
    
    try:
        evidence_html_gatkcnvnator = open(DATA_MOUNT_LOCATION + resequencing_experiment.gatk_location + gatk_evidence_location, 'r').read()
    except:
        evidence_html_gatkcnvnator = ""
    
    evidence_html = evidence_html_breseq + evidence_html_gatkcnvnator
    
    template = loader.get_template("evidence/evidence.html")
    context = get_user_context(request.user)
    context.update({'evidence_html': evidence_html)})

    return HttpResponse(template.render(context, request))
