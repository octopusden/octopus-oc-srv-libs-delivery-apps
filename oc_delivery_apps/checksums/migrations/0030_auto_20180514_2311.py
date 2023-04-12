# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('checksums', '0029_fake_id_reverse'),
    ]

    operations = [
        migrations.AlterIndexTogether(
            name='locations',
            index_together=set([('path', 'loc_type', 'revision', 'file_dst'), ('file',), ('file_dst',)]),
        ),
        migrations.AlterIndexTogether(
            name='historicallocations',
            index_together=set([('path', 'loc_type', 'revision', 'file_dst'), ('file',), ('file_dst',)]),
        ),
    ]
