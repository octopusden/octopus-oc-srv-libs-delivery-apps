# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dlcontents', '0002_auto_20170424_0902'),
    ]

    operations = [
        migrations.CreateModel(
            name='CiRegExp',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('regexp', models.CharField(max_length=4096, blank=False, null=False)),
            ],
        ),
        migrations.AddField(
            model_name='citypes',
            name='is_standard',
            field=models.CharField(default=b'N', max_length=8, blank=False, null=False),
        ),
        migrations.AddField(
            model_name='ciregexp',
            name='ci_type',
            field=models.ForeignKey(to='dlcontents.CiTypes', to_field='code', on_delete=models.CASCADE, blank=False, null=False),
        ),
        migrations.AddField(
            model_name='ciregexp',
            name='loc_type',
            field=models.ForeignKey(to='dlcontents.LocTypes', to_field='code', on_delete=models.CASCADE, blank=False, null=False),
        ),
    ]
