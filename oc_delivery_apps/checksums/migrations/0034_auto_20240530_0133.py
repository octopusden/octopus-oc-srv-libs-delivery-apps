# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('checksums', '0033_auto_20200117_0810'),
    ]

    operations = [
        migrations.AlterField(
            model_name='citypegroups',
            name='code',
            field=models.CharField(unique=True, max_length=127),
        ),
        migrations.AlterField(
            model_name='citypegroups',
            name='doc_artifactid',
            field=models.CharField(max_length=1023, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='citypegroups',
            name='name',
            field=models.CharField(max_length=511),
        ),
        migrations.AlterField(
            model_name='citypegroups',
            name='rn_artifactid',
            field=models.CharField(max_length=1023, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='citypes',
            name='code',
            field=models.CharField(unique=True, max_length=127),
        ),
        migrations.AlterField(
            model_name='citypes',
            name='doc_artifactid',
            field=models.CharField(max_length=1023, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='citypes',
            name='name',
            field=models.CharField(unique=True, max_length=511),
        ),
        migrations.AlterField(
            model_name='citypes',
            name='rn_artifactid',
            field=models.CharField(max_length=1023, null=True, blank=True),
        )
    ]
