# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('checksums', '0022_files_depth_level'),
    ]

    operations = [
        migrations.AlterIndexTogether(
            name='locations',
            index_together=set([ ('path', 'loc_type', 'file_dst', 'revision') ]),
        ),
        migrations.AlterIndexTogether(
            name='historicallocations',
            index_together=set([ ('path', 'loc_type', 'file_dst', 'revision') ]),
        ),
    ]
