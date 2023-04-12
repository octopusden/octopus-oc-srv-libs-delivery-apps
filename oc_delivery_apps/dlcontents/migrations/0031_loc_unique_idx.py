# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models, connection


class Migration(migrations.Migration):

    dependencies = [
        ('dlcontents', '0030_remove_dup_locations'),
    ]

    operations = [
    ]

    if 'postgresql' in connection.settings_dict['ENGINE'] :
        operations += [
            migrations.RunSQL("create unique index dlcontents_locations_uidx on dlcontents_locations(coalesce(path, ''), coalesce(loc_type_id, ''), coalesce(file_dst_id, 0), coalesce(revision, ''))"),
            migrations.RunSQL("create index dlcontents_historicallocations_uidx on dlcontents_historicallocations(coalesce(path, ''), coalesce(loc_type_id, ''), coalesce(file_dst_id, 0), coalesce(revision, ''))"),
        ]

    if 'sqlite3' in connection.settings_dict['ENGINE'] :
        operations += [
            migrations.RunSQL("create unique index dlcontents_locations_uidx on dlcontents_locations(ifnull(path, ''), ifnull(loc_type_id, ''), ifnull(file_dst_id, 0), ifnull(revision, ''))"),
            migrations.RunSQL("create index dlcontents_historicallocations_uidx on dlcontents_historicallocations(ifnull(path, ''), ifnull(loc_type_id, ''), ifnull(file_dst_id, 0), ifnull(revision, ''))"),
        ]


