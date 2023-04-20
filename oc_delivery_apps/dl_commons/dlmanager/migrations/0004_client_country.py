# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dlmanager', '0003_delivery_build_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='client',
            name='country',
            field=models.CharField(default='empty', max_length=63),
            preserve_default=False,
        ),
    ]
