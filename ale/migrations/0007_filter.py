# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ale', '0006_isolate_reseq_date'),
    ]

    operations = [
        migrations.CreateModel(
            name='Filter',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('min_cutoff', models.PositiveSmallIntegerField(default=20)),
                ('max_cutoff', models.PositiveSmallIntegerField(default=100)),
                ('ignored_genes', models.CharField(default=b'', max_length=500, blank=True)),
                ('ale_experiment', models.ForeignKey(to='ale.AleExperiment')),
            ],
        ),
    ]
