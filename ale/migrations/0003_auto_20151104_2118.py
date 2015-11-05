# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ale', '0002_auto_20151104_1624'),
    ]

    operations = [
        migrations.AddField(
            model_name='aleid',
            name='knockouts',
            field=models.CharField(max_length=300, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='aleid',
            name='species',
            field=models.CharField(max_length=300, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='aleid',
            name='strain',
            field=models.CharField(max_length=300, null=True, blank=True),
        ),
    ]
