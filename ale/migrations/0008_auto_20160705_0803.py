# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ale', '0007_filter'),
    ]

    operations = [
        migrations.AlterField(
            model_name='filter',
            name='ignored_genes',
            field=models.CharField(blank=True, default='', max_length=500),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='freezerbox',
            name='location',
            field=models.CharField(help_text='Where is the box located', default='None', max_length=500, null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='freezerbox',
            name='location_last_updated',
            field=models.DateField(auto_now=True, help_text='Date when location was last updated', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='freezerbox',
            name='name',
            field=models.CharField(help_text='A unique name that identifies the box from other boxes', max_length=500),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='freezerbox',
            name='number',
            field=models.IntegerField(help_text='Start with 1. If another box with the same name is needed label it with 2, 3 etc... Make sure this box number appears on the label', default=1),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='media',
            name='stirring_speed',
            field=models.FloatField(help_text='RPM', default=1123),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='media',
            name='temperature',
            field=models.FloatField(help_text='Temperature in Celcius', default=37),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='media',
            name='volume',
            field=models.FloatField(help_text='Volume of culture in each flask (mL)', default=25),
            preserve_default=True,
        ),
    ]
