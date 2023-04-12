# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('checksums', '0017_historicallocations_history_change_reason'),
    ]

    operations = [
        migrations.AlterIndexTogether(
            name='checksums',
            index_together=set([('checksum', 'cs_prov')]),
        ),
    ]
