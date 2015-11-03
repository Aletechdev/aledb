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
            ],
            options={
                'verbose_name_plural': 'Flasks',
            },
        ),
        migrations.CreateModel(
            name='FreezerBox',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(help_text=b'A unique name that identifies the box from other boxes', max_length=500)),
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
            ],
        ),
        migrations.CreateModel(
            name='KeyMutation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('ale_experiment', models.ForeignKey(to='ale.AleExperiment')),
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
                ('substrate', models.CharField(default=None, max_length=200, null=True, blank=True)),
                ('other', models.TextField(null=True, blank=True)),
            ],
            options={
                'verbose_name_plural': 'Media',
            },
        ),
    ]
