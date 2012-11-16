from django.db import models

# Create your models here.
class Instrument(models.Model):
    name = models.CharField(max_length=200)

    def __unicode__(self):
        return self.name

class AleExperiment(models.Model):
    # TODO - id should be something that you enter
    ale_id = models.AutoField(primary_key=True)
    person = models.CharField(max_length=200)
    date = models.DateField()
    instrument = models.ForeignKey(Instrument)
    notes = models.TextField(blank=True)
    def __unicode__(self):
        return "Ale %s#%d" % (self.instrument, self.ale_id)

class Media(models.Model):
    temperature = models.FloatField(default=37,
        help_text="Temperature in Celcius")
    volume = models.FloatField(default=25,
        help_text="Volume of culture in each flask (mL)")
    stirring_speed = models.FloatField(default=1123, help_text="RPM")
    description = models.CharField(max_length=200)
    other = models.TextField(blank=True)
    # todo - figure out components
    def __unicode__(self):
        return "%s (%.1f C, %.1f mL, %.1f RPM)" % \
            (self.description, self.temperature, self.volume, self.stirring_speed)

    class Meta:
        verbose_name_plural = "media"

class AleId(models.Model):
    """Parallel ALE's run within an ALE experiment"""
    ale_id = models.IntegerField()
    parent_strain = models.CharField(max_length=300)
    ale_experiment = models.ForeignKey(AleExperiment)

    def __unicode__(self):
        return "Ale #%d from %s" % (self.ale_id, str(self.ale_experiment))

    class Meta:
        unique_together = (("ale_experiment", "ale_id"),)

class FrozenPopulation(models.Model):
    ale_id = models.ForeignKey(AleId)
    flask_number = models.IntegerField()
    media = models.ForeignKey(Media)  # TODO - decide where this should go
    person = models.CharField(max_length=200, blank=True)

    def __unicode__(self):
        return "Flask #%d from %s" % (self.flask_number, str(self.ale_id))

    class Meta:
        unique_together = (("ale_id", "flask_number"),)

class Isolate(models.Model):
    isolate_id = models.IntegerField()
    frozen_population = models.ForeignKey(FrozenPopulation)
    person = models.CharField(max_length=200, blank=True)

    class Meta:
        unique_together = (("frozen_population", "isolate_id"),)
    # TODO - encode experiments done on the isolate
