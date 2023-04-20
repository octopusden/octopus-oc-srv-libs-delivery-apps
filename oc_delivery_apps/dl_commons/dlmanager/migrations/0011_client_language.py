# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dlmanager', '0010_clientlanguage'),
    ]

    operations = [
        migrations.AddField(
            model_name='client',
            name='language',
            field=models.ForeignKey(to='dlmanager.ClientLanguage', null=True, on_delete=models.CASCADE),
        ),
    ]
