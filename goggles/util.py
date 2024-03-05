# talk to model, get data in JSON form

import random
import math
from .models import Projects, Experiments, Batches, MeasurementTypes, Measurements, GrowthAnalyses, \
    TemperatureMeasurements

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


def get_growth_data(measurement_type_db_ids):
    experiment_growth_rates = GrowthAnalyses.objects.using('ale_machine').filter(
        measurement_type_db_id__in=measurement_type_db_ids)
    growth_rate_dict = {}
    for rate in experiment_growth_rates:
        growth_rate_dict[rate.measurement_type_db.batch.batch_id] = rate.growth_rate
    return growth_rate_dict


def get_measurement_data(measurement_type_db_ids):
    growth_dict = get_growth_data(measurement_type_db_ids)
    # let's just do each experiment separately
    measurements = Measurements.objects.using('ale_machine').filter(
        measurement_type_db_id__in=measurement_type_db_ids)
    temperature_measurements = TemperatureMeasurements.objects.using('ale_machine').filter(measurement__in=measurements)
    # temperature measurements include measurements and batch, we can use it to pull all we need at once

    measurement_list = []
    temperature_measurements_list = []
    growth_rate_list = []
    for temp_measurement in temperature_measurements:
        current_batch = temp_measurement.measurement.measurement_type_db.batch.batch_id
        current_time = temp_measurement.time.timestamp() * 1000
        calculated_orreader_value = temp_measurement.measurement.calculated_orreader_value
        if calculated_orreader_value and calculated_orreader_value > 0:
            adc_OD_values = calculated_orreader_value
        else:
            raw_incident_value = temp_measurement.measurement.raw_incident_value
            raw_transmittance_value = temp_measurement.measurement.raw_transmittance_value
            measurement_type_short = temp_measurement.measurement.measurement_type_db.description[-1].lower()
            if temp_measurement.measurement.measurement_type_id and raw_incident_value != 0 and raw_transmittance_value != 0 and \
                    measurement_type_short == 'a':
                t = (1.0 * raw_incident_value) / (
                        1.0 * raw_transmittance_value)
                if t >= 1:
                    adc_OD_values = float(np.log10(t))
                else:
                    adc_OD_values = 0.01
            elif temp_measurement.measurement.measurement_type_id and raw_incident_value != 0 and raw_transmittance_value != 0 and \
                    measurement_type_short == 'r':
                adc_OD_values = (
                                        raw_transmittance_value / temp_measurement.measurement.empty_scattering_value) - raw_incident_value
            else:
                adc_OD_values = 0.01  # To prevent division by zero
        adc_OD_values = max(round(adc_OD_values, 3), 0.01)
        measurement_list.append(
            [current_time, adc_OD_values,
             current_batch])
        temperature_measurements_list.append(
            [current_time, temp_measurement.temperature,
             current_batch])
        growth_rate_list.append([current_time,
                                 growth_dict[current_batch],
                                 current_batch])
    return [measurement_list, growth_rate_list, temperature_measurements_list]


def get_experiment_data(experiment_id):
    batches = Batches.objects.using('ale_machine').filter(experiment=experiment_id).values("db_id")
    measurement_type_db_ids = MeasurementTypes.objects.using('ale_machine').filter(batch_id__in=batches).values("db_id")
    measurement_data = get_measurement_data(measurement_type_db_ids)
    return [measurement_data[0], measurement_data[1], measurement_data[2]]
