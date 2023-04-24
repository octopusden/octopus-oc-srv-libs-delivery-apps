# -*- coding: utf-8 -*-
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dlmanager', '0016_ftpuploadclientoptions_can_receive'),
    ]

    operations = [
        migrations.CreateModel(
            name='PrivateFile',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                 serialize=False, auto_created=True, primary_key=True)),
                ('regexp', models.CharField(max_length=1000)),
            ],
        ),
    ]
