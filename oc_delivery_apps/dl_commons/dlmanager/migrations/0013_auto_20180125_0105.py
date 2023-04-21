# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dlmanager', '0012_ftpuploadextendedclient'),
    ]

    operations = [
        migrations.CreateModel(
            name='FtpUploadClientOptions',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                 serialize=False, auto_created=True, primary_key=True)),
                ('should_encrypt', models.BooleanField(default=True)),
                ('client', models.OneToOneField(
                    to='dlmanager.Client', on_delete=models.CASCADE)),
            ],
        ),
        migrations.RemoveField(
            model_name='ftpuploadextendedclient',
            name='client_ptr',
        ),
        migrations.DeleteModel(
            name='FtpUploadExtendedClient',
        ),
    ]
