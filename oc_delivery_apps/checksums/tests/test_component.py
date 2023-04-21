#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# unit-tests for checksums Components (abstraction overlay on CiType)

import django.test
from . import django_settings
from oc_delivery_apps.checksums.Component import Component
import oc_delivery_apps.checksums.models as models #for database records creation

class CheckSumsComponentTest(django.test.TransactionTestCase):
    def setUp(self):
        django.core.management.call_command('migrate', verbosity=0, interactive=False)

    def tearDown(self):
        django.core.management.call_command('flush', verbosity=0, interactive=False)

    def test_get_all_components__no_file(self):
        with self.assertRaises(models.CiTypes.DoesNotExist):
            Component.get_all_components()

    def test_get_all_names__no_file(self):
        with self.assertRaises(models.CiTypes.DoesNotExist):
            Component.get_all_names()

    def test_get_all_components__ok(self):
        # add test records and regexps
        _loc_type = models.LocTypes(code="NXS", name="Maven compatible")
        _loc_type.save()
        _t1 = models.CiTypes(code="TYPE1", name="Type One", is_standard="N", is_deliverable=False)
        _t1.save()
        _t2 = models.CiTypes(code="TYPE2", name="Type Two", is_standard="Y", is_deliverable=True)
        _t2.save()
        _tf = models.CiTypes(code="FILE", name="File", is_standard="N", is_deliverable=True)
        _tf.save()

        for _t in [_t1, _t2]:
            for _idx in range(0, 2):
                models.CiRegExp(ci_type=_t, loc_type=_loc_type, regexp="Rec%s%d" % (_t.code, _idx)).save()

        # note: 'FILE' should be the first one
        _all_types = Component.get_all_components()
        _file = _all_types.pop(0)
        self.assertEqual(_file.short_name, "FILE")
        self.assertEqual(_file.full_name, "File")
        self.assertEqual(len(_file.stubs), 0)
        self.assertEqual(len(_all_types), 2)
        # note: ordering is by 'is_standard' field first, and 'name' - second
        self.assertEqual(list(map(lambda x: x.full_name, _all_types)), ["Type Two", "Type One"])
        for _t in _all_types:
            self.assertEqual(len(range(0, 2)), len(_t.stubs))
            for _idx in range(0, 2):
                self.assertIn("Rec%s%d" % (_t.short_name, _idx), _t.stubs)

    def test_get_all_names__ok(self):
        _loc_type = models.LocTypes(code="NXS", name="Maven compatible")
        _loc_type.save()
        _t1 = models.CiTypes(code="TYPE1", name="Type One", is_standard="N", is_deliverable=False)
        _t1.save()
        _t2 = models.CiTypes(code="TYPE2", name="Type Two", is_standard="Y", is_deliverable=True)
        _t2.save()
        _tf = models.CiTypes(code="FILE", name="File", is_standard="N", is_deliverable=True)
        _tf.save()

        for _t in [_t1, _t2]:
            for _idx in range(0, 2):
                models.CiRegExp(ci_type=_t, loc_type=_loc_type, regexp="Rec%s%d" % (_t.code, _idx)).save()

        _all_names = Component.get_all_names()
        self.assertEqual(("FILE", "File"), _all_names.pop(0))
        self.assertEqual([('TYPE2', "Type Two"),('TYPE1', "Type One")], _all_names)
