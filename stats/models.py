from django.db import models
from django_mysql.models import JSONField, Model

# Create your models here.
class StaticData(models.Model):
    id = models.AutoField(primary_key=True)
    mut_needle_data = JSONField(default=dict)
    histogram_data = JSONField(default=dict)