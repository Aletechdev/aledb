# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ale', '0001_initial'),
        ('seq', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='keymutation',
            name='mutation',
            field=models.ForeignKey(to='seq.Mutation', null=True),
        ),
        migrations.AddField(
            model_name='isolate',
            name='flask',
            field=models.ForeignKey(to='ale.Flask'),
        ),
        migrations.AddField(
            model_name='isolate',
            name='freezer_box',
            field=models.ForeignKey(to='ale.FreezerBox'),
        ),
        migrations.AddField(
            model_name='isolate',
            name='parent_isolate',
            field=models.ForeignKey(blank=True, to='ale.Isolate', null=True),
        ),
        migrations.AddField(
            model_name='flask',
            name='ale_id',
            field=models.ForeignKey(to='ale.AleId'),
        ),
        migrations.AddField(
            model_name='flask',
            name='media',
            field=models.ForeignKey(to='ale.Media'),
        ),
        migrations.AddField(
            model_name='aleid',
            name='ale_experiment',
            field=models.ForeignKey(to='ale.AleExperiment'),
        ),
        migrations.AddField(
            model_name='aleid',
            name='starting_strain',
            field=models.ForeignKey(default=None, blank=True, to='ale.Isolate', null=True),
        ),
        migrations.AddField(
            model_name='aleexperiment',
            name='instrument',
            field=models.ForeignKey(to='ale.Instrument'),
        ),
        migrations.AlterUniqueTogether(
            name='isolate',
            unique_together=set([('flask', 'isolate_number')]),
        ),
        migrations.AlterUniqueTogether(
            name='flask',
            unique_together=set([('ale_id', 'flask_number')]),
        ),
        migrations.AlterUniqueTogether(
            name='aleid',
            unique_together=set([('ale_experiment', 'ale_id')]),
        ),
    ]
