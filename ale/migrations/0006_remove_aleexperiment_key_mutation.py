# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ale', '0005_auto_20151005_1346'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='aleexperiment',
            name='key_mutation',
        ),
    ]
