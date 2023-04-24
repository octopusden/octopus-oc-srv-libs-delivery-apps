# -*- coding: utf-8 -*-
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dlmanager', '0021_AddedUniqueFields'),
    ]

    operations = [
        migrations.AddField(
            model_name='jirainstances',
            name='code',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='jiraprojects',
            name='code',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='jiraprojects',
            name='project_id',
            field=models.IntegerField(null=True, blank=True),
        ),
    ]
