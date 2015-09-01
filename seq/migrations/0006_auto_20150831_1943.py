# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('seq', '0005_unassignedmissingcoverageevidence'),
    ]

    operations = [
        migrations.AlterField(
            model_name='observedmutation',
            name='frequency',
            field=models.DecimalField(null=True, max_digits=5, decimal_places=4),
        ),
    ]
