# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('checksums', '0020_cs_prov_migration'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='checksums',
            unique_together=set([('checksum', 'cs_type')]),
        ),
        migrations.AlterIndexTogether(
            name='checksums',
            index_together=set([]),
        ),
        migrations.AlterIndexTogether(
            name='checksumsnst',
            index_together=set([('checksum', 'cs_type')]),
        ),
        migrations.RemoveField(
            model_name='checksums',
            name='cs_prov',
        ),
        migrations.RemoveField(
            model_name='checksumsnst',
            name='cs_prov',
        ),
    ]
