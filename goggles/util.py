# talk to model, get data in JSON form

import random
import math
from .models import Projects, Experiments, Batches, MeasurementTypes, Measurements, GrowthAnalyses, \
    TemperatureMeasurements, Protocol, Medias

from django.core import serializers
import numpy as np

# i don't know about you but i'm feeling
TEMPERATURE_MINIMUM = 22
TEMPERATURE_MAXIMUM = 500

ALE_MACHINES = [['UCSD 3.0', 'UCSD ONE', 'ucsd_machine_one'],
                ['UCSD 3.0a', 'UCSD TWO', 'ucsd_machine_two'],
                ['DTU 3.1', 'DTU ONE', 'dtu_machine_one'],
                ['DTU 1.0', 'DTU TWO', 'dtu_machine_two']]


def json_serialize(qs):
    qs_json = serializers.serialize('json', qs)
    return qs_json


def get_ale_machines():
    return ALE_MACHINES


def get_initial_data():
    data = {}
    for machine in ALE_MACHINES:
        id = machine[2]
        try:
            data[id] = {
                'name': machine[0],
                'codename': machine[1],
                'id': id,
                'projects': generate_projects_with_experiments(id),
            }
        except:
            continue
    return data


def generate_medias(machine):
    return Medias.objects.using(machine).all()


def generate_projects_with_experiments(machine):
    from string import ascii_lowercase as alc
    projects = {}
    experiments = generate_experiments(machine)
    all_projects = Projects.objects.using(machine).all().reverse()
    for p in all_projects:
        projects[p.db_id] = {
            'name': p.title,
            'experiments': tuple(experiments[p.db_id])
        }
    return projects


def generate_experiments(machine):
    experiments = {}
    all_protocols = Protocol.objects.using(machine).all()
    for protocol in all_protocols:
        current_experiment = protocol.experiment
        if protocol.media:
            media = protocol.media.description
        else:
            media = "N/A"
        experiment = (current_experiment.ale_id, current_experiment.description,
                      protocol.type, protocol.filter_toggle, media,
                      current_experiment.description + ',' + '#' + ''.join(
                          random.sample('0123456789ABCDEF', 6)) + ',' +
                      str(current_experiment.ale_id), current_experiment.db_id
                      )
        if current_experiment.project_id in experiments.keys():
            experiments[current_experiment.project_id].append(experiment)
        else:
            experiments[current_experiment.project_id] = [experiment]
    return experiments


def get_growth_data(ale_machine, measurement_type_db_ids):
    experiment_growth_rates = GrowthAnalyses.objects.using(ale_machine).filter(
        measurement_type_db_id__in=measurement_type_db_ids)
    growth_rate_dict = {}
    for rate in experiment_growth_rates:
        growth_rate_dict[rate.measurement_type_db.batch.batch_id] = rate.growth_rate
    return growth_rate_dict

def get_experiment_data(ale_machine, experiment_id):
    batches = Batches.objects.using(ale_machine).filter(experiment=experiment_id).values("db_id")
    measurement_type_db_ids = MeasurementTypes.objects.using(ale_machine).filter(batch_id__in=batches).values("db_id")
    growth_dict = get_growth_data(ale_machine, measurement_type_db_ids)
    temperature_measurement_ids = Experiments.objects.using(ale_machine).get(
        db_id=experiment_id).temperature_meas_ids.split(',')
    if len(temperature_measurement_ids) < 2:
        return [[], [], []]

    measurement_list = []
    temperature_measurements_list = []
    growth_rate_list = []
    prev_batch_id = -1

    temp_measurement_queryset = TemperatureMeasurements.objects.using(ale_machine).filter(
        db_id__in=temperature_measurement_ids)
    for temp_measurement in temp_measurement_queryset:
        current_batch = temp_measurement.measurement.measurement_type_db.batch
        current_media_description = current_batch.media.description
        current_batch_id = current_batch.batch_id
        current_time = temp_measurement.time.timestamp() * 1000
        calculated_orreader_value = temp_measurement.measurement.calculated_orreader_value
        if calculated_orreader_value and calculated_orreader_value > 0:
            adc_OD_values = calculated_orreader_value
        else:
            adc_OD_values = temp_measurement.measurement.OD
        adc_OD_values = max(round(adc_OD_values, 3), 0.01)
        measurement_list.append(
            [current_time, adc_OD_values,
             current_batch_id, current_media_description])
        current_temp = temp_measurement.temperature
        if current_temp > TEMPERATURE_MINIMUM and current_temp < TEMPERATURE_MAXIMUM:
            temperature_measurements_list.append(
                [current_time, current_temp,
                 current_batch_id, current_media_description])
        if current_batch_id != prev_batch_id:
            growth_rate_list.append([current_time,
                                     growth_dict[current_batch_id],
                                     current_batch_id, current_media_description])
            prev_batch_id = current_batch_id
    return [measurement_list, growth_rate_list, temperature_measurements_list]
