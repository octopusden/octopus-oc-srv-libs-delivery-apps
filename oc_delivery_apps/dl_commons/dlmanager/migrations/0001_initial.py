# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Client',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                 serialize=False, auto_created=True, primary_key=True)),
                ('code', models.CharField(max_length=63)),
            ],
        ),
        migrations.CreateModel(
            name='ClientUser',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                 serialize=False, auto_created=True, primary_key=True)),
                ('clientid', models.ForeignKey(to='dlmanager.Client',
                 db_column='clientId', on_delete=models.CASCADE)),
                ('userid', models.ForeignKey(to=settings.AUTH_USER_MODEL,
                 db_column='userId', on_delete=models.CASCADE)),
            ],
        ),
        migrations.CreateModel(
            name='Delivery',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                 serialize=False, auto_created=True, primary_key=True)),
                ('groupid', models.CharField(max_length=255, db_column='groupId')),
                ('artifactid', models.CharField(
                    max_length=127, db_column='artifactId')),
                ('version', models.CharField(max_length=63)),
                ('flag_approved', models.BooleanField(default=False)),
                ('flag_uploaded', models.BooleanField(default=False)),
                ('flag_failed', models.BooleanField(default=False)),
                ('request_date', models.DateTimeField(null=True, blank=True)),
                ('request_by', models.CharField(
                    max_length=127, null=True, blank=True)),
                ('mf_delivery_revision', models.IntegerField(null=True, blank=True)),
                ('mf_delivery_author', models.CharField(
                    max_length=127, null=True, blank=True)),
                ('mf_source_svn', models.CharField(
                    max_length=511, null=True, blank=True)),
                ('mf_ci_build', models.IntegerField(null=True, blank=True)),
                ('mf_ci_job', models.CharField(max_length=63, null=True, blank=True)),
                ('mf_tag_svn', models.CharField(
                    max_length=511, null=True, blank=True)),
                ('mf_delivery_comment', models.TextField(null=True, blank=True)),
                ('mf_delivery_files_specified',
                 models.TextField(null=True, blank=True)),
                ('build_status', models.CharField(
                    max_length=127, null=True, blank=True)),
            ],
            options={
                'ordering': ['-request_date'],
                'db_table': 'deliveries',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='DeliveryHistory',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                 serialize=False, auto_created=True, primary_key=True)),
                ('time', models.DateTimeField()),
                ('change_by', models.TextField(null=True, blank=True)),
                ('flag_approved', models.NullBooleanField()),
                ('flag_uploaded', models.NullBooleanField()),
                ('flag_failed', models.NullBooleanField()),
                ('message', models.TextField(null=True, blank=True)),
                ('deliveryid', models.ForeignKey(to='dlmanager.Delivery',
                 db_column='deliveryId', on_delete=models.CASCADE)),
            ],
            options={
                'db_table': 'delivery_history',
                'managed': True,
            },
        ),
        migrations.AlterUniqueTogether(
            name='delivery',
            unique_together=set([('groupid', 'artifactid', 'version')]),
        ),
    ]
