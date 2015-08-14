from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required

from ale.models import *
from seq.models import *


@login_required
def mutations_db_browser(request):

    reseq_experiments = ResequencingExperiment.objects.all()

    experiment_mapping = dict((o.id, o) for o in reseq_experiments)

    observed_mutations = ObservedMutation.objects.filter(sequencing_experiment_id__in=experiment_mapping.keys())

    output_str = ""

    for observed_mutation in observed_mutations:

        output_str += _build_mutation_output_str(observed_mutation) + "<br>"

    return HttpResponse(output_str)


def _build_mutation_output_str(observed_mutation):

    ale_experiment_str = observed_mutation.sequencing_experiment.isolate.flask.ale_id.ale_experiment.name
    seq_experiment_str = observed_mutation.sequencing_experiment.get_isolate_name()
    observed_mutation_str = observed_mutation.mutation.mutation_type\
                             + " " + str(observed_mutation.mutation.position)\
                             + " " + observed_mutation.mutation.sequence_change\
                             + " " + observed_mutation.mutation.gene

    output_str = ale_experiment_str\
                 + " " + seq_experiment_str\
                 + " " + observed_mutation_str

    return output_str