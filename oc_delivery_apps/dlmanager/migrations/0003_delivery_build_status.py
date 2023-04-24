# -*- coding: utf-8 -*-
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dlmanager', '0002_remove_delivery_build_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='delivery',
            name='build_status',
            field=models.CharField(max_length=127, null=True, blank=True),
        ),
    ]
