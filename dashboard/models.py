from django.db import models
from django_mysql.models import JSONField, Model


class ObservedMutationCounts(models.Model):
    total = models.IntegerField(default=0)
    single_base_substitution = models.IntegerField(default=0)
    multiple_base_substitution = models.IntegerField(default=0)
    deletion = models.IntegerField(default=0)
    insertion = models.IntegerField(default=0)
    mobile_element_insertion = models.IntegerField(default=0)
    amplification = models.IntegerField(default=0)
    gene_conversion = models.IntegerField(default=0)
    inversion = models.IntegerField(default=0)
    intergenic = models.IntegerField(default=0)
    noncoding = models.IntegerField(default=0)
    pseudogene = models.IntegerField(default=0)
    synonymous = models.IntegerField(default=0)
    nonsynonymous = models.IntegerField(default=0)


class UniqueMutationCounts(models.Model):
    total = models.IntegerField(default=0)
    single_base_substitution = models.IntegerField(default=0)
    multiple_base_substitution = models.IntegerField(default=0)
    deletion = models.IntegerField(default=0)
    insertion = models.IntegerField(default=0)
    mobile_element_insertion = models.IntegerField(default=0)
    amplification = models.IntegerField(default=0)
    gene_conversion = models.IntegerField(default=0)
    inversion = models.IntegerField(default=0)
    intergenic = models.IntegerField(default=0)
    noncoding = models.IntegerField(default=0)
    pseudogene = models.IntegerField(default=0)
    synonymous = models.IntegerField(default=0)
    nonsynonymous = models.IntegerField(default=0)


class TimelineEvent(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=100)
    message = models.CharField(max_length=500)
    icon = models.CharField(max_length=200)
    color = models.CharField(max_length=50, default='')


class SampleCounts(models.Model):
    ale_count = models.IntegerField(default=0)
    isolate_count = models.IntegerField(default=0)
    flask_count = models.IntegerField(default=0)

def bar_chart_json_default(): return {"":""}
class BarCharts(Model):
    mut_gene_json = JSONField(default=bar_chart_json_default)
    mut_json = JSONField(default=bar_chart_json_default)
