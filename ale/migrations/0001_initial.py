# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AleExperiment',
            fields=[
                ('ale_id', models.AutoField(serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=40)),
                ('person', models.CharField(max_length=200)),
                ('date', models.DateTimeField(auto_now_add=True)),
                ('simulation', models.BooleanField()),
                ('notes', models.TextField(null=True, blank=True)),
            ],
            options={
                'verbose_name_plural': 'ALE Experiments',
            },
        ),
        migrations.CreateModel(
            name='AleId',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('ale_id', models.IntegerField()),
                ('description', models.CharField(max_length=300, null=True, blank=True)),
                ('ale_experiment', models.ForeignKey(to='ale.AleExperiment')),
            ],
            options={
                'verbose_name_plural': 'ALEs',
            },
        ),
        migrations.CreateModel(
            name='Flask',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('flask_number', models.IntegerField(null=True, blank=True)),
                ('comments', models.CharField(max_length=200, null=True, blank=True)),
                ('ale_id', models.ForeignKey(to='ale.AleId')),
            ],
            options={
                'verbose_name_plural': 'Flasks',
            },
        ),
        migrations.CreateModel(
            name='FreezerBox',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(help_text=b'A unique name that identifies the box form other boxes', max_length=500)),
                ('number', models.IntegerField(default=1, help_text=b'Start with 1. If another box with the same name is needed label it with 2, 3 etc... Make sure this box number appears on the label')),
                ('location', models.CharField(default=b'None', max_length=500, null=True, help_text=b'Where is the box located')),
                ('location_last_updated', models.DateField(help_text=b'Date when location was last updated', auto_now=True, null=True)),
            ],
            options={
                'verbose_name_plural': 'Freezer Boxes',
            },
        ),
        migrations.CreateModel(
            name='Instrument',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='Isolate',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('isolate_number', models.IntegerField()),
                ('is_population', models.BooleanField()),
                ('description', models.CharField(max_length=300, null=True, blank=True)),
                ('person', models.CharField(max_length=200, null=True, blank=True)),
                ('flask', models.ForeignKey(to='ale.Flask')),
                ('freezer_box', models.ForeignKey(to='ale.FreezerBox')),
                ('parent_isolate', models.ForeignKey(blank=True, to='ale.Isolate', null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Media',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('temperature', models.FloatField(default=37, help_text=b'Temperature in Celcius')),
                ('volume', models.FloatField(default=25, help_text=b'Volume of culture in each flask (mL)')),
                ('stirring_speed', models.FloatField(default=1123, help_text=b'RPM')),
                ('description', models.CharField(max_length=200)),
                ('other', models.TextField(null=True, blank=True)),
            ],
            options={
                'verbose_name_plural': 'Media',
            },
        ),
        migrations.AddField(
            model_name='flask',
            name='media',
            field=models.ForeignKey(to='ale.Media'),
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
