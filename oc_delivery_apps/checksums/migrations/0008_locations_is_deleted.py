# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('checksums', '0007_locations_revision'),
    ]

    operations = [
        migrations.AddField(
            model_name='locations',
            name='is_deleted',
            field=models.BooleanField(default=False),
        ),
    ]
