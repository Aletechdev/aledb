# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('seq', '0005_remove_observedmutation_key_mutation'),
        ('ale', '0004_auto_20151001_1239'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='keymutation',
            name='mutations',
        ),
        migrations.AddField(
            model_name='keymutation',
            name='mutation',
            field=models.ForeignKey(to='seq.Mutation', null=True),
        ),
    ]
