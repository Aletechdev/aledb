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
                'DTU 1.0', 'DTU TWO', 'dtu_machine_two']


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
                'medias': generate_medias(id)
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
    for p in Projects.objects.using(machine).all():
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
            experiment = (current_experiment.db_id, current_experiment.description,
                          protocol.type, protocol.filter_toggle, protocol.media.description,
                          current_experiment.description + ',' + '#' + ''.join(
                              random.sample('0123456789ABCDEF', 6)) + ',' +
                          str(current_experiment.db_id)
                          )
            if current_experiment.project_id in experiments.keys():
                experiments[current_experiment.project_id].append(experiment)
            else:
                experiments[current_experiment.project_id] = [experiment]
        else:
            experiment = (current_experiment.db_id, current_experiment.description,
                          protocol.type, protocol.filter_toggle, "No Media",
                          current_experiment.description + ',' + '#' + ''.join(
                              random.sample('0123456789ABCDEF', 6)) + ',' +
                          str(current_experiment.db_id)
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


def get_measurement_data(ale_machine: object, measurement_type_db_ids: object) -> object:
    growth_dict = get_growth_data(ale_machine, measurement_type_db_ids)
    # let's just do each experiment separately
    measurements = Measurements.objects.using(ale_machine).filter(
        measurement_type_db_id__in=measurement_type_db_ids)
    temperature_measurements = TemperatureMeasurements.objects.using(ale_machine).filter(measurement__in=measurements)
    # temperature measurements include measurements and batch, we can use it to pull all we need at once

    measurement_list = []
    temperature_measurements_list = []
    growth_rate_list = []
    prev_batch = -1
    for temp_measurement in temperature_measurements:
        current_batch = temp_measurement.measurement.measurement_type_db.batch.batch_id
        current_time = temp_measurement.time.timestamp() * 1000
        calculated_orreader_value = temp_measurement.measurement.calculated_orreader_value
        if calculated_orreader_value and calculated_orreader_value > 0:
            adc_OD_values = calculated_orreader_value
        else:
            adc_OD_values = temp_measurement.measurement.OD
            '''raw_incident_value = temp_measurement.measurement.raw_incident_value
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
                adc_OD_values = 0.01  # To prevent division by zero'''
        adc_OD_values = max(round(adc_OD_values, 3), 0.01)
        measurement_list.append(
            [current_time, adc_OD_values,
             current_batch])
        current_temp = temp_measurement.temperature
        if current_temp > TEMPERATURE_MINIMUM:
            temperature_measurements_list.append(
                [current_time, temp_measurement.temperature,
                 current_batch])
        if current_batch != prev_batch:
            growth_rate_list.append([current_time,
                                     growth_dict[current_batch],
                                     current_batch])
            prev_batch = current_batch
    return [measurement_list, growth_rate_list, temperature_measurements_list]


def get_experiment_data(ale_machine, experiment_id):
    batches = Batches.objects.using(ale_machine).filter(experiment=experiment_id).values("db_id")
    measurement_type_db_ids = MeasurementTypes.objects.using(ale_machine).filter(batch_id__in=batches).values("db_id")
    growth_dict = get_growth_data(ale_machine, measurement_type_db_ids)
    temperature_measurement_ids = Experiments.objects.using(ale_machine).get(db_id=experiment_id).temperature_meas_ids.split(',')
    if len(temperature_measurement_ids) < 2:
        return [[],[],[]]
    # measurement_ids = Experiments.objects.using(ale_machine).get(db_id=experiment_id).meas_ids

    measurement_list = []
    temperature_measurements_list = []
    growth_rate_list = []
    prev_batch = -1

    for temp_measurement_id in temperature_measurement_ids:
        if temp_measurement_id.isdigit():
            temp_measurement = TemperatureMeasurements.objects.using(ale_machine).get(db_id=temp_measurement_id)
            current_batch = temp_measurement.measurement.measurement_type_db.batch.batch_id
            current_time = temp_measurement.time.timestamp() * 1000
            calculated_orreader_value = temp_measurement.measurement.calculated_orreader_value
            if calculated_orreader_value and calculated_orreader_value > 0:
                adc_OD_values = calculated_orreader_value
            else:
                adc_OD_values = temp_measurement.measurement.OD
                '''raw_incident_value = temp_measurement.measurement.raw_incident_value
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
                    adc_OD_values = 0.01  # To prevent division by zero'''
            adc_OD_values = max(round(adc_OD_values, 3), 0.01)
            measurement_list.append(
                [current_time, adc_OD_values,
                 current_batch])
            current_temp = temp_measurement.temperature
            if current_temp > TEMPERATURE_MINIMUM and current_temp < TEMPERATURE_MAXIMUM:
                temperature_measurements_list.append(
                    [current_time, current_temp,
                     current_batch])
            if current_batch != prev_batch:
                growth_rate_list.append([current_time,
                                         growth_dict[current_batch],
                                         current_batch])
                prev_batch = current_batch
    return [measurement_list, growth_rate_list, temperature_measurements_list]


def get_experiment_data_old(ale_machine, experiment_id):
    batches = Batches.objects.using(ale_machine).filter(experiment=experiment_id).values("db_id")
    measurement_type_db_ids = MeasurementTypes.objects.using(ale_machine).filter(batch_id__in=batches).values("db_id")
    measurement_data = get_measurement_data(ale_machine, measurement_type_db_ids)
    return [measurement_data[0], measurement_data[1], measurement_data[2]]
