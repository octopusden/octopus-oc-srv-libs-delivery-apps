# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dlmanager', '0017_privatefile'),
    ]

    operations = [
        migrations.CreateModel(
            name='JiraProjects',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('code', models.CharField(max_length=255)),
                ('int_url', models.CharField(max_length=255)),
                ('ext_url', models.CharField(max_length=255)),
                ('description', models.CharField(max_length=255)),
            ],
            options={
                'managed': True,
            },
        ),
    ]
