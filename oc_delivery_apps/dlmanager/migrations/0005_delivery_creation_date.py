# -*- coding: utf-8 -*-
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dlmanager', '0004_client_country'),
    ]

    operations = [
        migrations.AddField(
            model_name='delivery',
            name='creation_date',
            field=models.DateTimeField(null=True, blank=True),
        ),
    ]
