# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('checksums', '0005_fileinfo'),
    ]

    operations = [
        migrations.AddField(
            model_name='citypes',
            name='is_deliverable',
            field=models.BooleanField(default=False),
        ),
    ]
