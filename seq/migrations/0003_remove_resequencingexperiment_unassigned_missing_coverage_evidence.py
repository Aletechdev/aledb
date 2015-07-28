# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('seq', '0002_auto_20150721_1455'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='resequencingexperiment',
            name='unassigned_missing_coverage_evidence',
        ),
    ]
