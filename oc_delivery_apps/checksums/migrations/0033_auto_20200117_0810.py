# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('checksums', '0032_auto_20180703_0023'),
    ]

    operations = [
        migrations.AddField(
            model_name='citypegroups',
            name='doc_artifactid',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='citypes',
            name='doc_artifactid',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='citypes',
            name='rn_artifactid',
            field=models.CharField(max_length=255, null=True, blank=True),
        )
    ]
