from django.db import models
from django.contrib.auth.models import User


# Create your models here.
class Run(models.Model):
    name = models.CharField(max_length=50)
    user = models.ForeignKey(User, default=None, on_delete=models.DO_NOTHING, help_text="project owner")
    date = models.DateTimeField(auto_now_add=True, help_text="pipeline run created date")
    PIPELINE_RUN_STATUS = (('new', 'New'), ('running', 'Running'), ('awaiting upload', 'Awaiting Upload'),
                           ('uploading', 'Uploading'), ('done', 'Done'))
    status = models.CharField(max_length=25, default='new', blank=True, choices=PIPELINE_RUN_STATUS)
    xpmd = models.CharField(max_length=150)

    def owner(self):
        return self.user.get_full_name()

    def __str__(self):
        return self.name

    def date_str(self):
        if self.date:
            return self.date.strftime("%Y-%m-%d")
        return ''


def get_runs(user: User):
    run_queryset = Run.objects.all()
    runs = []
    for run in run_queryset:
        if user.is_superuser or run.user == user:
            runs.append(run)
    return runs


class Attempt(models.Model):
    date = models.DateTimeField(auto_now_add=True, help_text="pipeline run attempt start date")
    run = models.ForeignKey(Run, on_delete=models.CASCADE, help_text="associated run")
    vm = models.CharField(max_length=50)
    input = models.CharField(max_length=50)
    output = models.CharField(max_length=50)

    def date_str(self):
        if self.date:
            return self.date.strftime("%Y-%m-%d")
        return ''
