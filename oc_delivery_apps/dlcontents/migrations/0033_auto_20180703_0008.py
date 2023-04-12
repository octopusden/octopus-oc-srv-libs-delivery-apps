# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dlcontents', '0032_auto_20180529_0123'),
    ]

    operations = [
        migrations.CreateModel(
            name='CiTypeDms',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('dms_id', models.CharField(max_length=256, null=True, blank=True)),
                ('ci_type', models.ForeignKey(to='dlcontents.CiTypes', to_field='code', on_delete=models.CASCADE, blank=False, null=False)),
            ],
        ),
    ]
