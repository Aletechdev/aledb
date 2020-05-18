from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse

blank_field = {"blank": True, "null": True}

VIEW_PROJECT = 'view_project'


class Instrument(models.Model):

    name = models.CharField(max_length=200)

    def __unicode__(self):
        return self.name

    def __str__(self):
        return self.name


class Project(models.Model):
    name = models.CharField(max_length=50)
    user = models.ForeignKey(User, default=None, on_delete=models.DO_NOTHING, help_text="project owner")
    date = models.DateTimeField(auto_now_add=True, help_text="project created date")
    is_public = models.BooleanField(default=False)
    PROJECT_STATUS = (('new', 'New'), ('in progress', 'In progress'), ('completed', 'Completed'))
    status = models.CharField(max_length=25, default='new', blank=True, choices=PROJECT_STATUS)
    description = models.CharField(max_length=300)

    class Meta:
        permissions = (
            (VIEW_PROJECT, 'View project'),
        )

    def owner(self):
        return self.user.get_full_name()

    def experiments(self):
        return AleExperiment.objects.filter(project=self)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("project_detail", args=(self.pk,))

    def date_str(self):
        if self.date:
            return self.date.strftime("%Y-%m-%d")
        return ''


def get_projects(user: User):
    project_queryset = Project.objects.all()
    projects = []
    for project in project_queryset:
        if project.is_public or user.has_perm(VIEW_PROJECT, project):
            projects.append(project)
    return projects


class AleExperiment(models.Model):
    ale_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=200)
    person = models.CharField(max_length=200)
    date = models.DateTimeField(auto_now_add=True)
    instrument = models.ForeignKey(Instrument)
    notes = models.TextField(**blank_field)
    project = models.ForeignKey(Project, default=None, **blank_field, on_delete=models.DO_NOTHING)
    doi = models.TextField(**blank_field)

    class Meta:
        verbose_name_plural = "experiments"

    def __unicode__(self):
        return "#%d-%s" % (self.ale_id, self.name)

    def __str__(self):
        return self.name

    def doi_as_list(self):
        return self.doi.split(' ')

    def get_absolute_url(self):
        return reverse("experiment_detail", args=(self.pk,))

    def date_str(self):
        if self.date:
            return self.date.strftime("%Y-%m-%d")
        return ''

    def experiment_context(self) -> dict:
        ale_exp_name = self.project.name + ": " + self.name
        return {
            "ale_experiment_name": ale_exp_name,
            "ale_experiment_id": self.ale_id,
        }


# TODO: this model should be called "Ale".
class AleId(models.Model):
    """Parallel ALE's run within an ALE experiment"""
    ale_id = models.IntegerField()
    description = models.CharField(max_length=300, **blank_field)
    species = models.CharField(max_length=300, **blank_field)
    strain = models.CharField(max_length=300, **blank_field)
    ale_experiment = models.ForeignKey(AleExperiment)
    starting_strain = models.ForeignKey("Isolate",
                                        default=None,
                                        **blank_field)

    def __unicode__(self):
        # return "ALE #%d < %s" % (self.ale_id, self.ale_experiment.name)
        return "ALE #%d < %s" % (self.ale_id, self.ale_experiment)

    class Meta:
        unique_together = (("ale_experiment", "ale_id"),)

        verbose_name_plural = "ALEs"


