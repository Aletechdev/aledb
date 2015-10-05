# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('seq', '0003_remove_observedmutation_key_mutation'),
        ('ale', '0002_auto_20151001_1034'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='keymutation',
            name='ale_experiment',
        ),
        migrations.RemoveField(
            model_name='keymutation',
            name='mutations',
        ),
        migrations.RemoveField(
            model_name='aleexperiment',
            name='key_mutation',
        ),
        migrations.DeleteModel(
            name='KeyMutation',
        ),
    ]
