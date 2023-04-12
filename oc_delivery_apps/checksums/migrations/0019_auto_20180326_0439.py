# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('checksums', '0018_auto_20180312_0116'),
    ]

    operations = [
        migrations.CreateModel(
            name='CheckSumsNst',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('cs_prov', models.CharField(max_length=64, blank=False, null=False)),
                ('checksum', models.CharField(max_length=64, blank=False, null=False)),
                ('cs_type', models.ForeignKey(to='checksums.CsTypes', to_field='code', on_delete=models.CASCADE, blank=False, null=False)),
            ],
        ),
        migrations.CreateModel(
            name='CsProv',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('cs_prov', models.CharField(max_length=64, blank=False, null=False)),
                ('cs', models.ForeignKey(to='checksums.CheckSums', on_delete=models.CASCADE, blank=False, null=False)),
            ],
        ),
        migrations.CreateModel(
            name='CsProvNst',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('cs_prov', models.CharField(max_length=64, blank=False, null=False)),
                ('cs', models.ForeignKey(to='checksums.CheckSumsNst', on_delete=models.CASCADE, blank=False, null=False)),
            ],
        ),
        migrations.AddField(
            model_name='files',
            name='file_dup',
            field=models.ForeignKey(blank=True, to='checksums.Files', null=True, on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='checksumsnst',
            name='file',
            field=models.ForeignKey(to='checksums.Files', on_delete=models.CASCADE, blank=False, null=False),
        ),
        migrations.AlterIndexTogether(
            name='csprovnst',
            index_together=set([('cs', 'cs_prov')]),
        ),
        migrations.AlterUniqueTogether(
            name='csprov',
            unique_together=set([('cs', 'cs_prov')]),
        ),
        migrations.AlterIndexTogether(
            name='checksumsnst',
            index_together=set([('checksum', 'cs_prov')]),
        ),
    ]
