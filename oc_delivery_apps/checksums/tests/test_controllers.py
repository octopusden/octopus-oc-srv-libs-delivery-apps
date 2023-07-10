#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# unit-tests for checksums controllers

import django.test
from . import django_settings
from oc_delivery_apps.checksums.controllers import CheckSumsController
import oc_delivery_apps.checksums.models as models
import tempfile
import string
import random
from django.db import IntegrityError
import unittest.mock
import zipfile
import tarfile
import os
from oc_sql_helpers.normalizer import PLSQLNormalizationFlags

# disable extra logging output
import logging
logging.getLogger().propagate = False
logging.getLogger().disabled = True

class CheckSumsControllersTester(django.test.TransactionTestCase):
    def setUp(self):
        #django.core.management.call_command('migrate', run_syncdb=True, verbosity=0, interactive=False)
        django.core.management.call_command('migrate', verbosity=0, interactive=False)

    def tearDown(self):
        django.core.management.call_command('flush', verbosity=0, interactive=False)

    def test_get_file_by_checksum__prov(self):
        self.assertEqual(models.CsProv.objects.count(), 0)
        self.assertEqual(models.CheckSums.objects.count(), 0)
        # add file, checksum and provider
        _cs_t = "0"*32
        _citype = models.CiTypes(code="CODE_TYPE", name="Name", is_standard="N", is_deliverable=False)
        _citype.save()
        _f = models.Files(mime_type="mime/type", ci_type=_citype)
        _f.save()
        _cs_type = models.CsTypes(code="CODE_CS", name="Checksums Type Code")
        _cs_type.save()
        _cs = models.CheckSums(checksum=_cs_t, file=_f, cs_type=_cs_type)
        _cs.save()
        _csp =  models.CsProv(cs=_cs, cs_prov="Regular")
        _csp.save()
        _result = CheckSumsController().get_file_by_checksum(_cs_t, cs_type="CODE_CS")
        self.assertEqual(_result, _f)

    def test_get_file_by_checksum__strict(self):
        self.assertEqual(models.CsProv.objects.count(), 0)
        self.assertEqual(models.CheckSums.objects.count(), 0)
        _cs_t = "0"*32
        _citype = models.CiTypes(code="CODE_TYPE", name="Name", is_standard="N", is_deliverable=False)
        _citype.save()
        _f = models.Files(mime_type="mime/type", ci_type=_citype)
        _f.save()
        _cs_type = models.CsTypes(code="CODE_CS", name="Checksums Type Code")
        _cs_type.save()
        _cs = models.CheckSums(checksum=_cs_t, file=_f, cs_type=_cs_type)
        _cs.save()
        # not searching for provider this case, skipped
        _result = CheckSumsController().get_file_by_checksum(_cs_t, cs_type="CODE_CS")
        self.assertEqual(_result, _f)

    def test_get_file_by_checksum__none(self):
        self.assertEqual(models.CsProv.objects.count(), 0)
        self.assertEqual(models.CheckSums.objects.count(), 0)
        _c = CheckSumsController()
        self.assertIsNone(_c.get_file_by_checksum('0aaaaabbbbbcccccdddddeeeeefffff0'))
        self.assertIsNone(_c.get_file_by_checksum('71452134635635462345345324532453', 
            cs_prov="Wondered", cs_type="MD6"))

    def test_get_checksum_by_file__ok(self):
        # register file and checksum, then get it back
        self.assertEqual(models.CsProv.objects.count(), 0)
        self.assertEqual(models.CheckSums.objects.count(), 0)
        # add file, checksum and provider
        _cs_t = "0"*32
        _citype = models.CiTypes(code="CODE_TYPE", name="Name", is_standard="N", is_deliverable=False)
        _citype.save()
        _f = models.Files(mime_type="mime/type", ci_type=_citype)
        _f.save()
        _cs_type = models.CsTypes(code="CODE_CS", name="Checksums Type Code")
        _cs_type.save()
        _cs = models.CheckSums(checksum=_cs_t, file=_f, cs_type=_cs_type)
        _cs.save()
        _csp =  models.CsProv(cs=_cs, cs_prov="Regular")
        _csp.save()
        _result = CheckSumsController().get_checksum_by_file(_f, cs_type="CODE_CS")
        self.assertEqual(_result, _cs_t)

    def test_get_checksum_by_file__fail(self):
        self.assertEqual(models.CsProv.objects.count(), 0)
        self.assertEqual(models.CheckSums.objects.count(), 0)
        # register file but do not register checksum
        _cs_t = "0"*32
        _citype = models.CiTypes(code="CODE_TYPE", name="Name", is_standard="N", is_deliverable=False)
        _citype.save()
        _f = models.Files(mime_type="mime/type", ci_type=_citype)
        _f.save()
        self.assertIsNone(CheckSumsController().get_checksum_by_file(_f, cs_type="CODE_CS"))


    def test_get_file_by_location__ok(self):
        # register file with location and try to find it
        self.assertEqual(models.Files.objects.count(), 0)
        _cs_t = "0"*32
        _citype = models.CiTypes(code="CODE_TYPE", name="Name", is_standard="N", is_deliverable=False)
        _citype.save()
        _f = models.Files(mime_type="mime/type", ci_type=_citype)
        _f.save()
        _cs_type = models.CsTypes(code="MD5", name="MD5 Checksum")
        _cs_type.save()
        _cs = models.CheckSums(checksum=_cs_t, file=_f, cs_type=_cs_type)
        _cs.save()
        _csp =  models.CsProv(cs=_cs, cs_prov="Regular")
        _csp.save()
        _loc_type = models.LocTypes(code="SVN", name="SubVersion")
        _loc_type.save()
        _loc_p = "https://svn.example.com/svn/file.txt"
        _location = models.Locations(file=_f, path=_loc_p, loc_type=_loc_type, revision=0)
        _location.save()
        _cs = CheckSumsController()
        _result = _cs.get_file_by_location(_loc_p, loc_type="SVN", revision=0, history=False)
        self.assertEqual(_result, _f)

    def test_get_file_by_location__hist(self):
        # register file with location, then delete and try to find it with history
        self.assertEqual(models.Files.objects.count(), 0)
        _cs_t = "0"*32
        _citype = models.CiTypes(code="CODE_TYPE", name="Name", is_standard="N", is_deliverable=False)
        _citype.save()
        _f = models.Files(mime_type="mime/type", ci_type=_citype)
        _f.save()
        _cs_type = models.CsTypes(code="MD5", name="MD5 Checksum")
        _cs_type.save()
        _cs = models.CheckSums(checksum=_cs_t, file=_f, cs_type=_cs_type)
        _cs.save()
        _csp =  models.CsProv(cs=_cs, cs_prov="Regular")
        _csp.save()
        _loc_type = models.LocTypes(code="SVN", name="SubVersion")
        _loc_type.save()
        _loc_p = "https://svn.example.com/svn/file.txt"
        _location = models.Locations(file=_f, path=_loc_p, loc_type=_loc_type, revision=0)
        _location.save()
        _location.delete()
        self.assertEqual(models.Locations.objects.count(), 0)
        _cs = CheckSumsController()
        _result = _cs.get_file_by_location(_loc_p, loc_type="SVN", revision=0, history=False)
        self.assertIsNone(_result)
        _result = _cs.get_file_by_location(_loc_p, loc_type="SVN", revision=0, history=True)
        self.assertEqual(_result, _f)

    def test_get_file_by_location__none(self):
        self.assertEqual(models.Files.objects.count(), 0)
        self.assertEqual(models.Locations.objects.count(), 0)
        _cs = CheckSumsController()
        _loc_p = "https://svn.example.com/svn/file.txt"
        self.assertIsNone(_cs.get_file_by_location(_loc_p, loc_type="SVN", revision=0, history=False))
        self.assertIsNone(_cs.get_file_by_location(_loc_p, loc_type="SVN", revision=0, history=True))

    def test_file_exist(self):
        _citype = models.CiTypes(code="CODE_TYPE", name="Name", is_standard="N", is_deliverable=False)
        _citype.save()
        _f = models.Files(mime_type="mime/type", ci_type=_citype)
        _f.save()
        _loc_type = models.LocTypes(code="NXS", name="Maven-compatible storage")
        _loc_type.save()
        _loc_p = "com.example.groupId:artifactId:version:packaging:classifier"
        _location = models.Locations(file=_f, path=_loc_p, loc_type=_loc_type)
        _location.save()
        _cs = CheckSumsController()
        self.assertTrue(_cs.is_file_exist(_f, _loc_p, loc_type="NXS"))
        _location.delete()
        self.assertEqual(models.Locations.objects.count(), 0)
        self.assertFalse(_cs.is_file_exist(_f, _loc_p, loc_type="NXS"))

    def test_add_checksum(self):
        self.assertEqual(models.CheckSums.objects.count(), 0)
        self.assertEqual(models.CsProv.objects.count(), 0)

        ## register a file then add a checksum
        _citype = models.CiTypes(code="CODE_TYPE", name="Name", is_standard="N", is_deliverable=False)
        _citype.save()
        _f = models.Files(mime_type="mime/type", ci_type=_citype)
        _f.save()
        _cs_r = models.CsTypes(code="MD5", name="MD5 checksum")
        _cs_r.save()
        _cs_t = "0"*32
        _cs = CheckSumsController()
        _result = _cs.add_checksum(_f, _cs_t)
        self.assertEqual(models.Files.objects.count(), 1)
        self.assertEqual(models.CheckSums.objects.count(), 1)
        self.assertEqual(models.CsProv.objects.count(), 1)
        _csp = models.CsProv.objects.last()
        _cso = models.CheckSums.objects.last()
        self.assertEqual(_csp.cs, _cso)
        self.assertEqual(_cso.cs_type, _cs_r)
        self.assertEqual(_cso.file, _f)
        self.assertEqual(_cso.checksum, _cs_t)

        ## then try to register it with the same provider and check no duplicate created
        _result = _cs.add_checksum(_f, _cs_t)
        self.assertEqual(models.Files.objects.count(), 1)
        self.assertEqual(models.CheckSums.objects.count(), 1)
        self.assertEqual(models.CsProv.objects.count(), 1)
        _csp = models.CsProv.objects.last()
        _cso = models.CheckSums.objects.last()
        self.assertEqual(_csp.cs, _cso)
        self.assertEqual(_cso.cs_type, _cs_r)
        self.assertEqual(_csp.cs_prov, "Regular")
        self.assertEqual(_cso.file, _f)
        self.assertEqual(_cso.checksum, _cs_t)

        ## then try to register it with another provider and check no duplicate created
        _result = _cs.add_checksum(_f, _cs_t, cs_prov="Wrapped")
        self.assertEqual(models.Files.objects.count(), 1)
        self.assertEqual(models.CheckSums.objects.count(), 1)
        self.assertEqual(models.CsProv.objects.count(), 2)
        _csp = models.CsProv.objects.last()
        _cso = models.CheckSums.objects.last()
        self.assertEqual(_csp.cs, _cso)
        self.assertEqual(_cso.cs_type, _cs_r)
        self.assertEqual(_csp.cs_prov, "Wrapped")
        self.assertEqual(_cso.file, _f)
        self.assertEqual(_cso.checksum, _cs_t)


    def test_add_location(self):
        self.assertEqual(models.Files.objects.count(), 0)
        self.assertEqual(models.Locations.objects.count(), 0)

        # register file and add location to it
        _citype = models.CiTypes(code="CODE_TYPE_1", name="Name One", is_standard="N", is_deliverable=False)
        _citype.save()
        _f = models.Files(mime_type="mime/type", ci_type=_citype)
        _f.save()
        _loc_type = models.LocTypes(code="NXS", name="Maven-compatible storage")
        _loc_type.save()
        _loc_p = "com.example.groupId:artifactId:version:packaging:classifier"

        _cs = CheckSumsController()
        _rslt = _cs.add_location(_f, _loc_p, "NXS")

        self.assertEqual(models.Locations.objects.count(), 1)
        _loc = models.Locations.objects.last()
        self.assertEqual(_loc.path, _loc_p)
        self.assertEqual(_loc.loc_type.code, "NXS")
        self.assertEqual(_loc.file, _f)
        self.assertIsNone(_loc.file_dst)

        # try to do the same again and che"com.example.group.id:artifact_id:0.0.0:pkg1"ck nothing changed
        _rslt = _cs.add_location(_f, _loc_p, "NXS")

        self.assertEqual(models.Locations.objects.count(), 1)
        _loc = models.Locations.objects.last()
        self.assertEqual(_loc.path, _loc_p)
        self.assertEqual(_loc.loc_type.code, "NXS")
        self.assertEqual(_loc.file, _f)
        self.assertIsNone(_loc.file_dst)

        # register another file and try to put it to the same location
        _citype = models.CiTypes(code="CODE_TYPE_2", name="Name Two", is_standard="N", is_deliverable=False)
        _citype.save()
        _f = models.Files(mime_type="mime/type", ci_type=_citype)
        _f.save()

        _rslt = _cs.add_location(_f, _loc_p, "NXS")

        self.assertEqual(models.Locations.objects.count(), 1)
        _loc = models.Locations.objects.last()
        self.assertEqual(_loc.path, _loc_p)
        self.assertEqual(_loc.loc_type.code, "NXS")
        self.assertEqual(_loc.file, _f)
        self.assertIsNone(_loc.file_dst)

        # try to do the same again and check nothing changed
        _rslt = _cs.add_location(_f, _loc_p, "NXS")

        self.assertEqual(models.Locations.objects.count(), 1)
        _loc = models.Locations.objects.last()
        self.assertEqual(_loc.path, _loc_p)
        self.assertEqual(_loc.loc_type.code, "NXS")
        self.assertEqual(_loc.file, _f)
        self.assertIsNone(_loc.file_dst)

        # now try to add SVN without revision
        with self.assertRaises(ValueError):
            _rslt = _cs.add_location(_f, _loc_p, "SVN")

        _loc_type = models.LocTypes(code="SVN", name="SubVersion")
        _loc_type.save()
        _loc_p = "https://svn.example.com/svn/file.txt"
        _loc_rev = 0

        with self.assertRaises(ValueError):
            _rslt = _cs.add_location(_f, _loc_p, "SVN")

        _rslt = _cs.add_location(_f, _loc_p, "SVN", 0)

        self.assertEqual(models.Locations.objects.count(), 2)
        _loc = models.Locations.objects.last()
        self.assertEqual(_loc.path, _loc_p)
        self.assertEqual(_loc.loc_type.code, "SVN")
        self.assertEqual(_loc.file, _f)
        self.assertIsNone(_loc.file_dst)

    def test_is_strict_cs_prov(self):
        _cs = CheckSumsController()
        self.assertFalse(_cs._is_strict_cs_prov("NonExistent"))
        self.assertTrue(_cs._is_strict_cs_prov())
        self.assertTrue(_cs._is_strict_cs_prov("Regular"))
        self.assertTrue(_cs._is_strict_cs_prov("Normed"))
        self.assertTrue(_cs._is_strict_cs_prov("Wrapped"))
        self.assertTrue(_cs._is_strict_cs_prov("Wrapped_Normed"))
        self.assertTrue(_cs._is_strict_cs_prov("Normed_Wrapped"))
        self.assertTrue(_cs._is_strict_cs_prov("Unwrapped"))
        self.assertTrue(_cs._is_strict_cs_prov("Normed_Wrapped_Normed"))
        self.assertTrue(_cs._is_strict_cs_prov("Normed_Wrapped_Unwrapped"))
        self.assertTrue(_cs._is_strict_cs_prov("Unwrapped_Normed"))
        self.assertTrue(_cs._is_strict_cs_prov("Normed_Wrapped_Unwrapped_Normed"))

    def test_add_location_checksum(self):
        # prepare ci_type, cs_type and try to store non-strict first
        self.assertEqual(models.Files.objects.count(), 0)
        self.assertEqual(models.Locations.objects.count(), 0)
        self.assertEqual(models.CheckSums.objects.count(), 0)
        _citype = models.CiTypes(code="CODE_TYPE_1", name="Name One", is_standard="N", is_deliverable=False)
        _citype.save()
        _loctype = models.LocTypes(code="NXS", name="Maven-compatible storage")
        _loctype.save()
        _cstype = models.CsTypes(code="MD5", name="MD5")
        _cstype.save()

        _cs = CheckSumsController()
        _cs_t = "0"*32
        _pth = "com.example.group.id:artifact_id:version:packaging:classifier"
        self.assertFalse(_cs.add_location_checksum(_cs_t, _pth, "NXS", "CODE_TYPE_1", cs_prov="NonStrictOne"))
        self.assertEqual(models.Files.objects.count(), 0)
        self.assertEqual(models.Locations.objects.count(), 0)

        # then try to store strict, should be saved
        self.assertTrue(_cs.add_location_checksum(_cs_t, _pth, "NXS", "CODE_TYPE_1"))
        self.assertEqual(models.Files.objects.count(), 1)
        self.assertEqual(models.Locations.objects.count(), 1)
        self.assertEqual(models.CheckSums.objects.count(), 1)
        self.assertEqual(models.CheckSums.objects.last().cs_type.code, "MD5")
        _f = models.Files.objects.last()
        _loc = models.Locations.objects.last()
        _cs_r = models.CheckSums.objects.last()
        self.assertEqual(_loc.path, _pth)
        self.assertEqual(_cs_r.checksum, _cs_t)

        # store the same, shoud be no chagnes
        self.assertTrue(_cs.add_location_checksum(_cs_t, _pth, "NXS", "CODE_TYPE_1"))
        self.assertEqual(models.Files.objects.count(), 1)
        self.assertEqual(models.Locations.objects.count(), 1)
        self.assertEqual(models.CheckSums.objects.count(), 1)
        _f = models.Files.objects.last()
        _loc = models.Locations.objects.last()
        _cs_r = models.CheckSums.objects.last()
        self.assertEqual(_loc.path, _pth)
        self.assertEqual(_loc.loc_type.code, "NXS")
        self.assertEqual(_cs_r.checksum, _cs_t)

        # store file with the same checksum but in another location
        # new location should be added
        # NOTE: non-existent CI_TYPE is specified, this is NOT A BUG
        _loctype = models.LocTypes(code="SVN", name="SubVersion")
        _loctype.save()

        # first it should raise an erorr - we do not have 'CODE_TYPE_2" here and "FILE" is missing also
        with self.assertRaises(ValueError):
            _cs.add_location_checksum(_cs_t, _pth, "SVN", "CODE_TYPE_2", revision=0)

        # now add the type - error sould disappear
        _citype = models.CiTypes(code="CODE_TYPE_2", name="Name Two", is_standard="N", is_deliverable=False)
        _citype.save()
        self.assertTrue(_cs.add_location_checksum(_cs_t, _pth, "SVN", "CODE_TYPE_2", revision=0))
        self.assertEqual(models.Files.objects.count(), 1)
        self.assertEqual(models.Locations.objects.count(), 2)
        self.assertEqual(models.CheckSums.objects.count(), 1)
        _f = models.Files.objects.last()
        _loc = models.Locations.objects.last()
        _cs_r = models.CheckSums.objects.last()
        self.assertEqual(_loc.path, _pth)
        self.assertEqual(_loc.loc_type.code, "SVN")
        self.assertEqual(_cs_r.checksum, _cs_t)

        # store file with another checksum but for existing location
        # file should be added and location overwritten
        _cs_t = "1"*32
        self.assertTrue(_cs.add_location_checksum(_cs_t, _pth, "SVN", "CODE_TYPE_2", revision=0))
        self.assertEqual(models.Files.objects.count(), 2)
        self.assertEqual(models.Locations.objects.count(), 2)
        self.assertEqual(models.CheckSums.objects.count(), 2)
        _f = models.Files.objects.last()
        _loc = models.Locations.objects.last()
        _cs_r = models.CheckSums.objects.last()
        self.assertEqual(_loc.path, _pth)
        self.assertEqual(_loc.loc_type.code, "SVN")
        self.assertEqual(_cs_r.checksum, _cs_t)

    def test_get_location_checksum(self):
        _cs = CheckSumsController()
        _citype = models.CiTypes(code="CODE_TYPE_1", name="Name One", is_standard="N", is_deliverable=False)
        _citype.save()
        _loctype = models.LocTypes(code="NXS", name="Maven-compatible storage")
        _loctype.save()
        _cstype = models.CsTypes(code="MD5", name="MD5")
        _cstype.save()

        # nonexistent file
        self.assertEqual(models.Locations.objects.count(), 0)
        self.assertEqual(models.CheckSums.objects.count(), 0)
        self.assertIsNone(_cs.get_file_by_checksum("com.example.group.id:artifact_id:0.0.0:pkg:cls", "NXS"))

        # add three files with two locations each and check them all
        for _i in range(0, 4):
            _pth = "com.example.group.id:artifact_id:%d.%d.%d:pkg:cls" % (_i, _i, _i)
            _cs_t = ("%d" % _i)*32
            self.assertTrue(_cs.add_location_checksum(_cs_t, _pth, "NXS", "CODE_TYPE_1"))


        self.assertEqual(models.Locations.objects.count(), len(range(0, 4)))
        self.assertEqual(models.CheckSums.objects.count(), len(range(0, 4)))
        self.assertEqual(models.CsProv.objects.count(), len(range(0, 4)))

        for _i in range(0, 4):
            _pth = "com.example.group.id:artifact_id:%d.%d.%d:pkg:cls" % (_i, _i, _i)
            _cs_t = ("%d" % _i)*32
            self.assertEqual(_cs.get_location_checksum(_pth, "NXS"), _cs_t)

    def test_add_inclusion(self):
        _cs = CheckSumsController()
        _citype = models.CiTypes(code="CODE_TYPE_1", name="Name One", is_standard="N", is_deliverable=False)
        _citype.save()
        # do NOT add it now because we need to test for ValueError first if "ARCH" location type is not registered
        # will be added below
        #_loctype = models.LocTypes(code="ARCH", name="Inside Archive")
        #_loctype.save()
        _loctype = models.LocTypes(code="NXS", name="Maven-compatible")
        _loctype.save()
        _cstype = models.CsTypes(code="MD5", name="MD5")
        _cstype.save()

        _f1 = models.Files(mime_type="Data", ci_type=_citype)
        _f1.save()
        _f2 = models.Files(mime_type="application/archive", ci_type=_citype)
        _f2.save()


        self.assertEqual(models.Locations.objects.count(), 0)

        # add inclusion with no path - ValueError
        with self.assertRaises(ValueError):
            _cs.add_inclusion(_f1, _f2, path="")

        self.assertEqual(models.Locations.objects.count(), 0)

        # child or parent is None - ValueError
        with self.assertRaises(ValueError):
            _cs.add_inclusion(_f1, None, "somefile.txt")

        self.assertEqual(models.Locations.objects.count(), 0)

        with self.assertRaises(ValueError):
            _cs.add_inclusion(None, _f2, "somefile.txt")

        self.assertEqual(models.Locations.objects.count(), 0)


        # add two files with non-registered location type - ValueError
        with self.assertRaises(ValueError):
            _cs.add_inclusion(_f1, _f2, "somefile.txt")

        self.assertEqual(models.Locations.objects.count(), 0)

        _loctype = models.LocTypes(code="ARCH", name="Inside Archive")
        _loctype.save()

        # add file to itself - should be 1 and no changes in the tables
        self.assertEqual(1, _cs.add_inclusion(_f1, _f1, "path.txt"))
        self.assertEqual(models.Locations.objects.count(), 0)

        # add two files - one path inside
        self.assertEqual(1, _cs.add_inclusion(_f1, _f2, "path.txt"))
        self.assertEqual(models.Locations.objects.count(), 1)
        _loc = models.Locations.objects.last()
        self.assertEqual(_loc.loc_type.code, "ARCH")
        self.assertEqual(_loc.file_dst, _f2)
        self.assertEqual(_loc.file, _f1)
        self.assertEqual(_loc.path, "path.txt")

        # add two files - for another path
        self.assertEqual(1, _cs.add_inclusion(_f1, _f2, "another_path.txt"))
        self.assertEqual(models.Locations.objects.count(), 2)
        _loc = models.Locations.objects.last()
        self.assertEqual(_loc.loc_type.code, "ARCH")
        self.assertEqual(_loc.file_dst, _f2)
        self.assertEqual(_loc.file, _f1)
        self.assertEqual(_loc.path, "another_path.txt")

    def test_add_inclusion_checksums(self):
        _cs = CheckSumsController()
        _citype = models.CiTypes(code="CODE_TYPE_1", name="Name One", is_standard="N", is_deliverable=False)
        _citype.save()
        _loctype = models.LocTypes(code="ARCH", name="Inside Archive")
        _loctype.save()
        _loctype = models.LocTypes(code="NXS", name="Maven-compatible")
        _loctype.save()
        _cstype = models.CsTypes(code="MD5", name="MD5")
        _cstype.save()

        _cst_1 = "0"*32
        _cst_2 = "1"*32
        _cst_3 = "3"*32
        _path_1 = "com.example.group.id:artifact_id:0.0.0:pkg"
        _path_2 = "com.example.group.id:artifact_ie:1.1.1:pkg"

        # error if no both
        self.assertEqual(models.CheckSums.objects.count(), 0)

        with self.assertRaises(ValueError):
            _cs.add_inclusion_checksums(_cst_1, _cst_2, "path_1.ext")

        self.assertEqual(_cs.add_inclusion_checksums(_cst_1, _cst_2, "path_1.txt", skip_absent=True), 0)
        self.assertEqual(models.Locations.objects.count(), 0)

        # error if no parent
        _cs.add_location_checksum(_cst_1, _path_1, "NXS", "CODE_TYPE_1")
        self.assertEqual(models.Locations.objects.count(), 1)

        with self.assertRaises(ValueError):
            _cs.add_inclusion_checksums(_cst_1, _cst_2, "path_1.ext")

        self.assertEqual(_cs.add_inclusion_checksums(_cst_1, _cst_2, "path_1.txt", skip_absent=True), 0)
        self.assertEqual(models.Locations.objects.count(), 1)

        # error if no child
        _cs.add_location_checksum(_cst_2, _path_2, "NXS", "CODE_TYPE_1")
        self.assertEqual(models.Locations.objects.count(), 2)

        with self.assertRaises(ValueError):
            _cs.add_inclusion_checksums(_cst_3, _cst_2, "path_1.ext")

        self.assertEqual(_cs.add_inclusion_checksums(_cst_3, _cst_2, "path_1.txt", skip_absent=True), 0)
        self.assertEqual(models.Locations.objects.count(), 2)

        # correct one
        self.assertEqual(_cs.add_inclusion_checksums(_cst_1, _cst_2, "path_1.txt"), 1)
        self.assertEqual(models.Locations.objects.count(), 3)
        _loc = models.Locations.objects.last()
        self.assertEqual(_loc.path, "path_1.txt")
        self.assertIsNotNone(_loc.file_dst)
        self.assertEqual(_loc.loc_type.code, "ARCH")

        # second the same but in another path
        self.assertEqual(_cs.add_inclusion_checksums(_cst_1, _cst_2, "path_2.txt"), 1)
        self.assertEqual(models.Locations.objects.count(), 4)
        _loc = models.Locations.objects.last()
        self.assertEqual(_loc.path, "path_2.txt")
        self.assertIsNotNone(_loc.file_dst)
        self.assertEqual(_loc.loc_type.code, "ARCH")


    def tst_ci_type_by_path(self):
        # add type and some regexps
        _loc_type_1 = models.LocTypes(code="NXS", name="Maven-compatible")
        _loc_type_2 = models.LocTypes(code="SVN", name="SubVersion")
        _loc_type_1.save()
        _loc_type_2.save()

        _ci_type_1 = models.CiTypes(code="TYPE_ONE", name="Type One")
        _ci_type_1.save()
        _ci_type_2 = models.CiTypes(code="TYPE_TWO", name="Type Two")
        _ci_type_2.save()

        models.CiRegExp(regexp="^.*:pkg1$", ci_type=_ci_type_1, loc_type=_loc_type_1).save()
        models.CiRegExp(regexp="^.*\.pkg1$", ci_type=_ci_type_1, loc_type=_loc_type_2).save()
        models.CiRegExp(regexp="^.*:pkg2$", ci_type=_ci_type_2, loc_type=_loc_type_1).save()
        models.CiRegExp(regexp="^.*\.pkg2$", ci_type=_ci_type_2, loc_type=_loc_type_2).save()

        _cs = CheckSumsController()

        # no path given
        with self.assertRaises(ValueError):
            _cs.ci_type_by_path(None, "SVN")

        # no loc_type given
        with self.assertRaises(ValueError):
            _cs.ci_type_by_path("com.example.group.id:artifact_id:0.0.0:pkg1", None)

        # existent
        self.assertEqual(_cs.ci_type_by_path("com.example.group.id:artifact_id:0.0.0:pkg1", "NXS"), "TYPE_ONE")
        self.assertEqual(_cs.ci_type_by_gav("com.example.group.id:artifact_id:0.0.0:pkg1"), "TYPE_ONE")
        self.assertEqual(_cs.ci_type_by_path("http://svn.example.com/svn/com/example/group/id/artifact_id-0.0.0.pkg1", "SVN"), "TYPE_ONE")
        self.assertEqual(_cs.ci_type_by_path("com.example.group.id:artifact_id:0.0.0:pkg2", "NXS"), "TYPE_TWO")
        self.assertEqual(_cs.ci_type_by_gav("com.example.group.id:artifact_id:0.0.0:pkg2"), "TYPE_TWO")
        self.assertEqual(_cs.ci_type_by_path("http://svn.example.com/svn/com/example/group/id/artifact_id-0.0.0.pkg2", "SVN"), "TYPE_TWO")

        # non-existent
        self.assertIsNone(_cs.ci_type_by_path("com.example.group.id:artifact_id:0.0.0:pkg3", "NXS"))
        self.assertIsNone(_cs.ci_type_by_gav("com.example.group.id:artifact_id:0.0.0:pkg3"))
        self.assertIsNone(_cs.ci_type_by_path("http://svn.example.com/svn/com/example/group/id/artifact_id-0.0.0.pkg3", "SVN"))

    def test_md5(self):
        # this is a dummy smoke test, because algorithm is provided by 'hashlib'
        _f = tempfile.NamedTemporaryFile()

        for _i in range(0, random.randint(1024,2048)):
            _f.write(b'%d' % _i)

        self.assertIsNotNone(CheckSumsController().md5(_f))
        _f.close()

    def test_mime(self):
        # this is a dummy smoke test, because algorithm is provided by 'mime' module
        _f = tempfile.NamedTemporaryFile()

        for _i in range(0, random.randint(1024,2048)):
            _f.write(b'%d' % _i)

        self.assertIsNotNone(CheckSumsController().mime(_f))
        _f.close()

    def test_get_file_by_checksums_dict(self):
        # non-strict, strict
        _csc = CheckSumsController()
        _citype = models.CiTypes(code="CODE_TYPE_1", name="Name One", is_standard="N", is_deliverable=False)
        _citype.save()
        _cstype = models.CsTypes(code="MD5", name="MD5")
        _cstype.save()

        _f1 = models.Files(mime_type="text/plain", ci_type = _citype)
        _f1.save()
        _f2 = models.Files(mime_type="text/plain", ci_type = _citype)
        _f2.save()

        # add some checksums for both files
        _cs_strict_f1 = "a" + "1"*31
        _cs_nonstrict_f1 = "b" + "1"*31
        _cs_strict_f2 = "a" + "2"*31
        _cs_nonstrict_f2 = "b" + "2"*31

        _csc.add_checksum(_f1, _cs_strict_f1)
        _csc.add_checksum(_f2, _cs_strict_f2)
        _csc.add_checksum(_f1, _cs_nonstrict_f1, cs_prov="FullNormed")
        _csc.add_checksum(_f2, _cs_nonstrict_f2, cs_prov="FullNormed")

        self.assertEqual(4, models.CheckSums.objects.count())

        self.assertEqual(("Regular", _f1, True), _csc.get_file_by_checksums_dict({"Regular": {"MD5": _cs_strict_f1}}))
        self.assertEqual(("Regular", _f2, True), _csc.get_file_by_checksums_dict({"Regular": {"MD5": _cs_strict_f2}}))
        self.assertIsNone(_csc.get_file_by_checksums_dict({"FullNormed": {"MD5": _cs_nonstrict_f1}}))
        self.assertIsNone(_csc.get_file_by_checksums_dict({"FullNormed": {"MD5": _cs_nonstrict_f2}}))
        self.assertEqual(("FullNormed", _f1, False), _csc.get_file_by_checksums_dict({"FullNormed": {"MD5": _cs_nonstrict_f1}}, strict_only=False))
        self.assertEqual(("FullNormed", _f2, False), _csc.get_file_by_checksums_dict({"FullNormed": {"MD5": _cs_nonstrict_f2}}, strict_only=False))

    def test_get_current_inclusion_depth(self):
        _csc = CheckSumsController()
        _citype = models.CiTypes(code="CODE_TYPE_1", name="Name One", is_standard="N", is_deliverable=False)
        _citype.save()
        _f = models.Files(mime_type="Data", ci_type=_citype)
        _f.save()
        self.assertEqual(0, _csc.get_current_inclusion_depth(_f))
        _f.depth_level = 1
        _f.save()
        _f.depth_level = 2 # Note that '2' is not saved to database, there is now '1'
        self.assertEqual(1, _csc.get_current_inclusion_depth(_f))

    def test_update_current_incluseion_depth(self):
        # should return the maximum of two given
        _csc = CheckSumsController()
        _citype = models.CiTypes(code="CODE_TYPE_1", name="Name One", is_standard="N", is_deliverable=False)
        _citype.save()
        _f = models.Files(mime_type="Data", ci_type=_citype)
        _f.save()
        self.assertEqual(_f, _csc._update_current_inclusion_depth(_f, 1))
        _f.depth_level = 0
        self.assertEqual(1, _csc.get_current_inclusion_depth(_f))

        self.assertEqual(_f, _csc._update_current_inclusion_depth(_f, 0))
        # should left '1'
        self.assertEqual(1, _csc.get_current_inclusion_depth(_f))

    def test_relink_file_duplicate(self):
        # three files, let them be duplicates
        # try to loop linkage also
        # should re-link: checksums, locations, inclusions (locations also), files (file_dup)
        _csc = CheckSumsController()
        
        # citype, loctype, cstype
        _citype = models.CiTypes(code="CODE_TYPE_1", name="Name One", is_standard="N", is_deliverable=False)
        _citype.save()
        _loctype_n = models.LocTypes(code="NXS", name="Maven-compatible")
        _loctype_n.save()
        _loctype_a = models.LocTypes(code="ARCH", name="Inside archive")
        _loctype_a.save()
        _cstype = models.CsTypes(code="MD5", name="MD5")
        _cstype.save()

        # add files
        _ls = ["Normed", "Wrapped", "Wrapped_Normed"]

        for _i in range(0, 4):
            _csc.add_location_checksum(("%d" % _i)*32, "loc:file:%d" % _i, "NXS", "CODE_TYPE_1", cs_prov=(_ls.pop() if _ls else "Regular"))

        # do the links (link loop)
        _fpk = models.Files.objects.first().pk
        _f0 = models.Files.objects.get(pk=_fpk)
        _f1 = models.Files.objects.get(pk=_fpk+1)
        _f2 = models.Files.objects.get(pk=_fpk+2)
        _f3 = models.Files.objects.get(pk=_fpk+3)
        _lpk = _f3.pk
        _link_pk = _lpk

        for _f in models.Files.objects.all():
            _f.file_dup = models.Files.objects.get(pk=_link_pk)
            _f.save()
            _link_pk += 1

            if _link_pk > _lpk:
                _link_pk = _fpk

        for _l in models.Locations.objects.all():
            _l.file_dst = _f3
            _l.loc_type = _loctype_a
            _l.save()

        # now try to re-link, should return file _0
        self.assertEqual(_f0.pk, _csc._relink_file_duplicate(_f2, _f1).pk)

        # check all checksums, locations and files
        for _f in models.Files.objects.all():

            if _f.pk == _fpk:
                self.assertIsNone(_f.file_dup)
                continue

            self.assertEqual(_fpk, _f.file_dup.pk)

        for _c in models.CheckSums.objects.all():
            self.assertEqual(_c.file.pk, _fpk)

        for _l in models.Locations.objects.all():
            self.assertEqual(_l.file.pk, _fpk)
            self.assertEqual(_l.file_dst.pk, _fpk)

    def test_reg_all_sql_cs_provs(self):
        _csc = CheckSumsController()
        
        # citype, loctype, cstype
        _citype = models.CiTypes(code="CODE_TYPE_1", name="Name One", is_standard="N", is_deliverable=False)
        _citype.save()
        _loctype_n = models.LocTypes(code="NXS", name="Maven-compatible")
        _loctype_n.save()
        _cstype = models.CsTypes(code="MD5", name="MD5")
        _cstype.save()

        # clean file record
        _f1 = models.Files(mime_type="text/plain", ci_type=_citype)
        _f1.save()
        _cs_d_1 = {
                "Regular": {"MD5": "1" + "0"*32},
                "Wrapped": {"MD5": "1" + "1"*32},
                "Normed": {"MD5": "1" + "3"*32}}
        self.assertEqual(_f1, _csc._reg_all_sql_cs_provs(_f1, _cs_d_1))
        self.assertEqual(_csc.get_checksum_by_file(_f1, cs_prov="Regular"), "1" + "0"*32)
        self.assertEqual(_csc.get_checksum_by_file(_f1, cs_prov="Wrapped"), "1" + "1"*32)
        self.assertEqual(_csc.get_checksum_by_file(_f1, cs_prov="Normed"), "1" + "3"*32)

        # a duplicate - with exception because of no-relink
        _f2 = models.Files(mime_type="text/plain", ci_type=_citype)
        _f2.save()
        _cs_d_2 = {
                "Regular": {"MD5": "2" + "0"*32},
                "Wrapped": {"MD5": "2" + "1"*32},
                "Normed": {"MD5": "1" + "3"*32}}

        with self.assertRaises(IntegrityError):
            _csc._reg_all_sql_cs_provs(_f2, _cs_d_2)

        self.assertEqual(_csc.get_checksum_by_file(_f1, cs_prov="Regular"), "1" + "0"*32)
        self.assertEqual(_csc.get_checksum_by_file(_f1, cs_prov="Wrapped"), "1" + "1"*32)
        self.assertEqual(_csc.get_checksum_by_file(_f1, cs_prov="Normed"), "1" + "3"*32)
        self.assertEqual(_csc.get_checksum_by_file(_f2, cs_prov="Wrapped"), "2" + "1"*32)
        self.assertIsNone(_csc.get_checksum_by_file(_f2, cs_prov="Normed"))
        self.assertEqual(_csc.get_checksum_by_file(_f2, cs_prov="Regular"), "2" + "0"*32)

        # with a relink
        self.assertEqual(_f1, _csc._reg_all_sql_cs_provs(_f2, _cs_d_2, dup=True))

        self.assertEqual(_csc.get_checksum_by_file(_f1, cs_prov="Regular"), "2" + "0"*32)
        self.assertEqual(_csc.get_checksum_by_file(_f1, cs_prov="Wrapped"), "2" + "1"*32)
        self.assertEqual(_csc.get_checksum_by_file(_f1, cs_prov="Normed"), "1" + "3"*32)
        # all objects should be linked to _f1, so _f2 has no checksums, but is linked to _f1 via 'file_dup'
        _f2.refresh_from_db()
        self.assertEqual(_f2.file_dup, _f1)
        self.assertIsNone(_csc.get_checksum_by_file(_f2, cs_prov="Regular"), "2" + "0"*32)
        self.assertIsNone(_csc.get_checksum_by_file(_f2, cs_prov="Wrapped"), "2" + "1"*32)
        self.assertIsNone(_csc.get_checksum_by_file(_f2, cs_prov="Normed"), "1" + "3"*32)

    def test_register_sql(self):
        _csc = CheckSumsController()

        # citype, loctype, cstype
        _citype = models.CiTypes(code="CODE_TYPE_1", name="Name One", is_standard="N", is_deliverable=False)
        _citype.save()
        _loctype_n = models.LocTypes(code="NXS", name="Maven-compatible")
        _loctype_n.save()
        _cstype = models.CsTypes(code="MD5", name="MD5")
        _cstype.save()

        # make sure DB is empty
        self.assertEqual(models.Files.objects.count(), 0)
        self.assertEqual(models.Locations.objects.count(), 0)
        self.assertEqual(models.CheckSums.objects.count(), 0)

        _f_o = tempfile.NamedTemporaryFile()

        # we have to mock 'get_all_sql_checksums' here to see the result
        _cs_d_1 = {
                "Regular": {"MD5": "1" + "0"*32},
                "Wrapped": {"MD5": "1" + "1"*32},
                "Normed": {"MD5": "1" + "3"*32}}
        _csc.get_all_sql_checksums = unittest.mock.MagicMock(return_value=_cs_d_1)

        # first time we are registering the file in clean database
        _f_r_1 = _csc._register_sql(_f_o, "CODE_TYPE_1", "loc:gav:1", loc_type="NXS", loc_revision=None)
        self.assertEqual(models.Files.objects.count(), 1)
        self.assertEqual(_f_r_1, models.Files.objects.last())
        self.assertEqual(models.Locations.objects.count(), 1)
        _loc_1 = models.Locations.objects.last()
        self.assertEqual(_loc_1.loc_type.code, "NXS")
        self.assertEqual(_loc_1.path, "loc:gav:1")
        self.assertEqual(_loc_1.file, _f_r_1)
        self.assertEqual(models.CheckSums.objects.count(), 3)

        for _cs_r, _vcs in _cs_d_1.items():
            self.assertEqual(models.CsProv.objects.filter(cs_prov=_cs_r, cs__cs_type__code="MD5", cs__checksum=_vcs.get("MD5")).last().cs.file, _f_r_1)

        # try to do the same with incorrect args
        with self.assertRaises(ValueError):
            _csc._register_sql(_f_o, "CODE_TYPE_1", "loc:gav:1", loc_type=None, loc_revision=None)

        self.assertEqual(models.Files.objects.count(), 1)
        self.assertEqual(_f_r_1, models.Files.objects.last())
        self.assertEqual(models.Locations.objects.count(), 1)
        _loc_1 = models.Locations.objects.last()
        self.assertEqual(_loc_1.loc_type.code, "NXS")
        self.assertEqual(_loc_1.path, "loc:gav:1")
        self.assertEqual(_loc_1.file, _f_r_1)

        # try to register another file with no dup relink
        _cs_d_2 = {
                "Regular": {"MD5": "2" + "0"*32},
                "Wrapped": {"MD5": "2" + "1"*32},
                "Normed": {"MD5": "1" + "3"*32}}
        _csc.get_all_sql_checksums = unittest.mock.MagicMock(return_value=_cs_d_2)

        _f_r_2 = _csc._register_sql(_f_o, "CODE_TYPE_1", "loc:gav:2", loc_type="NXS", loc_revision=None)

        self.assertEqual(models.Files.objects.count(), 1) # second should NOT be created because of atomic transaction
        self.assertEqual(_f_r_1, _f_r_2)
        self.assertEqual(models.Locations.objects.count(), 2)
        _loc_2 = models.Locations.objects.last()
        self.assertEqual(_loc_2.loc_type.code, "NXS")
        self.assertEqual(_loc_2.path, "loc:gav:2")
        self.assertEqual(_loc_2.file, _f_r_1)
        self.assertEqual(models.CheckSums.objects.count(), 5)

        for _cs_r, _vcs in _cs_d_1.items():
            self.assertEqual(models.CsProv.objects.filter(cs_prov=_cs_r, cs__cs_type__code="MD5", cs__checksum=_vcs.get("MD5")).last().cs.file, _f_r_1)

        for _cs_r, _vcs in _cs_d_2.items():
            self.assertEqual(models.CsProv.objects.filter(cs_prov=_cs_r, cs__cs_type__code="MD5", cs__checksum=_vcs.get("MD5")).last().cs.file, _f_r_1)

        _f_o.close()

    def test_register_file_md5__with_location(self):
        _csc = CheckSumsController()

        # citype, loctype, cstype
        _citype = models.CiTypes(code="CODE_TYPE_1", name="Name One", is_standard="N", is_deliverable=False)
        _citype.save()
        _loctype_n = models.LocTypes(code="NXS", name="Maven-compatible")
        _loctype_n.save()
        _cstype = models.CsTypes(code="MD5", name="MD5")
        _cstype.save()

        # make sure DB is empty
        self.assertEqual(models.Files.objects.count(), 0)
        self.assertEqual(models.Locations.objects.count(), 0)
        self.assertEqual(models.CheckSums.objects.count(), 0)

        # non-strict cs-prov
        # nothing is to be changed
        _cs1_t="0"*32
        self.assertIsNone(_csc.register_file_md5(_cs1_t, "CODE_TYPE_1", "Data", "loc:path:1", "NXS", cs_prov="FullNormed"))
        self.assertEqual(models.Files.objects.count(), 0)
        self.assertEqual(models.Locations.objects.count(), 0)
        self.assertEqual(models.CheckSums.objects.count(), 0)

        # location without loc_type
        with self.assertRaises(ValueError):
            self.assertIsNone(_csc.register_file_md5(_cs1_t, "CODE_TYPE_1", "Data", "loc:path:1"))

        self.assertEqual(models.Files.objects.count(), 0)
        self.assertEqual(models.Locations.objects.count(), 0)
        self.assertEqual(models.CheckSums.objects.count(), 0)

        # ci_type specified
        _fr_t1 = _csc.register_file_md5(_cs1_t, "CODE_TYPE_1", "Data", "loc:path:1", "NXS")
        self.assertEqual(_fr_t1.ci_type.code, "CODE_TYPE_1")
        self.assertEqual(_csc.get_checksum_by_file(_fr_t1), _cs1_t)
        self.assertEqual(models.Files.objects.count(), 1)
        self.assertEqual(models.Locations.objects.count(), 1)
        self.assertEqual(models.CheckSums.objects.count(), 1)

        # ci_type autodetect
        _citype = models.CiTypes(code="CODE_TYPE_2", name="Name Two", is_standard="N", is_deliverable=False)
        _citype.save()
        models.CiRegExp(ci_type=_citype, loc_type=_loctype_n, regexp="^loc:path:2:ext$").save()
        _cs2_t = "1"*32

        with self.assertRaises(ValueError):
            # ci_type is not detected - location type absent
            _csc.register_file_md5(_cs2_t, None, "text/hypertrophed")

        with self.assertRaises(ValueError):
            # ci_type is not detected - location missing
            # "FILE" type is missing too
            _csc.register_file_md5(_cs2_t, None, "text/hypertrophed", None, "NXS")

        with self.assertRaises(ValueError):
            # ci_type is not detected - no regular expression
            _csc.register_file_md5(_cs2_t, None, "text/hypertrophed", "loc:path:3", "NXS")

        # add 'FILE' type to get rid of ValueError in further asserts
        models.CiTypes(code="FILE", name="A File", is_standard="N", is_deliverable=True).save()

        _fr_t2 = _csc.register_file_md5(_cs2_t, None, "text/hypertrophed", "loc:path:2:ext", "NXS")
        self.assertNotEqual(_fr_t2, _fr_t1)
        self.assertEqual(_csc.get_checksum_by_file(_fr_t2), _cs2_t)
        self.assertEqual(_fr_t2.ci_type.code, "CODE_TYPE_2")
        self.assertEqual(models.Files.objects.count(), 2)
        self.assertEqual(models.Locations.objects.count(), 2)
        self.assertEqual(models.CheckSums.objects.count(), 2)

        # new file with same checksum - no duplicates allowed, CI_TYPE has not to be overwritten
        _fr_t3 = _csc.register_file_md5(_cs2_t, "CODE_TYPE_1", "DataBomb", "loc:path:3", "NXS")
        self.assertEqual(_fr_t3, _fr_t2)
        self.assertEqual(_csc.get_checksum_by_file(_fr_t2), _cs2_t)
        self.assertEqual(_fr_t2.ci_type.code, "CODE_TYPE_2")
        self.assertEqual(models.Files.objects.count(), 2)
        self.assertEqual(models.Locations.objects.count(), 3)
        self.assertEqual(models.CheckSums.objects.count(), 2)

        # existent file with another checksum provider
        _fr_t4 = _csc.register_file_md5(_cs1_t, "CODE_TYPE_2", "DataBlumb", "loc:path:4", "NXS", cs_prov="Wrapped")
        self.assertEqual(_fr_t4, _fr_t1)
        self.assertEqual(_csc.get_checksum_by_file(_fr_t4, cs_prov="Wrapped"), _cs1_t)
        self.assertEqual(_fr_t4.ci_type.code, "CODE_TYPE_1")
        self.assertEqual(models.Files.objects.count(), 2)
        self.assertEqual(models.Locations.objects.count(), 4)
        self.assertEqual(models.CheckSums.objects.count(), 2)

    def test_register_file_md5__no_location(self):
        # register file file without location
        _csc = CheckSumsController()

        # citype, loctype, cstype
        _citype = models.CiTypes(code="CODE_TYPE_1", name="Name One", is_standard="N", is_deliverable=False)
        _citype.save()
        _loctype_n = models.LocTypes(code="NXS", name="Maven-compatible")
        _loctype_n.save()
        _cstype = models.CsTypes(code="MD5", name="MD5")
        _cstype.save()

        # make sure DB is empty
        self.assertEqual(models.Files.objects.count(), 0)
        self.assertEqual(models.Locations.objects.count(), 0)
        self.assertEqual(models.CheckSums.objects.count(), 0)

        _cs1_t = "0"*32
        _fr_t1 = _csc.register_file_md5(_cs1_t, "CODE_TYPE_1", "Data")
        self.assertEqual(_fr_t1.ci_type.code, "CODE_TYPE_1")
        self.assertEqual(_csc.get_checksum_by_file(_fr_t1), _cs1_t)
        self.assertEqual(models.Files.objects.count(), 1)
        self.assertEqual(models.Locations.objects.count(), 0)
        self.assertEqual(models.CheckSums.objects.count(), 1)

        # then add a location
        _fr_t1 = _csc.register_file_md5(_cs1_t, "CODE_TYPE_1", "Data", "loc:path:1.1:ext", "NXS")
        self.assertEqual(_fr_t1.ci_type.code, "CODE_TYPE_1")
        self.assertEqual(_csc.get_checksum_by_file(_fr_t1), _cs1_t)
        self.assertEqual(models.Files.objects.count(), 1)
        self.assertEqual(models.Locations.objects.count(), 1)
        self.assertEqual(models.CheckSums.objects.count(), 1)
        self.assertEqual(models.Locations.objects.last().path, "loc:path:1.1:ext")

    #### tests for 'register_includes' and 'register_file_obj' are united because they do call thmeselves recursively
    def test_register_includes__not_an_archive(self):
        _csc = CheckSumsController()

        # citype, loctype, cstype
        _citype = models.CiTypes(code="CODE_TYPE_1", name="Name One", is_standard="N", is_deliverable=False)
        _citype.save()
        _loctype_n = models.LocTypes(code="NXS", name="Maven-compatible")
        _loctype_n.save()
        _cstype = models.CsTypes(code="MD5", name="MD5")
        _cstype.save()

        # make sure DB is empty
        self.assertEqual(models.Files.objects.count(), 0)
        self.assertEqual(models.Locations.objects.count(), 0)
        self.assertEqual(models.CheckSums.objects.count(), 0)

        _f_o = tempfile.NamedTemporaryFile()
        _f_o.write(b"test_content")
        _f_o.flush()

        # no location, inc_level 0
        _f_r = _csc.register_file_obj(_f_o, "CODE_TYPE_1")
        self.assertEqual(models.Files.objects.count(), 1)
        self.assertEqual(models.Locations.objects.count(), 0)
        self.assertEqual(models.CheckSums.objects.count(), 1)
        self.assertEqual(_csc.get_current_inclusion_depth(_f_r), 0)

        # with location, inc_level 0
        _f_r = _csc.register_file_obj(_f_o, "CODE_TYPE_1", "the:location:path", "NXS")
        self.assertEqual(models.Files.objects.count(), 1)
        self.assertEqual(models.Locations.objects.count(), 1)
        self.assertEqual(models.CheckSums.objects.count(), 1)
        self.assertEqual(_csc.get_current_inclusion_depth(_f_r), 0)

        # no location, inc_level 1
        _f_r = _csc.register_file_obj(_f_o, "CODE_TYPE_1", inclusion_level=1)
        self.assertEqual(models.Files.objects.count(), 1)
        self.assertEqual(models.Locations.objects.count(), 1)
        self.assertEqual(models.CheckSums.objects.count(), 1)
        self.assertEqual(_csc.get_current_inclusion_depth(_f_r), 0)
        
        # with location, inc_level 1
        _f_r = _csc.register_file_obj(_f_o, "CODE_TYPE_1", "the:location:path", "NXS", inclusion_level=1)
        self.assertEqual(models.Files.objects.count(), 1)
        self.assertEqual(models.Locations.objects.count(), 1)
        self.assertEqual(models.CheckSums.objects.count(), 1)
        self.assertEqual(_csc.get_current_inclusion_depth(_f_r), 0)

        _f_o.close()
        

    def test_register_includes__archive_flat(self):
        # check all archive files registered
        _csc = CheckSumsController()

        # citype, loctype, cstype
        _citype = models.CiTypes(code="CODE_TYPE_1", name="Name One", is_standard="N", is_deliverable=False)
        _citype.save()
        _loctype_n = models.LocTypes(code="NXS", name="Maven-compatible")
        _loctype_n.save()
        _cstype = models.CsTypes(code="MD5", name="MD5")
        _cstype.save()

        # make sure DB is empty
        self.assertEqual(models.Files.objects.count(), 0)
        self.assertEqual(models.Locations.objects.count(), 0)
        self.assertEqual(models.CheckSums.objects.count(), 0)

        #_prepare an archive
        _a_c = tempfile.NamedTemporaryFile()
        _a_c.write(b"test file content")
        _a_c.flush()

        _arc_tgz_tmp = tempfile.NamedTemporaryFile()

        with tarfile.open(fileobj=_arc_tgz_tmp, mode="w:gz") as _tar_a:
            _tar_a.add(_a_c.name, recursive=False)
            _tar_a.close()

        _arc_tgz_tmp.flush()

        # no level given - should be zero
        _fl_r = _csc.register_file_obj(_arc_tgz_tmp, "CODE_TYPE_1")
        self.assertEqual(models.Files.objects.count(), 1)
        self.assertEqual(models.Locations.objects.count(), 0)
        self.assertEqual(models.CheckSums.objects.count(), 1)
        self.assertEqual(_fl_r, models.Files.objects.last())

        # No ci_type_sub given
        with self.assertRaises(ValueError):
            _csc._register_includes(_arc_tgz_tmp, None, None, 1, False, 0)

        # No file record for an archive: try to find out file by file object
        models.CiTypes(code="FILE", name="A file", is_standard="N", is_deliverable=False).save()
        models.LocTypes(code="ARCH", name="Inside archive").save()
        _il = _csc._register_includes(_arc_tgz_tmp, None, None, 1, False, 0)
        self.assertEqual(models.Files.objects.count(), 2)
        self.assertEqual(models.Locations.objects.count(), 1)
        self.assertEqual(models.CheckSums.objects.count(), 2)
        self.assertEqual(models.Files.objects.last().ci_type.code, "FILE")
        self.assertEqual(models.Locations.objects.last().loc_type.code, "ARCH")
        self.assertIsNotNone(models.Locations.objects.last().file_dst)
        self.assertEqual(models.Files.objects.last().depth_level, 0)
        self.assertEqual(models.Files.objects.first().depth_level, 0)
        self.assertEqual(_il, 1)

        _arc_tgz_tmp.close()
        _a_c.close()

    def test_register_includes__archive_in_archive(self):
        # all ok - includes-of-includes
        _csc = CheckSumsController()

        # citype, loctype, cstype
        _citype = models.CiTypes(code="CODE_TYPE_1", name="Name One", is_standard="N", is_deliverable=False)
        _citype.save()
        _loctype_n = models.LocTypes(code="NXS", name="Maven-compatible")
        _loctype_n.save()
        _cstype = models.CsTypes(code="MD5", name="MD5")
        _cstype.save()
        models.CiTypes(code="FILE", name="A file", is_standard="N", is_deliverable=False).save()
        models.LocTypes(code="ARCH", name="Inside archive").save()

        # make sure DB is empty
        self.assertEqual(models.Files.objects.count(), 0)
        self.assertEqual(models.Locations.objects.count(), 0)
        self.assertEqual(models.CheckSums.objects.count(), 0)

        #_prepare an archive
        _a_c = tempfile.NamedTemporaryFile()
        _a_c.write(b"test file content x")
        _a_c.flush()

        _arc_tgz_tmp = tempfile.NamedTemporaryFile()

        with tarfile.open(fileobj=_arc_tgz_tmp, mode="w:gz") as _tar_a:
            _tar_a.add(_a_c.name, recursive=False)
            _tar_a.close()

        _arc_tgz_tmp.flush()

        _arc_zip_tmp = tempfile.NamedTemporaryFile()
        _zip_a = zipfile.ZipFile(_arc_zip_tmp, mode='w')
        _zip_a.write(_arc_tgz_tmp.name)
        _zip_a.close()
        _arc_zip_tmp.flush()

        # register first archive
        _tgz_r = _csc.register_file_obj(_arc_tgz_tmp, "CODE_TYPE_1", "byx:poth:1.1.1:tgz", "NXS", inclusion_level=1)
        self.assertEqual(_tgz_r.depth_level, 1)
        self.assertEqual(_tgz_r.ci_type.code, "CODE_TYPE_1")
        self.assertEqual(models.Files.objects.count(), 2)
        self.assertEqual(models.Locations.objects.count(), 2)
        self.assertEqual(models.CheckSums.objects.count(), 2)
        self.assertEqual(models.Locations.objects.last().loc_type.code, "ARCH")
        self.assertEqual(models.Locations.objects.last().file_dst, _tgz_r)
        _fr_inc = models.Files.objects.last()
        self.assertEqual(_fr_inc.depth_level, 0)
        self.assertEqual(_fr_inc.ci_type.code, "FILE")

        # register second once again
        _zip_r = _csc.register_file_obj(_arc_zip_tmp, "CODE_TYPE_1", "byx:poth:1.1.1:zip", "NXS", inclusion_level=2)
        self.assertEqual(_zip_r.depth_level, 1)
        self.assertEqual(_zip_r.ci_type.code, "CODE_TYPE_1")
        self.assertEqual(models.Files.objects.count(), 3)
        self.assertEqual(models.Locations.objects.count(), 4)
        self.assertEqual(models.CheckSums.objects.count(), 3)
        self.assertEqual(models.Locations.objects.last().loc_type.code, "ARCH")
        self.assertEqual(models.Locations.objects.last().file_dst, _zip_r)
        self.assertEqual(models.Locations.objects.last().file, _tgz_r)
        _tgz_r.refresh_from_db()
        self.assertEqual(_tgz_r.depth_level, 1)
        _fr_inc.refresh_from_db()
        self.assertEqual(_fr_inc.depth_level, 0)

        _a_c.close()
        _arc_tgz_tmp.close()
        _arc_zip_tmp.close()

    def test_register_includes__sql(self):
        # prepare one PL/SQL file
        _sql_c = b"create or replace procedure testproc(testarg in varchar2(100 char)) as t varchar2(100 char); begin t:=testarg.substr(1,0); end;"
        _wrp_c = b"create or replace procedure testproc(testarg in varchar2(100 char)) wrapped abcdef abcdef abcdef"

        # citype, loctype, cstype
        _citype = models.CiTypes(code="CODE_TYPE_1", name="Name One", is_standard="N", is_deliverable=False)
        _citype.save()
        _loctype_n = models.LocTypes(code="NXS", name="Maven-compatible")
        _loctype_n.save()
        _cstype = models.CsTypes(code="MD5", name="MD5")
        _cstype.save()

        # make sure DB is empty
        self.assertEqual(models.Files.objects.count(), 0)
        self.assertEqual(models.Locations.objects.count(), 0)
        self.assertEqual(models.CheckSums.objects.count(), 0)

        # prepare file
        _sql_f = tempfile.NamedTemporaryFile(suffix=".sql")
        _sql_f.write(_sql_c)
        _sql_f.flush()

        # mock wrapper since we do not have original one
        class MockWrapper(unittest.mock.MagicMock):
            def wrap_buf(self, fl_in, write_to):
                assert(write_to is not None)
                write_to.write(_wrp_c)

            def unwrap_buf(self, fl_in, write_to):
                assert(write_to is not None)
                write_to.write(_sql_c)

        with unittest.mock.patch("oc_delivery_apps.checksums.controllers.wrapper.PLSQLWrapper", return_value=MockWrapper()) as _x:
            _csc = CheckSumsController()
            _csc.register_file_obj(_sql_f, "CODE_TYPE_1", "pl.sql.procedure:testproc:1.1.1:sql", "NXS")
            _x.assert_called()

        # check database checksums
        self.assertEqual(models.Locations.objects.count(), 1)
        self.assertEqual(models.Locations.objects.last().path, "pl.sql.procedure:testproc:1.1.1:sql")
        self.assertEqual(models.Files.objects.count(), 1)
        _fl_r = models.Files.objects.last()
        self.assertEqual(_fl_r.ci_type.code, "CODE_TYPE_1")
        # should be 4 checksums: "Regular", "Wrapped", "Normed", "WrappedNormed" and 8 csProvs
        # limitation is due to the same content for "Regular" and "Unwrapped" steps, see "mock" above
        self.assertEqual(models.CsProv.objects.count(), 8)
        self.assertEqual(models.CheckSums.objects.filter(file=_fl_r).count(), 4)

        _sql_f.close()

    def test_register_includes__sql_no_ext(self):
        # prepare one PL/SQL file
        _sql_c = b"create or replace procedure testproc(testarg in varchar2(100 char)) as t varchar2(100 char); begin t:=testarg.substr(1,0); end;"
        _wrp_c = b"create or replace procedure testproc(testarg in varchar2(100 char)) wrapped abcdef abcdef abcdef"

        # citype, loctype, cstype
        _citype = models.CiTypes(code="CODE_TYPE_1", name="Name One", is_standard="N", is_deliverable=False)
        _citype.save()
        _loctype_n = models.LocTypes(code="NXS", name="Maven-compatible")
        _loctype_n.save()
        _cstype = models.CsTypes(code="MD5", name="MD5")
        _cstype.save()

        # make sure DB is empty
        self.assertEqual(models.Files.objects.count(), 0)
        self.assertEqual(models.Locations.objects.count(), 0)
        self.assertEqual(models.CheckSums.objects.count(), 0)

        # prepare file
        _sql_f = tempfile.NamedTemporaryFile(suffix=".trt")
        _sql_f.write(_sql_c)
        _sql_f.flush()

        # mock wrapper since we do not have original one
        class MockWrapper(unittest.mock.MagicMock):
            def wrap_buf(self, fl_in, write_to):
                assert(write_to is not None)
                write_to.write(_wrp_c)

            def unwrap_buf(self, fl_in, write_to):
                assert(write_to is not None)
                write_to.write(_sql_c)

        with unittest.mock.patch("oc_delivery_apps.checksums.controllers.wrapper.PLSQLWrapper", return_value=MockWrapper()) as _x:
            _csc = CheckSumsController()
            _csc.register_file_obj(_sql_f, "CODE_TYPE_1", "pl.sql.procedure:testproc:1.1.1", "NXS")
            _x.assert_not_called()

        # check database checksums
        self.assertEqual(models.Locations.objects.count(), 1)
        self.assertEqual(models.Locations.objects.last().path, "pl.sql.procedure:testproc:1.1.1")
        self.assertEqual(models.Files.objects.count(), 1)
        _fl_r = models.Files.objects.last()
        self.assertEqual(_fl_r.ci_type.code, "CODE_TYPE_1")
        # should be 1 checksum
        self.assertEqual(models.CsProv.objects.count(), 1)
        self.assertEqual(models.CheckSums.objects.filter(file=_fl_r).count(), 1)

        _sql_f.close()

    def test_get_file_by_file_obj(self):
        _csc = CheckSumsController()

        #empty
        self.assertIsNone(_csc.get_file_by_file_obj(None))

        # prepare one PL/SQL file
        _sql_c = b"create or replace procedure testproc(testarg in varchar2(100 char)) as t varchar2(100 char); begin t:=testarg.substr(1,0); end;"
        _wrp_c = b"create or replace procedure testproc(testarg in varchar2(100 char)) wrapped abcdef abcdef abcdef"

        # citype, loctype, cstype
        _citype = models.CiTypes(code="CODE_TYPE_1", name="Name One", is_standard="N", is_deliverable=False)
        _citype.save()
        _loctype_n = models.LocTypes(code="NXS", name="Maven-compatible")
        _loctype_n.save()
        _cstype = models.CsTypes(code="MD5", name="MD5")
        _cstype.save()

        # make sure DB is empty
        self.assertEqual(models.Files.objects.count(), 0)
        self.assertEqual(models.Locations.objects.count(), 0)
        self.assertEqual(models.CheckSums.objects.count(), 0)

        #flat
        _tf = tempfile.NamedTemporaryFile()
        _tf.write(b"the test content")
        _csc.register_file_obj(_tf, "CODE_TYPE_1")
        self.assertEqual(models.Files.objects.count(), 1)
        _f = models.Files.objects.last()
        self.assertEqual(_f, _csc.get_file_by_file_obj(_tf))
        _tf.close()

        #sql
        _sql_f = tempfile.NamedTemporaryFile(suffix=".sql")
        _sql_f.write(_sql_c)
        _sql_f.flush()

        # mock wrapper
        class MockWrapper(unittest.mock.MagicMock):
            def wrap_buf(self, fl_in, write_to):
                assert(write_to is not None)
                write_to.write(_wrp_c)

            def unwrap_buf(self, fl_in, write_to):
                assert(write_to is not None)
                write_to.write(_sql_c)

        with unittest.mock.patch("oc_delivery_apps.checksums.controllers.wrapper.PLSQLWrapper", return_value=MockWrapper()) as _x:
            _csc = CheckSumsController()
            _csc.register_file_obj(_sql_f, "CODE_TYPE_1", "pl.sql.procedure:testproc:1.1.1:sql", "NXS")
            _x.assert_called()

        self.assertEqual(models.Files.objects.count(), 2)
        _f = models.Files.objects.last()
        self.assertEqual(_f, _csc.get_file_by_file_obj(_sql_f))
        _sql_f.close()

    def test_add_inclusion_file_obj(self):
        # register two files and see inclusion written
        # citype, loctype, cstype
        _citype = models.CiTypes(code="CODE_TYPE_1", name="Name One", is_standard="N", is_deliverable=False)
        _citype.save()
        _loctype_n = models.LocTypes(code="ARCH", name="Inside archive")
        _loctype_n.save()
        _cstype = models.CsTypes(code="MD5", name="MD5")
        _cstype.save()

        # make sure DB is empty
        self.assertEqual(models.Files.objects.count(), 0)
        self.assertEqual(models.Locations.objects.count(), 0)
        self.assertEqual(models.CheckSums.objects.count(), 0)

        _tf_a = tempfile.NamedTemporaryFile()
        _tf_a.write(b"Test archive content")
        _tf_i = tempfile.NamedTemporaryFile()
        _tf_i.write(b"Test included file content")

        _csc = CheckSumsController()

        _fr_a = _csc.register_file_obj(_tf_a, "CODE_TYPE_1")
        _fr_i = _csc.register_file_obj(_tf_i, "CODE_TYPE_1")

        _csc.add_inclusion_file_obj(_tf_i, _tf_a, "the/path.txt")
        self.assertEqual(models.Files.objects.count(), 2)
        self.assertEqual(models.Locations.objects.count(), 1)
        self.assertEqual(models.CheckSums.objects.count(), 2)
        _l = models.Locations.objects.last()
        self.assertEqual(_l.loc_type.code, "ARCH")
        self.assertEqual(_l.path, "the/path.txt")
        self.assertEqual(_l.file, _fr_i)
        self.assertEqual(_l.file_dst, _fr_a)

        _tf_a.close()
        _tf_i.close()

    def test_norm_flags_by_suffixes(self):
        _csc = CheckSumsController()
        self.assertEqual(len(_csc._norm_flags_by_suffixes("")), 0)
        self.assertEqual(_csc._norm_flags_by_suffixes("U").pop(), PLSQLNormalizationFlags.uppercase)
        _x = _csc._norm_flags_by_suffixes("UCS")
        
        for _flag in [PLSQLNormalizationFlags.uppercase, PLSQLNormalizationFlags.no_spaces, PLSQLNormalizationFlags.no_comments]:
            self.assertIn(_flag, _x)

    def test_sql_norm(self):
        _csc = CheckSumsController()
        _src = tempfile.NamedTemporaryFile()
        _src.write(b"create or replace procedure testproc(testarg in varchar2(100 char)) as t varchar2(100 char); begin t:=testarg.substr(1,0); end;")

        _r = _csc._sql_norm(_src, "Normed")
        self.assertEqual(1, len(list(_r.keys())))
        self.assertIn("Normed", list(_r.keys()))
        self.assertEqual(_r.get("Normed").read(), b"CREATE OR REPLACE PROCEDURE TESTPROC(TESTARG IN VARCHAR2(100 CHAR)) AS t varchar2(100 char); begin t:=testarg.substr(1,0); end;\n\n/")

    def test_sql_wrap_unwrap(self):
        _wrp_c = b"wrapped example"
        _sql_c = b"notwrapped_example"
        # mock wrapper
        class MockWrapper(unittest.mock.MagicMock):
            def wrap_buf(self, fl_in, write_to):
                assert(write_to is not None)
                write_to.write(_wrp_c)

            def unwrap_buf(self, fl_in, write_to):
                assert(write_to is not None)
                write_to.write(_sql_c)

        with unittest.mock.patch("oc_delivery_apps.checksums.controllers.wrapper.PLSQLWrapper", return_value=MockWrapper()) as _x:
            _csc = CheckSumsController()
            _r = _csc._sql_wrap(tempfile.NamedTemporaryFile(), "Wrapped")
            self.assertEqual(len(list(_r.keys())), 1)
            _t = _r.get("Wrapped")
            _t.seek(0, os.SEEK_SET)
            self.assertEqual(_t.read(), _wrp_c)
            _t.close()
            _r = _csc._sql_unwrap(tempfile.NamedTemporaryFile(), "Unwrapped")
            self.assertEqual(len(list(_r.keys())), 1)
            _t = _r.get("Unwrapped")
            _t.seek(0, os.SEEK_SET)
            self.assertEqual(_t.read(), _sql_c)
            _t.close()

    def test_is_wrapped(self):
        _csc = CheckSumsController()
        _sql_c = b"create or replace procedure testproc(testarg in varchar2(100 char)) as t varchar2(100 char); begin t:=testarg.substr(1,0); end;"
        _wrp_c = b"create or replace procedure testproc(testarg in varchar2(100 char)) wrapped abcdef abcdef abcdef"

        _tft = tempfile.NamedTemporaryFile()
        _tfo = tempfile.NamedTemporaryFile()
        _tft.write(_sql_c)
        _tft.flush()
        _tfo.write(_wrp_c)
        _tfo.flush()
        self.assertFalse(_csc._is_wrapped(_tft))
        self.assertTrue(_csc._is_wrapped(_tfo))
        _tft.close()
        _tfo.close()

    def test_perform_step(self):
        # a classic unit-test with mocks
        _csc = CheckSumsController()
        _tf = tempfile.NamedTemporaryFile()

        # 1. no such step
        with self.assertRaises(ValueError):
            _csc._perform_step(_tf, "NonExistentStep")

        # 2. empty function
        _tf = tempfile.NamedTemporaryFile()
        self.assertEqual(dict(), _csc._perform_step(_tf, "FullNormed", is_first=False))

        # 3. function returns nothing
        _csc._sql_norm = unittest.mock.MagicMock(return_value=dict())
        self.assertEqual(_csc._sql_norm(_tf, "AnyStep"), dict())
        self.assertEqual(dict(), _csc._perform_step(_tf, "Normed"))

        # 4. Go recursively with all steps
        def _step(f_o, step): return {step: f_o}

        _csc._sql_norm = unittest.mock.MagicMock(side_effect=_step)
        _csc._sql_wrap = unittest.mock.MagicMock(side_effect=_step)
        _csc._sql_unwrap = unittest.mock.MagicMock(side_effect=_step)
        _csc._is_wrapped = unittest.mock.MagicMock(return_value=True)

        _expected = {
                'Regular': _tf,
                'Normed': _tf,
                'Normed_Wrapped': _tf,
                'Normed_Wrapped_Normed': _tf,
                'Unwrapped': _tf,
                'Unwrapped_Normed': _tf,
                'Wrapped': _tf,
                'Wrapped_Normed': _tf}

        # assert the result
        self.assertEqual(_expected, _csc._perform_step(_tf, "Regular"))
        # assert calls for mocks
        self.assertEqual(_csc._sql_norm.call_count, 4)
        _csc._sql_norm.assert_any_call(_tf, "Normed")
        _csc._sql_norm.assert_any_call(_tf, "Normed_Wrapped_Normed")
        _csc._sql_norm.assert_any_call(_tf, "Wrapped_Normed")
        _csc._sql_norm.assert_any_call(_tf, "Unwrapped_Normed")
        self.assertEqual(_csc._sql_wrap.call_count, 2)
        _csc._sql_wrap.assert_any_call(_tf, "Wrapped")
        _csc._sql_wrap.assert_any_call(_tf, "Normed_Wrapped")
        _csc._sql_unwrap.assert_called_once_with(_tf, "Unwrapped")

        _tf.close()

    def test_get_all_sql_checksums(self):
        _csc = CheckSumsController()
        _tf = tempfile.NamedTemporaryFile()
        _csc._is_wrapped = unittest.mock.MagicMock(return_value=False)
        _csc._perform_step = unittest.mock.MagicMock(return_value={"Regular": _tf})
        _res = _csc.get_all_sql_checksums(_tf)
        _csc._is_wrapped.assert_called_once_with(_tf)
        _csc._perform_step.assert_called_once_with(_tf, "Regular")
        self.assertEqual("Regular", list(_res.keys()).pop())
        self.assertEqual(list(_res.get("Regular").keys()).pop(), "MD5")
        _tf.close()

    def test_delete_location_cascade(self):
        # name is a bit confused due to historical reason
        # actually location is deleted without historical records
        # also tests 'is_location_deleted'
        
        # citype, loctype, cstype
        _citype = models.CiTypes(code="CODE_TYPE_1", name="Name One", is_standard="N", is_deliverable=False)
        _citype.save()
        _loctype_n = models.LocTypes(code="NXS", name="Maven-compatible")
        _loctype_n.save()
        _cstype = models.CsTypes(code="MD5", name="MD5")
        _cstype.save()

        # make sure DB is empty
        self.assertEqual(models.Files.objects.count(), 0)
        self.assertEqual(models.Locations.objects.count(), 0)
        self.assertEqual(models.CheckSums.objects.count(), 0)
        self.assertEqual(models.Locations.history.count(), 0)

        _tf = tempfile.NamedTemporaryFile()
        _csc = CheckSumsController()
        self.assertTrue(_csc.is_location_deleted("the.path.to:artifact:1.1.1", "NXS"))
        _csc.register_file_obj(_tf, "CODE_TYPE_1", "the.path.to:artifact:1.1.1", "NXS")
        self.assertEqual(models.Files.objects.count(), 1)
        self.assertEqual(models.Locations.objects.count(), 1)
        self.assertEqual(models.CheckSums.objects.count(), 1)
        self.assertEqual(models.Locations.history.count(), 1)
        self.assertFalse(_csc.is_location_deleted("the.path.to:artifact:1.1.1", "NXS"))
        _loc = models.Locations.objects.last()
        self.assertEqual(_loc.loc_type.code, "NXS")
        self.assertEqual(_loc.path, "the.path.to:artifact:1.1.1")
        _csc.delete_location_cascade(_loc, reason="No more needed")
        self.assertEqual(models.Files.objects.count(), 1)
        self.assertEqual(models.Locations.objects.count(), 0)
        self.assertEqual(models.CheckSums.objects.count(), 1)
        self.assertEqual(models.Locations.history.count(), 2)
        self.assertEqual(models.Locations.history.filter(
                path="the.path.to:artifact:1.1.1", 
                loc_type__code="NXS",
                history_change_reason="No more needed").count(), 1)
        self.assertTrue(_csc.is_location_deleted("the.path.to:artifact:1.1.1", "NXS"))
        _tf.close()

    def test_delete_location(self):
        # citype, loctype, cstype
        _citype = models.CiTypes(code="CODE_TYPE_1", name="Name One", is_standard="N", is_deliverable=False)
        _citype.save()
        _loctype_n = models.LocTypes(code="SVN", name="SubVersion")
        _loctype_n.save()
        _cstype = models.CsTypes(code="MD5", name="MD5")
        _cstype.save()

        # make sure DB is empty
        self.assertEqual(models.Files.objects.count(), 0)
        self.assertEqual(models.Locations.objects.count(), 0)
        self.assertEqual(models.CheckSums.objects.count(), 0)
        self.assertEqual(models.Locations.history.count(), 0)

        _tf = tempfile.NamedTemporaryFile()
        _csc = CheckSumsController()
        _svn_t = "https://svn.example.com/svn/svn-tst.txt"
        self.assertTrue(_csc.is_location_deleted(_svn_t, "SVN", revision=0))
        _csc.register_file_obj(_tf, "CODE_TYPE_1", _svn_t, "SVN", loc_revision=0)
        _reason = "Deletion test reason"

        # 0 no path
        with self.assertRaises(ValueError):
            _csc.delete_location(" ", "SVN", revision=0, reason=_reason)

        # 1 no loc_type
        with self.assertRaises(ValueError):
            _csc.delete_location(_svn_t, " ", revision=0, reason=_reason)

        # 2 svn without revision
        with self.assertRaises(ValueError):
            _csc.delete_location(_svn_t, "SVN", revision=None, reason=_reason)

        # 3 two same locations for different files - unable to do due to database index
        self.assertFalse(_csc.is_location_deleted(_svn_t, "SVN", revision=0))
        _csc.delete_location(_svn_t, "SVN", revision=0, reason=_reason)
        self.assertEqual(models.Files.objects.count(), 1)
        self.assertEqual(models.Locations.objects.count(), 0)
        self.assertEqual(models.CheckSums.objects.count(), 1)
        self.assertEqual(models.Locations.history.count(), 2)
        # no need to check history exactly - done in 'test_delete_location_cascade'
        self.assertTrue(_csc.is_location_deleted(_svn_t, "SVN", revision=0))

    def test_add_ci_type_inclusion(self):
        self.assertEqual(models.CiTypes.objects.count(), 0)
        self.assertEqual(models.CiTypeGroups.objects.count(), 0)
        self.assertEqual(models.CiTypeIncs.objects.count(), 0)
        models.CiTypes(code="CODE", name="Name").save()
        models.CiTypeGroups(code="CODE", name="Name").save()
        _csc = CheckSumsController()

        self.assertEqual(0, _csc.add_ci_type_inclusion("", "CODE"))
        self.assertEqual(0, _csc.add_ci_type_inclusion("CODE", ""))
        self.assertEqual(1, _csc.add_ci_type_inclusion("CODE", "CODE"))
        self.assertEqual(1, _csc.add_ci_type_inclusion("CODE", "CODE")) # check no duplicates
        self.assertEqual(models.CiTypes.objects.count(), 1)
        self.assertEqual(models.CiTypeGroups.objects.count(), 1)
        self.assertEqual(models.CiTypeIncs.objects.count(), 1)
        _inc = models.CiTypeIncs.objects.last()
        self.assertEqual(_inc.ci_type_group.code, "CODE")
        self.assertEqual(_inc.ci_type.code, "CODE")

    def test_get_doc_gav(self):
        # add some group RNs and see GAVs
        self.assertEqual(models.CiTypes.objects.count(), 0)
        self.assertEqual(models.CiTypeGroups.objects.count(), 0)
        self.assertEqual(models.CiTypeIncs.objects.count(), 0)
        models.CiTypes(code="CODE_1", name="Name One").save()
        _csc = CheckSumsController()
        self.assertIsNone(_csc.get_doc_gav("CODE_1", "1.1.1"))

        with self.assertRaises(ValueError):
            _csc.get_doc_gav("CODE_1", "")

        with self.assertRaises(ValueError):
            _csc.get_doc_gav("", "1.1.1")

        with self.assertRaises(models.CiTypes.DoesNotExist):
            _csc.get_doc_gav("NONEXISTENT", "1.1.1")

        for _idx in range(0, 4):
            models.CiTypeGroups(code="CODE%d" % _idx, name="Name %d" % _idx, doc_artifactid="a%d" % _idx).save()
            _csc.add_ci_type_inclusion("CODE%d" % _idx, "CODE_1")

        _r = _csc.get_doc_gav("CODE_1", "1.1.1")
        self.assertTrue(_r.startswith("com.example.doc.sfx.documentation:a"))
        self.assertTrue(_r.endswith(":1.1.1"))

        # now test if we have CiType.doc_artifactid
        _t = models.CiTypes.objects.get(code="CODE_1")
        _t.doc_artifactid = 'b'
        _t.save()
        _r = _csc.get_doc_gav("CODE_1", "2.2.2")
        self.assertTrue(_r.startswith("com.example.doc.sfx.documentation:b:"))
        self.assertTrue(_r.endswith(":2.2.2"))

    def test_get_rn_gav(self):
        # add some group RNs and see GAVs
        self.assertEqual(models.CiTypes.objects.count(), 0)
        self.assertEqual(models.CiTypeGroups.objects.count(), 0)
        self.assertEqual(models.CiTypeIncs.objects.count(), 0)
        models.CiTypes(code="CODE_1", name="Name One").save()
        _csc = CheckSumsController()
        self.assertIsNone(_csc.get_rn_gav("CODE_1", "1.1.1"))

        with self.assertRaises(ValueError):
            _csc.get_rn_gav("CODE_1", "")

        with self.assertRaises(ValueError):
            _csc.get_rn_gav("", "1.1.1")

        with self.assertRaises(models.CiTypes.DoesNotExist):
            _csc.get_rn_gav("NONEXISTENT", "1.1.1")

        for _idx in range(0, 4):
            models.CiTypeGroups(code="CODE%d" % _idx, name="Name %d" % _idx, rn_artifactid="a%d" % _idx).save()
            _csc.add_ci_type_inclusion("CODE%d" % _idx, "CODE_1")

        _r = _csc.get_rn_gav("CODE_1", "1.1.1")
        self.assertTrue(_r.startswith("com.example.rn.sfx.release_notes:a"))
        self.assertTrue(_r.endswith(":1.1.1:txt"))

        # now test if we have CiType.rn_artifactid
        _t = models.CiTypes.objects.get(code="CODE_1")
        _t.rn_artifactid = 'b'
        _t.save()
        _r = _csc.get_rn_gav("CODE_1", "2.2.2")
        self.assertTrue(_r.startswith("com.example.rn.sfx.release_notes:b:"))
        self.assertTrue(_r.endswith(":2.2.2:txt"))

    def __assert_lists_equal(self, list_a, list_b):
        # 'assertListsEqual' is available in Python 3.9 or later, but we are forced to support Python 3.6
        self.assertEqual(type(list_a), type(list_b))
        self.assertEqual(len(list_a), len(list_b))

        for _t in list_a:
            self.assertIn(_t, list_b)

        for _t in list_b:
            self.assertIn(_t, list_a)

    def test_get_ci_group_regexp(self):
        # add group and some types with regexps for all
        self.assertEqual(models.CiTypes.objects.count(), 0)
        self.assertEqual(models.CiTypeGroups.objects.count(), 0)
        self.assertEqual(models.CiTypeIncs.objects.count(), 0)
        _lt_nxs = models.LocTypes(code="NXS", name="Maven compatible")
        _lt_nxs.save()
        _lt_svn = models.LocTypes(code="SVN", name="SubVersion")
        _lt_svn.save()
        _csc = CheckSumsController()

        for _ig in range(0, 3):
            _g_code = "GROUP%d" % _ig
            models.CiTypeGroups(code=_g_code, name="Group %d" % _ig).save()
            self.assertFalse(bool(_csc.get_ci_group_regexp(_g_code)))
            _expected_regexps_nxs = list()
            _expected_regexps_svn = list()

            for _it in range(0, 3):
                _t_code = "GROUP%dTYPE%d" % (_ig, _it)
                _type = models.CiTypes(code=_t_code, name="Group %d Type %d" % (_ig, _it))
                _type.save()
                self.__assert_lists_equal(_expected_regexps_nxs + _expected_regexps_svn, 
                        _csc.get_ci_group_regexp(_g_code))
                self.__assert_lists_equal(_expected_regexps_nxs, _csc.get_ci_group_regexp(_g_code, "NXS"))
                self.__assert_lists_equal(_expected_regexps_svn, _csc.get_ci_group_regexp(_g_code, "SVN"))

                for _ir in range(0, 3):
                    _rsvn = "g%dt%dr%dsvn" % (_ig, _it, _ir)
                    _rnxs = "g%dt%dr%dnxs" % (_ig, _it, _ir)
                    models.CiRegExp(ci_type=_type, loc_type=_lt_nxs, regexp=_rnxs).save()
                    models.CiRegExp(ci_type=_type, loc_type=_lt_svn, regexp=_rsvn).save()

                    # now add the type to the group
                    _csc.add_ci_type_inclusion(_g_code, _t_code) 
                    _expected_regexps_nxs.append(_rnxs)
                    _expected_regexps_svn.append(_rsvn)
                    self.__assert_lists_equal(_expected_regexps_nxs + _expected_regexps_svn, 
                            _csc.get_ci_group_regexp(_g_code))
                    self.__assert_lists_equal(_expected_regexps_nxs, _csc.get_ci_group_regexp(_g_code, "NXS"))
                    self.__assert_lists_equal(_expected_regexps_svn, _csc.get_ci_group_regexp(_g_code, "SVN"))

    def test_get_ci_type_dms_id(self):
        # add group and some types with regexps for all
        self.assertEqual(models.CiTypes.objects.count(), 0)
        self.assertEqual(models.CiTypeDms.objects.count(), 0)
        _t = models.CiTypes(code="C1", name="Type 1")
        _t.save()
        models.CiTypeDms(ci_type=_t, dms_id="dmsid1").save()
        models.CiTypeDms(ci_type=_t, dms_id="dmsid2").save()
        _csc = CheckSumsController()

        # no type
        with self.assertRaises(ValueError):
            _csc.get_ci_type_dms_id("")

        # ok
        self.assertEqual("dmsid2", _csc.get_ci_type_dms_id("C1"))
        self.assertIsNone(_csc.get_ci_type_dms_id("C2"))

    def test_add_ci_type_dms_id(self):
        # add group and some types with regexps for all
        self.assertEqual(models.CiTypes.objects.count(), 0)
        self.assertEqual(models.CiTypeDms.objects.count(), 0)
        models.CiTypes(code="C1", name="Type 1").save()
        _csc = CheckSumsController()
        _csc.add_ci_type_dms_id("C1", "dmsid1")
        _csc.add_ci_type_dms_id("C1", "dmsid1") # to check for duplicates
        _csc.add_ci_type_dms_id("C1", "dmsid2")
        _csc.add_ci_type_dms_id("C1", "dmsid2") # to check for duplicates

        # test exceptions
        with self.assertRaises(ValueError):
            _csc.add_ci_type_dms_id("", "dmsid3")

        with self.assertRaises(ValueError):
            _csc.add_ci_type_dms_id("C2", "dmsid3")

        with self.assertRaises(ValueError):
            _csc.add_ci_type_dms_id("C1", None)

        # ok
        self.assertEqual("dmsid2", _csc.get_ci_type_dms_id("C1"))
        self.assertEqual(models.CiTypeDms.objects.filter(ci_type__code="C1").count(), 1)

    def test_get_current_inclusion_depth__none(self):
        self.assertEqual(models.Locations.objects.count(), 0)
        # none - should return None
        _csc = CheckSumsController()
        
        self.assertIsNone(_csc.get_current_inclusion_depth_calc(None))
        self.assertIsNone(_csc._get_current_inclusion_depth_calc(None, 0))


    def __adjust_file_depth(self, f_r, level):
        if level < 0:
            return

        f_r.refresh_from_db()

        for _inc in models.Locations.objects.filter(file_dst=f_r).all():
            self.__adjust_file_depth(_inc.file, level-1)

        f_r.depth_level = level
        f_r.save()

    def test_get_current_inclusion_depth__actual(self):
        # actual is more than one specified
        self.assertEqual(models.Files.objects.count(), 0)
        self.assertEqual(models.Locations.objects.count(), 0)
        self.assertEqual(models.CiTypes.objects.count(), 0)
        self.assertEqual(models.CheckSums.objects.count(), 0)

        # register ci_type, loc_types, cs_type
        _type = models.CiTypes(code="C1", name="T1")
        _type.save()
        _loctype_n = models.LocTypes(code="NXS", name="Maven-compatible")
        _loctype_n.save()
        _loctype_a = models.LocTypes(code="ARCH", name="Inside archive")
        _loctype_a.save()
        _cst = models.CsTypes(code="MD5", name="MD5")
        _cst.save()

        # now add some files and inclusions
        _cs_f0 = "0"*32
        _cs_f1 = "1"*32
        _cs_f2 = "2"*32
        _cs_f3 = "3"*32

        _csc = CheckSumsController()
        _csc.register_file_md5(_cs_f0, "C1", "Data", "nxs.group.id:art:0.0.0.0:pkg", "NXS")
        _f1 = models.Files.objects.last()
        _csc.register_file_md5(_cs_f1, "C1", "Data")
        _csc.register_file_md5(_cs_f2, "C1", "Data")
        _csc.register_file_md5(_cs_f3, "C1", "Data")
        _csc.add_inclusion_checksums(_cs_f1, _cs_f0, "pf1")
        _csc.add_inclusion_checksums(_cs_f2, _cs_f1, "pf2")
        _csc.add_inclusion_checksums(_cs_f3, _cs_f2, "pf3")

        self.__adjust_file_depth(_f1, 0)
        self.assertEqual(_csc.get_current_inclusion_depth_calc(_f1), 3)
        
    def test_get_current_inclusion_depth__inactual(self):
        self.assertEqual(models.Files.objects.count(), 0)
        self.assertEqual(models.Locations.objects.count(), 0)
        self.assertEqual(models.CiTypes.objects.count(), 0)
        self.assertEqual(models.CheckSums.objects.count(), 0)

        # register ci_type, loc_types, cs_type
        _type = models.CiTypes(code="C1", name="T1")
        _type.save()
        _loctype_n = models.LocTypes(code="NXS", name="Maven-compatible")
        _loctype_n.save()
        _loctype_a = models.LocTypes(code="ARCH", name="Inside archive")
        _loctype_a.save()
        _cst = models.CsTypes(code="MD5", name="MD5")
        _cst.save()

        # now add some files and inclusions
        _cs_f0 = "0"*32
        _cs_f1 = "1"*32
        _cs_f2 = "2"*32
        _cs_f3 = "3"*32

        _csc = CheckSumsController()
        _csc.register_file_md5(_cs_f0, "C1", "Data", "nxs.group.id:art:0.0.0.0:pkg", "NXS")
        _f1 = models.Files.objects.last()
        _csc.register_file_md5(_cs_f1, "C1", "Data")
        _csc.register_file_md5(_cs_f2, "C1", "Data")
        _csc.register_file_md5(_cs_f3, "C1", "Data")
        _csc.add_inclusion_checksums(_cs_f1, _cs_f0, "pf1")
        _csc.add_inclusion_checksums(_cs_f2, _cs_f1, "pf2")
        _csc.add_inclusion_checksums(_cs_f3, _cs_f2, "pf3")

        self.assertEqual(_csc.get_current_inclusion_depth_calc(_f1), 3)

        _f1.refresh_from_db()
        _f1.depth_level = 4
        _f1.save()

        # this should not confuse us
        self.assertEqual(_csc.get_current_inclusion_depth_calc(_f1), 3)

    def test_ci_type_record(self):
        # no types in database - should raise ValueError
        _csc = CheckSumsController()

        with self.assertRaises(ValueError):
            _csc._ci_type_record('TYPE', 'path', 'loc')

        # store one type and make sure ValueError is raised
        _ci_type = models.CiTypes(code="T1", name="T1")
        _ci_type.save()

        with self.assertRaises(ValueError):
            _csc._ci_type_record('TYPE', 'path', 'loc')

        with self.assertRaises(ValueError):
            _csc._ci_type_record('TYPE', 'path', 'loc')

        with self.assertRaises(ValueError):
            _csc._ci_type_record('TYPE', None, 'loc')

        with self.assertRaises(ValueError):
            _csc._ci_type_record('TYPE', 'path', None)

        with self.assertRaises(ValueError):
            _csc._ci_type_record('TYPE', None, None)

        with self.assertRaises(ValueError):
            _csc._ci_type_record(None, None, None)

        # legal record
        self.assertEqual(_ci_type.code, _csc._ci_type_record('T1', 'path', 'loc').code)
        self.assertEqual(_ci_type.code, _csc._ci_type_record('T1', 'path', None).code)
        self.assertEqual(_ci_type.code, _csc._ci_type_record('T1', None, None).code)
        self.assertEqual(_ci_type.code, _csc._ci_type_record('T1', None, 'loc').code)

        # give a 'FILE' type - assert it returned where possible
        models.CiTypes(code='FILE', name='File').save()
        self.assertEqual(_ci_type.code, _csc._ci_type_record('T1', 'path', 'loc').code)
        self.assertEqual(_ci_type.code, _csc._ci_type_record('T1', 'path', None).code)
        self.assertEqual(_ci_type.code, _csc._ci_type_record('T1', None, None).code)
        self.assertEqual(_ci_type.code, _csc._ci_type_record('T1', None, 'loc').code)
        self.assertEqual('FILE', _csc._ci_type_record('T_NONEXIST', 'path', 'loc').code)

        with self.assertRaises(ValueError):
            _csc._ci_type_record('T_NONEXIST', 'path', None)

        with self.assertRaises(ValueError):
            _csc._ci_type_record('T_NONEXIST', None, None)

        with self.assertRaises(ValueError):
            _csc._ci_type_record('T_NONEXIST', None, 'loc')

        # add a regular expression
        _loc = models.LocTypes(code="LOC", name="Location")
        _loc.save()
        models.CiRegExp(regexp='path', loc_type=_loc, ci_type=_ci_type).save()

        self.assertEqual(_ci_type.code, _csc._ci_type_record(None, 'path', 'LOC').code) 
        self.assertEqual(_ci_type.code, _csc._ci_type_record('T_NONEXIST', 'path', 'LOC').code) 
