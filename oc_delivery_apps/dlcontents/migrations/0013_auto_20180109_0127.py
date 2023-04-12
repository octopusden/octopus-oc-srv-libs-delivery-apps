# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dlcontents', '0012_citypegroups_rn_artifactid'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicallocations',
            name='file_dst',
            field=models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.DO_NOTHING, db_constraint=False, blank=True, to='dlcontents.Files', null=True),
        ),
        migrations.AddField(
            model_name='locations',
            name='file_dst',
            field=models.ForeignKey(related_name='FileIdDst+', blank=True, to='dlcontents.Files', null=True, on_delete=models.CASCADE),
        ),
    ]
