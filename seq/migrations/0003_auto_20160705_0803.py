# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('seq', '0002_auto_20151114_2131'),
    ]

    operations = [
        migrations.CreateModel(
            name='GeneToPDB',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, primary_key=True, verbose_name='ID')),
                ('gene', models.CharField(max_length=50)),
                ('pdb_id', models.CharField(blank=True, max_length=4, null=True)),
                ('rank', models.IntegerField(blank=True, default=100, null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterField(
            model_name='mutation',
            name='mutation_type',
            field=models.CharField(help_text='Use breseq mutation codes, see the genome diff site\n                                     on the barrick lab wiki (http://tinyurl.com/l3fvnap) for more\n                                     information', max_length=3, null=True),
            preserve_default=True,
        ),
    ]
