# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('seq', '0004_auto_20150727_1935'),
    ]

    operations = [
        migrations.CreateModel(
            name='UnassignedMissingCoverageEvidence',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('seq_id', models.CharField(max_length=100)),
                ('start', models.IntegerField()),
                ('end', models.IntegerField()),
                ('sequencing_experiment', models.ForeignKey(to='seq.ResequencingExperiment')),
            ],
        ),
    ]
