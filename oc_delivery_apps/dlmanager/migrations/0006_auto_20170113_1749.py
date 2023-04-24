# -*- coding: utf-8 -*-
from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('dlmanager', '0005_delivery_creation_date'),
    ]

    operations = [
        migrations.CreateModel(
            name='BusinessStatus',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                 serialize=False, auto_created=True, primary_key=True)),
                ('description', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='HistoricalBusinessStatus',
            fields=[
                ('id', models.IntegerField(verbose_name='ID',
                 db_index=True, auto_created=True, blank=True)),
                ('description', models.CharField(max_length=100)),
                ('history_id', models.AutoField(serialize=False, primary_key=True)),
                ('history_date', models.DateTimeField()),
                ('history_type', models.CharField(max_length=1, choices=[
                 ('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')])),
                ('history_user', models.ForeignKey(related_name='+',
                 on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': 'history_date',
                'verbose_name': 'historical business status',
            },
        ),
        migrations.CreateModel(
            name='HistoricalDelivery',
            fields=[
                ('id', models.IntegerField(verbose_name='ID',
                 db_index=True, auto_created=True, blank=True)),
                ('groupid', models.CharField(max_length=255, db_column='groupId')),
                ('artifactid', models.CharField(
                    max_length=127, db_column='artifactId')),
                ('version', models.CharField(max_length=63)),
                ('flag_approved', models.BooleanField(default=False)),
                ('flag_uploaded', models.BooleanField(default=False)),
                ('flag_failed', models.BooleanField(default=False)),
                ('request_date', models.DateTimeField(null=True, blank=True)),
                ('creation_date', models.DateTimeField(null=True, blank=True)),
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
                ('comment', models.CharField(max_length=1000, blank=True)),
                ('history_id', models.AutoField(serialize=False, primary_key=True)),
                ('history_date', models.DateTimeField()),
                ('history_type', models.CharField(max_length=1, choices=[
                 ('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')])),
                ('business_status', models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.DO_NOTHING,
                 db_constraint=False, blank=True, to='dlmanager.BusinessStatus', null=True)),
                ('history_user', models.ForeignKey(related_name='+',
                 on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': 'history_date',
                'verbose_name': 'historical delivery',
            },
        ),
        migrations.AddField(
            model_name='delivery',
            name='comment',
            field=models.CharField(max_length=1000, blank=True),
        ),
        migrations.AddField(
            model_name='delivery',
            name='business_status',
            field=models.ForeignKey(
                to='dlmanager.BusinessStatus', null=True, on_delete=models.CASCADE),
        ),
    ]
