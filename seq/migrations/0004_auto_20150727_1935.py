# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('seq', '0003_remove_resequencingexperiment_unassigned_missing_coverage_evidence'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='unassignedmissingcoverageevidence',
            name='sequencing_experiment',
        ),
        migrations.DeleteModel(
            name='UnassignedMissingCoverageEvidence',
        ),
    ]
