# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models

import numpy as np

class Adps(models.Model):
    db_id = models.AutoField(primary_key=True)
    port = models.CharField(max_length=50)
    timeout = models.IntegerField(blank=True, null=True)
    baud = models.IntegerField()
    tip_currently_on = models.IntegerField(blank=True, null=True)
    tip_max_volume = models.FloatField()
    tip_current_volume = models.FloatField()
    plunger_position_max = models.IntegerField()
    plunger_position_min = models.IntegerField()
    plunger_position = models.IntegerField()
    machine = models.ForeignKey('Machines', models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'adps'


class Ale(models.Model):
    db = models.OneToOneField('Protocol', models.DO_NOTHING, primary_key=True)
    pass_volume = models.IntegerField()
    pass_od = models.FloatField()
    pass_od_accuracy = models.FloatField()
    inoculation_volume = models.IntegerField()
    number_of_measurements = models.IntegerField()
    max_failed_pass_attempts = models.IntegerField()
    max_wait_time = models.FloatField()
    min_accurate_od = models.FloatField()
    low_passage_volume_cutoff = models.IntegerField()
    max_growth_rate_increase = models.FloatField()
    max_number_of_rejections = models.IntegerField()
    measurement_type = models.CharField(max_length=50)
    sampling_delay = models.FloatField()
    maximum_batch_duration = models.FloatField()
    media_index = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'ale'


class AleMediaAssoc(models.Model):
    ale = models.ForeignKey(Ale, models.DO_NOTHING, blank=True, null=True)
    media = models.ForeignKey('Medias', models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'ale_media_assoc'


class Batches(models.Model):
    db_id = models.AutoField(primary_key=True)
    batch_id = models.IntegerField(blank=True, null=True)
    status = models.CharField(max_length=50)
    media = models.ForeignKey('Medias', models.DO_NOTHING, blank=True, null=True)
    cryostock = models.IntegerField()
    pcrcheck = models.CharField(db_column='PCRcheck', max_length=50)  # Field name made lowercase.
    experiment = models.ForeignKey('Experiments', models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'batches'


class BlankValues(models.Model):
    db_id = models.AutoField(primary_key=True)
    absorbance_580_blank = models.IntegerField()
    absorbance_640_blank = models.IntegerField()
    absorbance_480_blank = models.IntegerField()
    absorbance_620_blank = models.IntegerField()
    scattering_580_blank = models.IntegerField()
    scattering_640_blank = models.IntegerField()
    scattering_480_blank = models.IntegerField()
    scattering_620_blank = models.IntegerField()
    batch = models.ForeignKey(Batches, models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'blank_values'


class Cavropumps(models.Model):
    db_id = models.AutoField(primary_key=True)
    address = models.IntegerField()
    broadcast_address = models.IntegerField()
    syringe_volume_ml = models.FloatField()
    increments_per_stroke = models.IntegerField()
    speed_scale = models.FloatField()
    top_speed = models.IntegerField()
    dead_volume = models.IntegerField()
    total_valve_positions = models.IntegerField()
    slope_code = models.IntegerField()
    wait_timeout = models.FloatField()
    debug_log_directory = models.CharField(max_length=200)
    debug = models.IntegerField()
    batch_command = models.CharField(max_length=200)
    batch_mode = models.IntegerField()
    sequence = models.IntegerField()
    machine = models.ForeignKey('Machines', models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'cavropumps'


class Characterization(models.Model):
    db = models.OneToOneField('Protocol', models.DO_NOTHING, primary_key=True)
    pass_volume = models.IntegerField()
    inoculation_volume = models.IntegerField()
    sampling_delay = models.IntegerField()
    pass_od = models.FloatField()
    pass_od_accuracy = models.FloatField()
    max_batch_count = models.IntegerField()
    media = models.ForeignKey('Medias', models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'characterization'


class ControllerInteractions(models.Model):
    db_id = models.AutoField(primary_key=True)
    status = models.CharField(max_length=50, blank=True, null=True)
    controller_db = models.ForeignKey('Controllers', models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'controller_interactions'


class Controllers(models.Model):
    db_id = models.AutoField(primary_key=True)
    start_time = models.DateTimeField()
    stop = models.IntegerField(blank=True, null=True)
    replace_reader_plate = models.IntegerField(blank=True, null=True)
    exit_status = models.CharField(max_length=50, blank=True, null=True)
    machine = models.ForeignKey('Machines', models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'controllers'


class CurrentBatches(models.Model):
    test_tale = models.ForeignKey('TestTale', models.DO_NOTHING, blank=True, null=True)
    batch = models.ForeignKey(Batches, models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'current_batches'


class Experiments(models.Model):
    db_id = models.AutoField(primary_key=True)
    ale_id = models.IntegerField()
    description = models.CharField(max_length=100)
    position = models.IntegerField()
    status = models.IntegerField()
    pre_culture_position = models.IntegerField(blank=True, null=True)
    pre_culture_inoculation_volume = models.IntegerField(blank=True, null=True)
    starting_growth_rate = models.FloatField()
    project = models.ForeignKey('Projects', models.DO_NOTHING, blank=True, null=True)
    controller = models.ForeignKey(Controllers, models.DO_NOTHING, blank=True, null=True)
    measurement_type_string = models.CharField(max_length=50)
    primary_measurement_type_id = models.CharField(max_length=50)
    temperature = models.IntegerField()
    stirring_rate = models.IntegerField()
    aspirate_stir_speed = models.IntegerField(blank=True, null=True)
    coupling_stir_speed = models.IntegerField(blank=True, null=True)
    stir_power = models.IntegerField(blank=True, null=True)
    meas_ids = models.TextField()
    temperature_meas_ids = models.TextField()

    class Meta:
        managed = False
        db_table = 'experiments'


class FilterPlatePositions(models.Model):
    db_id = models.AutoField(primary_key=True)
    position_id = models.IntegerField()
    status = models.CharField(max_length=20, blank=True, null=True)
    time = models.DateTimeField(blank=True, null=True)
    experiment_id = models.IntegerField(blank=True, null=True)
    batch_id = models.IntegerField(blank=True, null=True)
    measurement_id = models.IntegerField(blank=True, null=True)
    description = models.CharField(max_length=100, blank=True, null=True)
    filter_plate = models.ForeignKey('FilterPlates', models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'filter_plate_positions'


class FilterPlates(models.Model):
    db_id = models.AutoField(primary_key=True)
    columns = models.IntegerField(blank=True, null=True)
    rows = models.IntegerField(blank=True, null=True)
    completed = models.IntegerField(blank=True, null=True)
    plate_location = models.IntegerField(blank=True, null=True)
    plate_num = models.IntegerField(blank=True, null=True)
    filter_controller = models.ForeignKey('FiltrationControllers', models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'filter_plates'


class FiltrationControllers(models.Model):
    db_id = models.AutoField(primary_key=True)
    default_columns = models.IntegerField(blank=True, null=True)
    default_rows = models.IntegerField(blank=True, null=True)
    active_plate_id = models.IntegerField(blank=True, null=True)
    machine = models.ForeignKey('Machines', models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'filtration_controllers'


class GrowthAnalyses(models.Model):
    db_id = models.AutoField(primary_key=True)
    growth_rate = models.FloatField(blank=True, null=True)
    quality_score = models.IntegerField(blank=True, null=True)
    stationary_phase_od = models.FloatField(blank=True, null=True)
    stationary_phase_start = models.FloatField(blank=True, null=True)
    stationary_phase_length = models.FloatField(blank=True, null=True)
    lag_phase_od = models.FloatField(blank=True, null=True)
    lag_phase_end = models.FloatField(blank=True, null=True)
    min_stationary_od = models.FloatField()
    min_stationary_growth_rate = models.FloatField()
    measurement_type_db = models.ForeignKey('MeasurementTypes', models.DO_NOTHING, blank=True, null=True)
    batch = models.ForeignKey(Batches, models.DO_NOTHING, blank=True, null=True)

    def __init__(self, *args, **kwargs):
        # Remove unknown fields from kwargs before calling parent __init__
        field_names = [f.name for f in self._meta.fields]
        for key in list(kwargs.keys()):
            if key not in field_names:
                kwargs.pop(key)
        super().__init__(*args, **kwargs)

    class Meta:
        managed = False
        db_table = 'growth_analyses'


class HeatBlockPositions(models.Model):
    db_id = models.AutoField(primary_key=True)
    position_id = models.IntegerField()
    status = models.CharField(max_length=20, blank=True, null=True)
    experiment_id = models.IntegerField(blank=True, null=True)
    batch_id = models.IntegerField(blank=True, null=True)
    time = models.DateTimeField(blank=True, null=True)
    current_opticale_temperature = models.FloatField(
        db_column='current_opticALE_temperature')  # Field name made lowercase.
    current_opticale_stirring_rpm = models.FloatField(
        db_column='current_opticALE_stirring_rpm')  # Field name made lowercase.
    d0_580_blank = models.IntegerField(db_column='D0_580_blank')  # Field name made lowercase.
    d0_640_blank = models.IntegerField(db_column='D0_640_blank')  # Field name made lowercase.
    d0_480_blank = models.IntegerField(db_column='D0_480_blank')  # Field name made lowercase.
    d0_620_blank = models.IntegerField(db_column='D0_620_blank')  # Field name made lowercase.
    m0_580_correction = models.IntegerField(db_column='M0_580_correction')  # Field name made lowercase.
    m0_640_correction = models.IntegerField(db_column='M0_640_correction')  # Field name made lowercase.
    m0_480_correction = models.IntegerField(db_column='M0_480_correction')  # Field name made lowercase.
    m0_620_correction = models.IntegerField(db_column='M0_620_correction')  # Field name made lowercase.
    media_type_id = models.IntegerField(blank=True, null=True)
    description = models.CharField(max_length=100, blank=True, null=True)
    heat_block = models.ForeignKey('HeatBlocks', models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'heat_block_positions'


class HeatBlocks(models.Model):
    db_id = models.AutoField(primary_key=True)
    definition = models.CharField(max_length=100, blank=True, null=True)
    machine = models.ForeignKey('Machines', models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'heat_blocks'


class InoculatedFromBatches(models.Model):
    pale_ale_test = models.ForeignKey('PaleAleTest', models.DO_NOTHING, blank=True, null=True)
    batch = models.ForeignKey(Batches, models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'inoculated_from_batches'


class Machines(models.Model):
    db_id = models.AutoField(primary_key=True)
    name = models.CharField(unique=True, max_length=50)
    driver_string = models.CharField(max_length=50)
    measurement_driver_string = models.CharField(max_length=50)

    class Meta:
        managed = False
        db_table = 'machines'


class MeasurementTypes(models.Model):
    db_id = models.AutoField(primary_key=True)
    description = models.CharField(max_length=50)
    initial_growth_rate = models.FloatField()
    previous_growth = models.FloatField()
    blank_value = models.FloatField()
    batch = models.ForeignKey(Batches, models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'measurement_types'


class Measurements(models.Model):
    db_id = models.AutoField(primary_key=True)
    time = models.DateTimeField()
    hidden = models.IntegerField()
    deleted = models.IntegerField()
    accepted = models.IntegerField()
    calculated = models.IntegerField()
    calculated_orreader_value = models.FloatField(db_column='calculated_orReader_value')  # Field name made lowercase.
    inoculated = models.IntegerField()
    visualization_only = models.IntegerField()
    qualifier = models.CharField(max_length=100, blank=True, null=True)
    sampling_volume = models.IntegerField()
    measurement_type_id = models.CharField(max_length=50)
    raw_transmittance_value = models.FloatField()
    empty_scattering_value = models.FloatField()
    stirring_rate = models.FloatField()
    measurement_type_db = models.ForeignKey(MeasurementTypes, models.DO_NOTHING, blank=True, null=True)
    class Meta:
        managed = False
        db_table = 'measurements'
    @property
    def OD(self):
        return self.value
    @property
    def optical_density(self):
        return self.value
    @property
    def raw_incident_value(self):
        if self.measurement_type_db is None:
            return 5000
        return self.measurement_type_db.blank_value
    @property
    def value(self):
        if self.calculated_orreader_value and self.calculated_orreader_value > 0:
            return self.calculated_orreader_value

        else:
            if self.measurement_type_db and self.raw_incident_value != 0 and self.raw_transmittance_value != 0 and \
                    self.measurement_type_db.description[-1].lower() == 'a':
                adc_OD_values = float(np.log10(self.raw_incident_value / self.raw_transmittance_value))
            elif self.measurement_type_db and self.raw_incident_value != 0 and self.raw_transmittance_value != 0 and \
                    self.measurement_type_db.description[-1].lower() == 'r':
                adc_OD_values = (self.raw_transmittance_value / self.empty_scattering_value) - self.raw_incident_value
            else:
                adc_OD_values = 0.01  # To prevent division by zero

            # Ensure adc_OD_values is a valid number
            adc_OD_values = np.nan_to_num(adc_OD_values, nan=0.01)  # Convert nan to 0.01
            adc_OD_values = max(round(adc_OD_values, 3), 0.01)
            return float(adc_OD_values)


class MediaComponents(models.Model):
    db_id = models.AutoField(primary_key=True)
    volume = models.IntegerField()
    media_stock = models.ForeignKey('MediaStocks', models.DO_NOTHING, blank=True, null=True)
    media = models.ForeignKey('Medias', models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'media_components'


class MediaController(models.Model):
    media_db = models.ForeignKey('Medias', models.DO_NOTHING, blank=True, null=True)
    controller_db = models.ForeignKey(Controllers, models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'media_controller'


class MediaStocks(models.Model):
    db_id = models.AutoField(primary_key=True)
    description = models.CharField(max_length=150)
    location = models.CharField(max_length=30)
    position = models.IntegerField()
    is_active = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'media_stocks'


class Medias(models.Model):
    db_id = models.AutoField(primary_key=True)
    description = models.CharField(max_length=200, blank=True, null=True)
    volume_scaling = models.FloatField()

    class Meta:
        managed = False
        db_table = 'medias'


class Opticales(models.Model):
    db_id = models.AutoField(primary_key=True)
    port = models.CharField(max_length=50, blank=True, null=True)
    terminator = models.CharField(max_length=5)
    timeout = models.IntegerField(blank=True, null=True)
    baudrate = models.IntegerField(blank=True, null=True)
    stir_speed = models.IntegerField(blank=True, null=True)
    coupling_stir_speed = models.IntegerField(blank=True, null=True)
    stir_power = models.IntegerField(blank=True, null=True)
    machine = models.ForeignKey(Machines, models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'opticales'


class PaleAle(models.Model):
    db = models.OneToOneField('Protocol', models.DO_NOTHING, primary_key=True)
    media_ratio = models.FloatField()
    target_od = models.FloatField()
    target_od_accuracy = models.FloatField()
    min_stationary_phase_duration = models.FloatField()
    pass_volume = models.IntegerField()
    sampling_delay = models.IntegerField()
    field_need_to_pass = models.IntegerField(db_column='_need_to_pass')  # Field renamed because it started with '_'.
    max_decrease = models.FloatField()
    min_decrease = models.FloatField()
    default_sampling_delay = models.IntegerField()
    min_accurate_od = models.FloatField()
    starting_media = models.ForeignKey(Medias, models.DO_NOTHING, blank=True, null=True)
    ending_media = models.ForeignKey(Medias, models.DO_NOTHING, related_name='paleale_ending_media_set', blank=True,
                                     null=True)
    media = models.ForeignKey(Medias, models.DO_NOTHING, related_name='paleale_media_set', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'pale_ale'


class PaleAleTest(models.Model):
    db = models.OneToOneField('Protocol', models.DO_NOTHING, primary_key=True)
    sampling_delay = models.IntegerField()
    status = models.CharField(max_length=20)
    delta_od = models.FloatField()
    growth_time = models.FloatField()
    stationary_phase_length = models.FloatField()
    growth_time_extension = models.IntegerField()
    pass_volume = models.FloatField()
    min_number_of_batches = models.IntegerField()
    field_propagate_boolean = models.IntegerField(
        db_column='_propagate_boolean')  # Field renamed because it started with '_'.

    class Meta:
        managed = False
        db_table = 'pale_ale_test'


class PaleAleTestExperiments(models.Model):
    pale_ale = models.ForeignKey(PaleAle, models.DO_NOTHING, blank=True, null=True)
    experiment = models.ForeignKey(Experiments, models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'pale_ale_test_experiments'


class ParentPaleAleExperiments(models.Model):
    pale_ale_test = models.ForeignKey(PaleAleTest, models.DO_NOTHING, blank=True, null=True)
    experiment = models.ForeignKey(Experiments, models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'parent_pale_ale_experiments'


class ParentTaleExperiments(models.Model):
    test_tale = models.ForeignKey('TestTale', models.DO_NOTHING, blank=True, null=True)
    experiment = models.ForeignKey(Experiments, models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'parent_tale_experiments'


class Projects(models.Model):
    db_id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=100)
    operator = models.CharField(max_length=50)
    date_created = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'projects'


class Protocol(models.Model):
    db_id = models.AutoField(primary_key=True)
    pass_volume = models.IntegerField()
    inoculation_volume = models.IntegerField()
    sampling_volume = models.IntegerField()
    filter_toggle = models.IntegerField()
    filter_delay = models.CharField(max_length=20)
    filter_vol = models.IntegerField()
    meas_until_filter = models.IntegerField()
    filter_at_batch = models.IntegerField()
    type = models.CharField(max_length=50, blank=True, null=True)
    experiment = models.ForeignKey(Experiments, models.DO_NOTHING, blank=True, null=True)
    media = models.ForeignKey(Medias, models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'protocol'


class RackPositions(models.Model):
    db_id = models.AutoField(primary_key=True)
    position_id = models.IntegerField()
    status = models.CharField(max_length=20, blank=True, null=True)
    time = models.DateTimeField(blank=True, null=True)
    rack = models.ForeignKey('Racks', models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'rack_positions'


class Racks(models.Model):
    db_id = models.AutoField(primary_key=True)
    columns = models.IntegerField(blank=True, null=True)
    rows = models.IntegerField(blank=True, null=True)
    machine = models.ForeignKey(Machines, models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'racks'


class ReaderPlate(models.Model):
    db_id = models.AutoField(primary_key=True)
    columns = models.IntegerField(blank=True, null=True)
    rows = models.IntegerField(blank=True, null=True)
    machine = models.ForeignKey(Machines, models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'reader_plate'


class ReaderPlatePositions(models.Model):
    db_id = models.AutoField(primary_key=True)
    position_id = models.IntegerField()
    status = models.CharField(max_length=20, blank=True, null=True)
    time = models.DateTimeField(blank=True, null=True)
    reader_plate = models.ForeignKey(ReaderPlate, models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'reader_plate_positions'


class Stirrers(models.Model):
    db_id = models.AutoField(primary_key=True)
    port = models.CharField(max_length=5, blank=True, null=True)
    terminator = models.CharField(max_length=5)
    timeout = models.IntegerField(blank=True, null=True)
    baudrate = models.IntegerField(blank=True, null=True)
    stir_speed = models.IntegerField(blank=True, null=True)
    aspirate_stir_speed = models.IntegerField(blank=True, null=True)
    coupling_stir_speed = models.IntegerField(blank=True, null=True)
    stir_power = models.IntegerField(blank=True, null=True)
    machine = models.ForeignKey(Machines, models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'stirrers'


class StorageRackPositions(models.Model):
    db_id = models.AutoField(primary_key=True)
    position_id = models.IntegerField()
    status = models.CharField(max_length=20, blank=True, null=True)
    time = models.DateTimeField(blank=True, null=True)
    experiment_id = models.IntegerField(blank=True, null=True)
    batch_id = models.IntegerField(blank=True, null=True)
    media_type_id = models.IntegerField(blank=True, null=True)
    description = models.CharField(max_length=100, blank=True, null=True)
    storage_rack = models.ForeignKey('StorageRacks', models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'storage_rack_positions'


class StorageRacks(models.Model):
    db_id = models.AutoField(primary_key=True)
    definition = models.CharField(max_length=100, blank=True, null=True)
    machine = models.ForeignKey(Machines, models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'storage_racks'


class SysConfig(models.Model):
    variable = models.CharField(primary_key=True, max_length=128)
    value = models.CharField(max_length=128, blank=True, null=True)
    set_time = models.DateTimeField()
    set_by = models.CharField(max_length=128, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'sys_config'


class Tale(models.Model):
    db = models.OneToOneField(Protocol, models.DO_NOTHING, primary_key=True)
    drop_factor = models.FloatField()
    upper_growth_rate = models.FloatField()
    lower_growth_rate = models.FloatField()
    pass_volume = models.IntegerField()
    inoculation_volume = models.IntegerField()
    pass_od = models.FloatField()
    pass_od_accuracy = models.FloatField()
    sampling_delay = models.IntegerField()
    min_rest = models.IntegerField()
    max_rest = models.IntegerField()
    field_next_step = models.FloatField(db_column='_next_step', blank=True,
                                        null=True)  # Field renamed because it started with '_'.
    max_samples = models.IntegerField()
    initial_media = models.ForeignKey(Medias, models.DO_NOTHING, blank=True, null=True)
    one_step_away_media = models.ForeignKey(Medias, models.DO_NOTHING, related_name='tale_one_step_away_media_set',
                                            blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tale'


class TemperatureMeasurements(models.Model):
    db_id = models.AutoField(primary_key=True)
    time = models.DateTimeField()
    temperature = models.FloatField(blank=True, null=True)
    batch = models.ForeignKey(Batches, models.DO_NOTHING, blank=True, null=True)
    measurement = models.ForeignKey(Measurements, models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'temperature_measurements'


class TestTale(models.Model):
    db = models.OneToOneField(Protocol, models.DO_NOTHING, primary_key=True)
    sampling_delay = models.IntegerField()
    status = models.CharField(max_length=20)

    class Meta:
        managed = False
        db_table = 'test_tale'


class TestTaleExperiments(models.Model):
    tale = models.ForeignKey(Tale, models.DO_NOTHING, blank=True, null=True)
    experiment = models.ForeignKey(Experiments, models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'test_tale_experiments'


class TipBoxPositions(models.Model):
    db_id = models.AutoField(primary_key=True)
    position_id = models.IntegerField()
    status = models.CharField(max_length=20, blank=True, null=True)
    time = models.DateTimeField(blank=True, null=True)
    tip_boxes = models.ForeignKey('TipBoxes', models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tip_box_positions'


class TipBoxes(models.Model):
    db_id = models.AutoField(primary_key=True)
    columns = models.IntegerField(blank=True, null=True)
    rows = models.IntegerField(blank=True, null=True)
    boxes = models.IntegerField(blank=True, null=True)
    machine = models.ForeignKey(Machines, models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tip_boxes'


class Urarm(models.Model):
    db_id = models.AutoField(primary_key=True)
    pc_ip = models.CharField(max_length=50)
    robot_ip = models.CharField(max_length=50)
    script_folder = models.CharField(max_length=250)
    machine = models.ForeignKey(Machines, models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'urarm'
