# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('seq', '0007_keymutation'),
        ('ale', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='aleexperiment',
            name='key_mutations',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, default=None, blank=True, to='seq.KeyMutation', null=True),
        ),
    ]
