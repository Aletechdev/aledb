# talk to model, get data in JSON form

import random
import math
from .models import Projects, Experiments, Batches, MeasurementTypes, Measurements, GrowthAnalyses

from django.core import serializers
import numpy as np


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


def get_OD_data(measurement_type_db_ids):
    # let's just do each experiment separately
    experiment_measurements = Measurements.objects.using('ale_machine').filter(
        measurement_type_db_id__in=measurement_type_db_ids)
    measurement_list = []
    for measurement in experiment_measurements:
        if measurement.calculated_orreader_value and measurement.calculated_orreader_value > 0:
            adc_OD_values = measurement.calculated_orreader_value
        else:
            if measurement.measurement_type_id and measurement.raw_incident_value != 0 and measurement.raw_transmittance_value != 0 and \
                    measurement.measurement_type_db.description[-1].lower() == 'a':
                t = (1.0 * measurement.raw_incident_value) / (1.0 * measurement.raw_transmittance_value)
                if t >= 1:
                    adc_OD_values = float(np.log10(t))
                else:
                    adc_OD_values = 0.01
            elif measurement.measurement_type_id and measurement.raw_incident_value != 0 and measurement.raw_transmittance_value != 0 and \
                    measurement.measurement_type_db.description[-1].lower() == 'r':
                adc_OD_values = (
                                        measurement.raw_transmittance_value / measurement.empty_scattering_value) - measurement.raw_incident_value
            else:
                adc_OD_values = 0.01  # To prevent division by zero
        adc_OD_values = max(round(adc_OD_values, 3), 0.01)
        measurement_list.append([measurement.time, adc_OD_values])

    return measurement_list


def get_growth_data(measurement_type_db_ids):
    experiment_growth_rates = GrowthAnalyses.objects.using('ale_machine').filter(
        measurement_type_db_id__in=measurement_type_db_ids)
    growth_rate_list = []
    for rate in experiment_growth_rates:
        growth_rate_list.append([rate.measurement_type_db.batch.batch_id, rate.growth_rate])
    return growth_rate_list


def get_experiment_data(experiment_id):
    batches = Batches.objects.using('ale_machine').filter(experiment=experiment_id).values("db_id")
    measurement_type_db_ids = MeasurementTypes.objects.using('ale_machine').filter(batch_id__in=batches).values("db_id")

    return [get_OD_data(measurement_type_db_ids), get_growth_data(measurement_type_db_ids)]
