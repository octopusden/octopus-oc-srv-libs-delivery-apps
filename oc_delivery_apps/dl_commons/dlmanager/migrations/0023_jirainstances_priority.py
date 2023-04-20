# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dlmanager', '0022_auto_20190319_0653'),
    ]

    operations = [
        migrations.AddField(
            model_name='jirainstances',
            name='priority',
            field=models.IntegerField(default=0),
        ),
    ]
