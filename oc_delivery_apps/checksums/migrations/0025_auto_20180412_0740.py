# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('checksums', '0024_locations_dup_remove'),
    ]

    operations = [
        migrations.AlterIndexTogether(
            name='locations',
            index_together=set([]),
        ),

        migrations.AlterUniqueTogether(
            name='locations',
            unique_together=set([('path', 'loc_type', 'file_dst', 'revision')]),
        ),
    ]
