# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('seq', '0001_initial'),
        ('ale', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='KeyMutation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('ale_experiment', models.ForeignKey(to='ale.AleExperiment')),
                ('mutations', models.ManyToManyField(to='seq.Mutation', through='seq.ObservedMutation')),
            ],
        ),
        migrations.AddField(
            model_name='aleexperiment',
            name='key_mutation',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, default=None, blank=True, to='ale.KeyMutation', null=True),
        ),
    ]
