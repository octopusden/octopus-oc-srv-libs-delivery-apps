# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('checksums', '0009_auto_20171204_0100'),
    ]

    operations = [
        migrations.CreateModel(
            name='CiTypeGroups',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('code', models.CharField(unique=True, max_length=32, blank=False, null=False)),
                ('name', models.CharField(max_length=64, blank=False, null=False)),
                ('rn_gav', models.CharField(max_length=255, null=True, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='CiTypeIncs',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('ci_type', models.ForeignKey(to='checksums.CiTypes', to_field='code', on_delete=models.CASCADE, blank=False, null=False)),
                ('ci_type_group', models.ForeignKey(to='checksums.CiTypeGroups', to_field='code', on_delete=models.CASCADE, blank=False, null=False)),
            ],
        ),
    ]
