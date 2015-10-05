# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ale', '0004_auto_20151001_1239'),
        ('seq', '0003_remove_observedmutation_key_mutation'),
    ]

    operations = [
        migrations.AddField(
            model_name='observedmutation',
            name='key_mutation',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, default=None, blank=True, to='ale.KeyMutation', null=True),
        ),
    ]
