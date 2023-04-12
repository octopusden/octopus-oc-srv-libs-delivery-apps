# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='CheckSums',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('cs_prov', models.CharField(max_length=64, blank=False, null=False)),
                ('checksum', models.CharField(max_length=64, blank=False, null=False)),
            ],
        ),
        migrations.CreateModel(
            name='CiTypes',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('code', models.CharField(unique=True, max_length=8, blank=False, null=False)),
                ('name', models.CharField(unique=True, max_length=64, blank=False, null=False)),
            ],
        ),
        migrations.CreateModel(
            name='CsTypes',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('code', models.CharField(unique=True, max_length=8, blank=False, null=False)),
                ('name', models.CharField(unique=True, max_length=64, blank=False, null=False)),
            ],
        ),
        migrations.CreateModel(
            name='Files',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('mime_type', models.CharField(max_length=512, blank=False, null=False)),
                ('ci_type', models.ForeignKey(to='checksums.CiTypes', to_field='code', on_delete=models.CASCADE, blank=False, null=False)),
            ],
        ),
        migrations.CreateModel(
            name='Locations',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('path', models.CharField(max_length=4096, blank=False, null=False)),
                ('input_date', models.DateTimeField(auto_now_add=True, blank=False, null=False)),
                ('file', models.ForeignKey(to='checksums.Files', on_delete=models.CASCADE, blank=False, null=False)),
            ],
        ),
        migrations.CreateModel(
            name='LocTypes',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('code', models.CharField(unique=True, max_length=8, blank=False, null=False)),
                ('name', models.CharField(unique=True, max_length=64, blank=False, null=False)),
            ],
        ),
        migrations.AddField(
            model_name='locations',
            name='loc_type',
            field=models.ForeignKey(to='checksums.LocTypes', to_field='code', on_delete=models.CASCADE, blank=False, null=False),
        ),
        migrations.AddField(
            model_name='checksums',
            name='cs_type',
            field=models.ForeignKey(to='checksums.CsTypes', to_field='code', on_delete=models.CASCADE, blank=False, null=False),
        ),
        migrations.AddField(
            model_name='checksums',
            name='file',
            field=models.ForeignKey(to='checksums.Files', on_delete=models.CASCADE, blank=False, null=False),
        ),
    ]
