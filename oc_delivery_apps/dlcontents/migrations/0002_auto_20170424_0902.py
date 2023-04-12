# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models, connection


class Migration(migrations.Migration):

    dependencies = [
        ('dlcontents', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='citypes',
            name='code',
            field=models.CharField(unique=True, max_length=32),
        ),
        migrations.AlterField(
            model_name='cstypes',
            name='code',
            field=models.CharField(unique=True, max_length=32),
        ),
        migrations.AlterField(
            model_name='loctypes',
            name='code',
            field=models.CharField(unique=True, max_length=32),
        ),
    ]

    if 'postgresql' in connection.settings_dict['ENGINE'] :
      operations += [
        migrations.RunSQL("alter table dlcontents_locations alter column loc_type_id type varchar(32)"),
        migrations.RunSQL("alter table dlcontents_files alter column ci_type_id type varchar(32)"),
        migrations.RunSQL("alter table dlcontents_checksums alter column cs_type_id type varchar(32)"),
    ]

