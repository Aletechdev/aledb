# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('seq', '0002_observedmutation_key_mutation'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='observedmutation',
            name='key_mutation',
        ),
    ]
