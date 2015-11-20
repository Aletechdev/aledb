# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ale', '0004_auto_20151111_1906'),
    ]

    operations = [
        migrations.AddField(
            model_name='isolate',
            name='breseq_version',
            field=models.CharField(max_length=200, null=True, blank=True),
        ),
    ]