class Media(models.Model):
    temperature = models.CharField(max_length=200,default='37',
                                    help_text="Temperature in Celcius")
    volume = models.FloatField(default=25,
                               help_text="Volume of culture in each flask (mL)")
    stirring_speed = models.FloatField(default=1123,
                                       help_text="RPM")
    description = models.CharField(max_length=200)
    substrate = models.CharField(max_length=200,
                                 default=None,
                                 **blank_field)
    carbon_source = models.CharField(max_length=200,
                                 default=None,
                                 **blank_field)
    nitrogen_source = models.CharField(max_length=200,
                                 default=None,
                                 **blank_field)
    phosphorus_source = models.CharField(max_length=200,
                                 default=None,
                                 **blank_field)
    sulfur_source = models.CharField(max_length=200,
                                 default=None,
                                 **blank_field)
    calcium_source = models.CharField(max_length=200,
                                     default=None,
                                     **blank_field)
    supplement = models.CharField(max_length=200,
                                     default=None,
                                     **blank_field)
    other = models.TextField(**blank_field)

    # TODO: figure out components
    # maybe carbon source, etc.? or track individual chemicals
    def __unicode__(self):
        return "%s (%.1f C, %.1f mL, %.1f RPM)" % \
               (self.description,
                self.temperature,
                self.volume,
                self.stirring_speed)

    class Meta:
        verbose_name_plural = "Media"


class FreezerBox(models.Model):

    name = models.CharField(max_length=500,
                            help_text="A unique name that identifies the box from other boxes")

    number = models.IntegerField(default=1,
                                 help_text="Start with 1. If another box with the same name is needed label it with 2, 3 etc... Make sure this box number appears on the label")

    location = models.CharField(max_length=500,
                                null=True,
                                default="None",
                                help_text="Where is the box located")

    location_last_updated = models.DateField(auto_now=True,
                                             null=True,
                                             help_text="Date when location was last updated")

    def __unicode__(self):
        return "Box #%i - %s" % (self.number,
                                 self.name)

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
                return "Flask#%d < %s" % (self.flask_number,
                                          self.ale_id)
        else:
            return "Flask#%d < %s" % (self.flask_number,
                                      self.ale_id)

    def ale_experiment(self):
        return self.ale_id.ale_experiment.ale_id
    class Meta:
        unique_together = (("ale_id",
                            "flask_number"),)

        verbose_name_plural = "Flasks"


#TODO: Change 'reseq_reference' field to 'reseq_ref_name'
#TODO: Change 'library_prep' field to 'wgs_kit'
class Isolate(models.Model):
    isolate_number = models.IntegerField()
    parent_isolate = models.ForeignKey("Isolate", **blank_field)
    flask = models.ForeignKey(Flask)
    is_population = models.BooleanField()
    freezer_box = models.ForeignKey(FreezerBox)
    description = models.CharField(max_length=300, **blank_field)
    person = models.CharField(max_length=200, **blank_field)
    reseq_reference = models.CharField(max_length=200, **blank_field)
    reseq_date = models.CharField(max_length=200, **blank_field)
    breseq_version = models.CharField(max_length=200, **blank_field)
    library_prep = models.CharField(max_length=200, **blank_field)

    def seq_location(self):
        return self.resequencingexperiment_set.values_list("location")[0][0]

    def __unicode__(self):
        if self.flask.ale_id.description is not None:
            if self.flask.ale_id.description.lower() == ('Not from ALE').lower():
                return self.description
            else:
                population_or_clonal = "POP" if self.is_population else "COL"
                parent = self.parent_isolate if self.parent_isolate else self.flask
                return "#%d %s < %s" % (self.isolate_number,
                                        population_or_clonal,
                                        parent)
        else:
            population_or_clonal = "POP" if self.is_population else "COL"
            parent = self.parent_isolate if self.parent_isolate else self.flask
            return "#%d %s < %s" % (self.isolate_number,
                                    population_or_clonal,
                                    parent)


class TechnicalReplicate(models.Model):
    tech_rep_number = models.IntegerField(default=1)
    isolate = models.ForeignKey(Isolate)
    tags = models.CharField(max_length=500, **blank_field)
    description = models.CharField(max_length=500, **blank_field)


# TODO: what are these integers referring to. If ALE Experiment, model should be moved to ale.models and use foreign keys.
class RecentExperiments(models.Model):
    first = models.IntegerField(null=True)
    second = models.IntegerField(null=True)
    third = models.IntegerField(null=True)
    fourth = models.IntegerField(null=True)
    fifth = models.IntegerField(null=True)
