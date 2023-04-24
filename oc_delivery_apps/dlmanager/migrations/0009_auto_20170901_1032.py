# -*- coding: utf-8 -*-
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dlmanager', '0008_client_is_active'),
    ]

    operations = [
        migrations.AlterField(
            model_name='client',
            name='is_active',
            field=models.BooleanField(default=False),
        ),
    ]
