# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('seq', '0006_auto_20150831_1943'),
    ]

    operations = [
        migrations.CreateModel(
            name='KeyMutation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('observed_mutation', models.ForeignKey(to='seq.ObservedMutation')),
            ],
        ),
    ]
