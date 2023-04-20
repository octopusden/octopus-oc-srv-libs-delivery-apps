# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dlmanager', '0011_client_language'),
    ]

    operations = [
        migrations.CreateModel(
            name='FtpUploadExtendedClient',
            fields=[
                ('client_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='dlmanager.Client', on_delete=models.CASCADE)),
                ('should_encrypt', models.BooleanField(default=True)),
            ],
            bases=('dlmanager.client',),
        ),
    ]
