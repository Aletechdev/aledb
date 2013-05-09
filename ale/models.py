from django.db import models

blank_field = {"blank": True, "null": True}

# Create your models here.
class Instrument(models.Model):
    name = models.CharField(max_length=200)

    def __unicode__(self):
        return self.name

class AleExperiment(models.Model):
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
    location = models.CharField(max_length=500, null=True, default="None",
        help_text="Where is the box located")
    location_last_updated = models.DateField(auto_now_add=True, auto_now=True, null=True, default="2013-05-02",
        help_text="Date when location was last updated")
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
        if self.ale_id.description is not None:
            if self.ale_id.description.lower() == ('Not from ALE').lower():
                return 'Not from ALE'
            else:
                return "Flask#%d < %s" % (self.flask_number, self.ale_id)
        else:
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

    def seq_location(self):
        return self.resequencingexperiment_set.values_list("location")[0][0]
    
    def __unicode__(self):
        if self.flask.ale_id.description is not None:
            if self.flask.ale_id.description.lower() == ('Not from ALE').lower():
                return self.description
            else:
                p_c = "POP" if self.is_population else "COL"
                parent = self.parent_isolate if self.parent_isolate else self.flask
                return "#%d %s < %s" % (self.isolate_number, p_c, parent)
        else:
            p_c = "POP" if self.is_population else "COL"
            parent = self.parent_isolate if self.parent_isolate else self.flask
            return "#%d %s < %s" % (self.isolate_number, p_c, parent)

    class Meta:
        unique_together = (("flask", "isolate_number"),)
    # TODO - encode experiments done on the isolate
