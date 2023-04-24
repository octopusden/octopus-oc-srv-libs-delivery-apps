# -*- coding: utf-8 -*-
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dlmanager', '0020_JiraInstances_Table_Addition'),
    ]

    operations = [
        migrations.AlterField(
            model_name='jiraprojects',
            name='code',
            field=models.CharField(
                max_length=255, unique=True, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='jiraprojects',
            name='project_id',
            field=models.IntegerField(unique=True, null=True, blank=True),
        ),
    ]
