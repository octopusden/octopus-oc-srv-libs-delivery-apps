# -*- coding: utf-8 -*-
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dlmanager', '0019_auto_20190219_0909'),
    ]

    operations = [
        migrations.CreateModel(
            name='JiraInstances',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                 serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255, null=True, blank=True)),
                ('api_url', models.CharField(max_length=255, null=True, blank=True)),
                ('int_url_prefix', models.CharField(
                    max_length=255, null=True, blank=True)),
                ('ext_url_prefix', models.CharField(
                    max_length=255, null=True, blank=True)),
            ],
            options={
                'managed': True,
            },
        ),
        migrations.RemoveField(
            model_name='jiraprojects',
            name='ext_url',
        ),
        migrations.RemoveField(
            model_name='jiraprojects',
            name='int_url',
        ),
        migrations.AddField(
            model_name='jiraprojects',
            name='instance_id',
            field=models.ForeignKey(
                blank=True, to='dlmanager.JiraInstances', null=True, on_delete=models.CASCADE),
        ),
    ]
