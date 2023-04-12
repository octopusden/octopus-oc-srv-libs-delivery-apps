# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dlcontents', '0016_citypeparms'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicallocations',
            name='history_change_reason',
            field=models.CharField(max_length=100, null=True),
        ),
    ]
