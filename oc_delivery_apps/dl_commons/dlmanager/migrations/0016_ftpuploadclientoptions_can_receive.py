# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dlmanager', '0015_delete_dl_status_rollback'),
    ]

    operations = [
        migrations.AddField(
            model_name='ftpuploadclientoptions',
            name='can_receive',
            field=models.BooleanField(default=True),
        ),
    ]
