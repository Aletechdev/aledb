# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ale', '0002_auto_20151001_1034'),
        ('seq', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='observedmutation',
            name='key_mutation',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, default=None, blank=True, to='ale.KeyMutation', null=True),
        ),
    ]
