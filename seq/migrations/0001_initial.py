# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ale', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Mutation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('mutation_type', models.CharField(help_text=b'Use breseq mutation codes, see the genome diff site\n                                     on the barrick lab wiki (http://tinyurl.com/l3fvnap) for more\n                                     information', max_length=3, null=True)),
                ('position', models.IntegerField()),
                ('feature_length', models.IntegerField(null=True, blank=True)),
                ('sequence_change', models.CharField(max_length=100)),
                ('protein_change', models.CharField(max_length=300, null=True, blank=True)),
                ('gene', models.CharField(max_length=300, null=True, blank=True)),
                ('reference_error', models.NullBooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='ObservedMutation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('present', models.NullBooleanField()),
                ('breseq_present', models.NullBooleanField()),
                ('wt_reads', models.IntegerField(null=True)),
                ('mutated_reads', models.IntegerField(null=True)),
                ('other_reads', models.IntegerField(null=True)),
                ('reference_genome_likelihood', models.FloatField(null=True)),
                ('evidence', models.CharField(max_length=400, null=True, blank=True)),
                ('frequency', models.DecimalField(null=True, max_digits=5, decimal_places=4)),
                ('mutation', models.ForeignKey(to='seq.Mutation')),
            ],
        ),
        migrations.CreateModel(
            name='ResequencingExperiment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('person', models.CharField(max_length=200, blank=True)),
                ('reads', models.IntegerField(null=True, blank=True)),
                ('average_read_length', models.FloatField(null=True, blank=True)),
                ('location', models.CharField(max_length=200, null=True, blank=True)),
                ('mean_coverage', models.FloatField(null=True, blank=True)),
                ('percentage_mapped', models.FloatField(null=True, blank=True)),
                ('isolate', models.ForeignKey(to='ale.Isolate')),
                ('mutations', models.ManyToManyField(to='seq.Mutation', through='seq.ObservedMutation')),
            ],
        ),
        migrations.CreateModel(
            name='UnassignedMissingCoverageEvidence',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('seq_id', models.CharField(max_length=100)),
                ('start', models.IntegerField()),
                ('end', models.IntegerField()),
                ('sequencing_experiment', models.ForeignKey(to='seq.ResequencingExperiment')),
            ],
        ),
        migrations.AddField(
            model_name='observedmutation',
            name='sequencing_experiment',
            field=models.ForeignKey(to='seq.ResequencingExperiment'),
        ),
        migrations.AlterUniqueTogether(
            name='mutation',
            unique_together=set([('position', 'sequence_change')]),
        ),
    ]
