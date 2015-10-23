# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ale', '0002_auto_20151008_1124'),
    ]

    operations = [
        migrations.AddField(
            model_name='media',
            name='substrate',
            field=models.CharField(default=None, max_length=200, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='freezerbox',
            name='name',
            field=models.CharField(help_text=b'A unique name that identifies the box from other boxes', max_length=500),
        ),
    ]
