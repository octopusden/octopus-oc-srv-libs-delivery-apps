# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('checksums', '0021_auto_20180329_0242'),
    ]

    operations = [
        migrations.AddField(
            model_name='files',
            name='depth_level',
            field=models.PositiveIntegerField(null=False, blank=False, default=0),
        ),
    ]
