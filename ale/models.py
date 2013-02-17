from django.db import models

# Create your models here.
class Instrument(models.Model):
    name = models.CharField(max_length=200)

    def __unicode__(self):
        return self.name

class AleExperiment(models.Model):
    # TODO - id should be something that you enter
    ale_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=40)
    person = models.CharField(max_length=200)
    date = models.DateTimeField(auto_now_add=True)
    instrument = models.ForeignKey(Instrument)
    simulation = models.BooleanField()
    notes = models.TextField(blank=True)
    def __unicode__(self):
        return "#%d-%s %s" % (self.ale_id, self.name, self.instrument)
    
    class Meta:
        verbose_name_plural = "ALE Experiments"

class Media(models.Model):
    temperature = models.FloatField(default=37,
        help_text="Temperature in Celcius")
    volume = models.FloatField(default=25,
        help_text="Volume of culture in each flask (mL)")
    stirring_speed = models.FloatField(default=1123, help_text="RPM")
    description = models.CharField(max_length=200)
    other = models.TextField(blank=True)
    # todo - figure out components
    # maybe carbon source, etc.? or track individual chemicals
    def __unicode__(self):
        return "%s (%.1f C, %.1f mL, %.1f RPM)" % \
            (self.description, self.temperature, self.volume, self.stirring_speed)

    class Meta:
        verbose_name_plural = "Media"

class AleId(models.Model):
    """Parallel ALE's run within an ALE experiment"""
    ale_id = models.IntegerField()
    description = models.CharField(max_length=300)
    ale_experiment = models.ForeignKey(AleExperiment)
    starting_strain_population = models.ForeignKey("FrozenPopulation", null=True, blank=True, default=None)
    starting_strain_isolate = models.ForeignKey("Isolate", null=True, blank=True, default=None)

    def __unicode__(self):
        return "ALE #%d from %s" % (self.ale_id, self.ale_experiment.name)

    class Meta:
        unique_together = (("ale_experiment", "ale_id"),)
        verbose_name_plural = "ALEs"

class FreezerBox(models.Model):
    name = models.CharField(max_length=500,
        help_text="A unique name that identifies the box form other boxes")
    number = models.IntegerField(default = 1,
        help_text="Start with 1. If another box with the same name is needed label it with 2, 3 etc... Make sure this box number appears on the label")
    
    def __unicode__(self):
        return "Box #%i - %s" % (self.number, self.name)
    
    class Meta:
        verbose_name_plural = "Freezer Boxes"
        
class FrozenPopulation(models.Model):
    ale_id = models.ForeignKey(AleId)
    flask_number = models.IntegerField(blank=True,
        help_text="Enter 0 if the population did not originate from an ALE")
    person = models.CharField(max_length=50)
    freezer_box = models.ForeignKey(FreezerBox)
    media = models.ForeignKey(Media)
    comments = models.CharField(max_length=200, help_text="If the population did not originate from an ALE put the name of the strain here")

    def __unicode__(self):
        if self.flask_number == 0:
            return self.comments
        else:
            return "Flask #%d from %s" % (self.flask_number, unicode(self.ale_id))
        
    def ale_experiment(self):
        return self.ale_id.ale_experiment.ale_id

    class Meta:
        unique_together = (("ale_id", "flask_number"),)
        verbose_name_plural = "Frozen Populations"
        

class Isolate(models.Model):
    isolate_id = models.IntegerField()
    frozen_population = models.ForeignKey(FrozenPopulation)
    freezer_box = models.ForeignKey(FreezerBox)
    description = models.CharField(max_length=300, blank=True)
    person = models.CharField(max_length=200, blank=True)

    class Meta:
        unique_together = (("frozen_population", "isolate_id"),)
    # TODO - encode experiments done on the isolate

