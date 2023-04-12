# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dlcontents', '0011_remove_citypegroups_rn_gav'),
    ]

    operations = [
        migrations.AddField(
            model_name='citypegroups',
            name='rn_artifactid',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
    ]
