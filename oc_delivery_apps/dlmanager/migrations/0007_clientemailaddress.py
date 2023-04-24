# -*- coding: utf-8 -*-
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dlmanager', '0006_auto_20170113_1749'),
    ]

    operations = [
        migrations.CreateModel(
            name='ClientEmailAddress',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                 serialize=False, auto_created=True, primary_key=True)),
                ('email_address', models.CharField(max_length=255)),
                ('clientid', models.ForeignKey(to='dlmanager.Client',
                 db_column='clientId', on_delete=models.CASCADE)),
            ],
        ),
    ]
