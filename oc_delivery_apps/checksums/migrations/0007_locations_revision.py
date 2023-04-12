# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('checksums', '0006_citypes_is_deliverable'),
    ]

    operations = [
        migrations.AddField(
            model_name='locations',
            name='revision',
            field=models.CharField(max_length=64, blank=True, null=True),
        ),
    ]
