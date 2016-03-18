# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('seq', '0002_auto_20151114_2131'),
    ]

    operations = [
        migrations.CreateModel(
            name='Filter',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('min_cutoff', models.PositiveSmallIntegerField(default=20)),
                ('max_cutoff', models.PositiveSmallIntegerField(default=100)),
                ('ignored_genes', models.CharField(default=b'', max_length=500, blank=True)),
            ],
        ),
    ]
