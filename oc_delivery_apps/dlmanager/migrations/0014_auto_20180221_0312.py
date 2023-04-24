# -*- coding: utf-8 -*-
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dlmanager', '0013_auto_20180125_0105'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicalbusinessstatus',
            name='history_change_reason',
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='historicaldelivery',
            name='history_change_reason',
            field=models.CharField(max_length=100, null=True),
        ),
    ]
