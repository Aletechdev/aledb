from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required

from seq.models import *


@login_required
def mutations_db_browser(request):

    '''
    list_of_experiments = ResequencingExperiment.objects.all()

    for experiment in experiments:
        print(experiment.mutations)
    '''

    mutations = Mutation.objects.all()

    for mutation in mutations:
        print(mutation.mutation_type)

    return HttpResponse("mutation_db_browser")

    

    
