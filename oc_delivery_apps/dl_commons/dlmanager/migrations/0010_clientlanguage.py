# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dlmanager', '0009_auto_20170901_1032'),
    ]

    operations = [
        migrations.CreateModel(
            name='ClientLanguage',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                 serialize=False, auto_created=True, primary_key=True)),
                ('code', models.CharField(unique=True, max_length=20)),
                ('description', models.CharField(unique=True, max_length=20)),
            ],
        ),
    ]
