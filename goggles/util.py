# talk to model, get data in JSON form

import random
import math
from .models import Projects, Experiments, Batches, MeasurementTypes, Measurements


from django.core import serializers


def json_serialize(qs):
    qs_json = serializers.serialize('json', qs)
    return qs_json


def generate_projects():
    from string import ascii_lowercase as alc
    projects = []
    for p in Projects.objects.using('ale_machine').all():
        projects.append(p.title)
    return projects


def generate_ales():
    ales = []
    for experiment in Experiments.objects.using('ale_machine').all():
        ale = [experiment.db_id, experiment.description,
               [experiment.description, '#' + ''.join(random.sample('0123456789ABCDEF', 6)), experiment.db_id]]
        ales.append(ale)
    return ales


# want to return everything at once for speed
# input a seried of experiments to grab data for
# seems to be from measuremnt> measurement_type> batch>experiment

def get_experiment_data(experiment_id):
    # let's just do each experiment separately
    batches = Batches.objects.using('ale_machine').filter(experiment=experiment_id).values("db_id")
    measurement_type_db_ids = MeasurementTypes.objects.using('ale_machine').filter(batch_id__in=batches).values("db_id")
    experiment_measurements = Measurements.objects.using('ale_machine').filter(measurement_type_db_id__in=measurement_type_db_ids)
    measurement_list = []
    for measurement in experiment_measurements:
        t_minus = (measurement.raw_incident_value*1.0)/measurement.raw_transmittance_value
        if t_minus > 0:
            measurement_list.append([measurement.time, math.log10(t_minus)])
        else:
            measurement_list.append([measurement.time, 0])

    return measurement_list
