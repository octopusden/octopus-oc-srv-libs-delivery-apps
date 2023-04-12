#!/usr/bin/env python3

import django.test
from . import django_settings
import oc_delivery_apps.checksums.models as models

class CheckSumsModelsTester(django.test.TestCase):
    def test_releasenotes_gav_generated__group(self):
        group = models.CiTypeGroups(code="TEST", name="TEST", rn_artifactid="foo")
        expected_gav = "com.example.rn.sfx.release_notes:foo:v123:txt"
        self.assertEqual(expected_gav, group.get_rn_gav("v123"))

    def test_documentation_gav_generated__group(self):
        group = models.CiTypeGroups(code="TEST", name="TEST", doc_artifactid="foo")
        expected_gav = "com.example.doc.sfx.documentation:foo:v123"
        self.assertEqual(expected_gav, group.get_doc_gav("v123"))

    def test_releasenotes_gav_generated__type(self):
        group = models.CiTypes(code="TEST", name="TEST", rn_artifactid="foo")
        expected_gav = "com.example.rn.sfx.release_notes:foo:v123:txt"
        self.assertEqual(expected_gav, group.get_rn_gav("v123"))

    def test_documentation_gav_generated__type(self):
        group = models.CiTypes(code="TEST", name="TEST", doc_artifactid="foo")
        expected_gav = "com.example.doc.sfx.documentation:foo:v123"
        self.assertEqual(expected_gav, group.get_doc_gav("v123"))

    def test_str(self):
        # testing all objects for correct string conversion

        self.assertEqual(
                str(models.CiTypes(code="CODE", name="Name", is_standard="Y", is_deliverable=False)),
                "CODE:(Name)")

        self.assertEqual(
                str(models.CiTypeGroups(code="CODE", name="Name")),
                "CODE:(Name)")

        self.assertEqual(
                str(models.CiTypeIncs(
                    ci_type_group=models.CiTypeGroups(code="CODE_G", name="Name"),
                    ci_type=models.CiTypes(code="CODE_T", name="Name", is_standard="Y", is_deliverable=False))),
                "'CODE_G'<=='CODE_T'")

        self.assertEqual(
                str(models.CsTypes(code='CODE', name='Name')),
                "CODE")

        self.assertEqual(
                str(models.LocTypes(code="CODE", name='Name')),
                "CODE:(Name)")

        self.assertEqual(
                str(models.CiRegExp(
                    loc_type=models.LocTypes(code="CODE", name="Name"),
                    ci_type=models.CiTypes(code="CODE", name="Name", is_standard="Y", is_deliverable=False),
                    regexp="regexp")),
                "regexp")

        _f = models.Files(
                pk=0,
                mime_type="mime/type",
                ci_type=models.CiTypes(code="CODE_T", name="Name", is_standard="Y", is_deliverable=False))

        self.assertEqual(
                str(_f),
                "0:mime/type:CODE_T")

        _cs = "01234567890abcdef01234567890abcdef"
        _cs_o = models.CheckSums(
                file=_f,
                checksum=_cs,
                cs_type=models.CsTypes(code='CODE', name='Name'))

        self.assertEqual(
                str(_cs_o),
                "0:CODE:%s" % (_cs))

        self.assertEqual(
                str(models.CsProv(
                    cs=_cs_o,
                    cs_prov="CODE_P"
                    )),
                "%s:CODE_P" % _cs)

        _cs_o_nst = models.CheckSumsNst(
                file=_f,
                checksum=_cs,
                cs_type=models.CsTypes(code='CODE', name='Name'))

        self.assertEqual(
                str(_cs_o_nst),
                "0:CODE:%s" % (_cs))

        self.assertTrue(
                str(models.Locations(
                    file=_f,
                    loc_type=models.LocTypes(code="LOC_C", name="Location Name"),
                    path="path")).startswith("0:LOC_C:path:"))

        self.assertTrue(
                str(models.Locations(
                    file=_f,
                    file_dst=_f,
                    loc_type=models.LocTypes(code="LOC_C", name="Location Name"),
                    path="path")).startswith("0:LOC_C:0[path]:"))
