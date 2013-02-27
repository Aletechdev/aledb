from django.db import models

blank_field = {"blank": True, "null": True}

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
    notes = models.TextField(**blank_field)
    def __unicode__(self):
        if self.simulation:
            return "#%d-%s-SIM" % (self.ale_id, self.name)
        else:
            return "#%d-%s" % (self.ale_id, self.name)
    
    class Meta:
        verbose_name_plural = "ALE Experiments"

class Media(models.Model):
    temperature = models.FloatField(default=37,
        help_text="Temperature in Celcius")
    volume = models.FloatField(default=25,
        help_text="Volume of culture in each flask (mL)")
    stirring_speed = models.FloatField(default=1123, help_text="RPM")
    description = models.CharField(max_length=200)
    other = models.TextField(**blank_field)
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
    description = models.CharField(max_length=300, **blank_field)
    ale_experiment = models.ForeignKey(AleExperiment)
    starting_strain = models.ForeignKey("Isolate", default=None, **blank_field)

    def __unicode__(self):
        #return "ALE #%d < %s" % (self.ale_id, self.ale_experiment.name)
        return "ALE #%d < %s" % (self.ale_id, self.ale_experiment)

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
        

class Flask(models.Model):
    ale_id = models.ForeignKey(AleId)
    flask_number = models.IntegerField(**blank_field)
    media = models.ForeignKey(Media)
    comments = models.CharField(max_length=200, **blank_field)

    def __unicode__(self):
        return "Flask#%d < %s" % (self.flask_number, self.ale_id)
        
    def ale_experiment(self):
        return self.ale_id.ale_experiment.ale_id

    class Meta:
        unique_together = (("ale_id", "flask_number"),)
        verbose_name_plural = "Flasks"
        

class Isolate(models.Model):
    isolate_number = models.IntegerField()
    parent_isolate = models.ForeignKey("Isolate", **blank_field)
    flask = models.ForeignKey(Flask)
    is_population = models.BooleanField()
    freezer_box = models.ForeignKey(FreezerBox)
    description = models.CharField(max_length=300, **blank_field)
    person = models.CharField(max_length=200, **blank_field)
    
    def __unicode__(self):
        if self.flask.flask_number == 0:
            return self.description
        else:
            if self.is_population:
                return "#%d POP < %s" % (self.isolate_number, self.flask)
            else:
                return "#%d COL < %s" % (self.isolate_number, self.parent_isolate)
    
    class Meta:
        unique_together = (("flask", "isolate_number"),)
    # TODO - encode experiments done on the isolate

