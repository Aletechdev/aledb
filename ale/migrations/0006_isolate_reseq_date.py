# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ale', '0005_isolate_breseq_version'),
    ]

    operations = [
        migrations.AddField(
            model_name='isolate',
            name='reseq_date',
            field=models.CharField(max_length=200, null=True, blank=True),
        ),
    ]
