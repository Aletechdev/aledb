# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ale', '0003_auto_20151104_2118'),
    ]

    operations = [
        migrations.AddField(
            model_name='isolate',
            name='library_prep',
            field=models.CharField(max_length=200, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='isolate',
            name='reseq_reference',
            field=models.CharField(max_length=200, null=True, blank=True),
        ),
    ]
