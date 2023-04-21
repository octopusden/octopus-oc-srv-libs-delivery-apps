# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dlmanager', '0018_jiraprojects'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='jiraprojects',
            name='description',
        ),
        migrations.AddField(
            model_name='jiraprojects',
            name='name',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='jiraprojects',
            name='project_id',
            field=models.IntegerField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='jiraprojects',
            name='code',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='jiraprojects',
            name='ext_url',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='jiraprojects',
            name='int_url',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
    ]
