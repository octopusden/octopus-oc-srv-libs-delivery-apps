#!/usr/bin/env python3
# coding: utf-8 --*
import django.test
from . import django_settings
from oc_delivery_apps.dlmanager.DLModels import DeliveryList, InvalidPathError
import oc_delivery_apps.dlmanager.models as models
import django.contrib.auth.models as auth_models
import datetime

# disable extra logging output
import logging
logging.getLogger().propagate = False
logging.getLogger().disabled = True

class DeliveryModelsTestSuite(django.test.TestCase):
    def setUp(self):
        # this tests all migrations also
        django.core.management.call_command('migrate', verbosity=0, interactive=False)

    def tearDown(self):
        django.core.management.call_command('flush', verbosity=0, interactive=False)

    def test_delivery_attributes(self):
        _m = models.Delivery(groupid="groupId.BOMBY", artifactid="artifactId", version="version")
        _m.mf_delivery_files_specified = 'g:a:v1:zip; b/r/t/g.txt'
        _m.save()
        self.assertEqual(str(_m), "groupId.BOMBY:artifactId:version:zip")
        self.assertEqual(_m.gav, "groupId.BOMBY:artifactId:version:zip")
        self.assertEqual(_m.client_name, "BOMBY")
        self.assertEqual(len(_m.filelist), 2)
        self.assertIn('g:a:v1:zip', _m.filelist)
        self.assertIn('b/r/t/g.txt', _m.filelist)
        self.assertEqual(_m.mvn_files, ['g:a:v1:zip'])
        self.assertEqual(_m.svn_files, ['b/r/t/g.txt'])
        self.assertEqual(_m.delivery_name, "artifactId-version")
    
    def test_set_flags(self):
        _m = models.Delivery(groupid="groupId.BOMBY", artifactid="artifactId", version="version")
        _m.mf_delivery_files_specified = 'g:a:v2:zip; b/r/t/g-g.txt'
        _m.save()

        _m.set_approved(True, 'user')
        self.assertTrue(_m.flag_approved)
        self.assertEqual(_m.request_by, "user")
        self.assertEqual(_m.get_flags_description(), "Approved, waiting for delivery")
        _m.set_uploaded(True, 'user2')
        self.assertTrue(_m.flag_uploaded)
        self.assertEqual(_m.request_by, "user2")
        self.assertEqual(_m.get_flags_description(), "Delivered")
        _m.set_approved(False, 'user3')
        self.assertFalse(_m.flag_approved)
        self.assertEqual(_m.request_by, "user3")
        self.assertEqual(_m.get_flags_description(), "Delivered")
        _m.set_approved(True, 'user')
        _m.set_failed(True, 'user')
        self.assertTrue(_m.flag_failed)
        self.assertEqual(_m.get_flags_description(), "Marked as bad after delivery")
        _m.set_approved(False, 'user')
        self.assertFalse(_m.flag_approved)
        self.assertEqual(_m.get_flags_description(), "Marked as bad after delivery")

class DeliveryHistoryTestSuite(django.test.TransactionTestCase):
    def setUp(self):
        django.core.management.call_command('migrate', verbosity=0, interactive=False)

    def tearDown(self):
        django.core.management.call_command('flush', verbosity=0, interactive=False)

    def test_change_user(self):
        # create two users
        _user_1 = auth_models.User(username="user_1")
        _user_1.save()
        _user_2 = auth_models.User(username="user_2")
        _user_2.save()
        _m = models.Delivery(groupid="groupId.BOMBY", artifactid="artifactId", version="version")
        _m.mf_delivery_files_specified = 'g:a:v2:zip; b/r/t/g-g.txt'
        _m.mf_delivery_author = "user_1"
        _m.save()
        self.assertEqual(_m.history.all().count(), 1)
        _m._change_reason = "Testy Test"
        _m.set_approved(True, "user_2")
        self.assertEqual(_m.history.all().count(), 2)
        _last_h = _m.history.first()
        self.assertEqual("Testy Test", _last_h.history_change_reason)
        self.assertTrue(_last_h.flag_approved)
        self.assertEqual(_last_h.request_by, "user_2")

class DeliveryListTestSuite(django.test.SimpleTestCase):

    def test_delivery_list_from_empty_list(self):
        dlist = DeliveryList([])
        self.assertEqual([], dlist.svn_files)
        self.assertEqual([], dlist.mvn_files)

    def test_delivery_list_from_empty_string(self):
        dlist = DeliveryList([])
        self.assertEqual([], dlist.svn_files)
        self.assertEqual([], dlist.mvn_files)

    def test_delivery_list_from_single_file(self):
        dlist = DeliveryList(["svn_file"])
        self.assertEqual(["svn_file"], dlist.svn_files)
        self.assertEqual([], dlist.mvn_files)

    def test_file_types_distinguished(self):
        dlist = DeliveryList(["svn_file", "g:a:v"])
        self.assertEqual(["svn_file"], dlist.svn_files)
        self.assertEqual(["g:a:v"], dlist.mvn_files)

    def test_all_files(self):
        dlist = DeliveryList(["svn_file", "g:a:v"])
        self.assertEqual(["svn_file", "g:a:v"], dlist.filelist)

    def test_string_filelist_parsed(self):
        dlist = DeliveryList("\n".join(["svn_file", "g:a:v"]))
        self.assertEqual(["svn_file"], dlist.svn_files)
        self.assertEqual(["g:a:v"], dlist.mvn_files)

    def test_string_with_colons_parsed(self):
        dlist = DeliveryList(";".join(["svn_file", "g:a:v"]))
        self.assertEqual(["svn_file"], dlist.svn_files)
        self.assertEqual(["g:a:v"], dlist.mvn_files)

    def test_empty_entries_skipped(self):
        dlist = DeliveryList(["svn_file", "", "g:a:v", ""])
        self.assertEqual(["svn_file"], dlist.svn_files)
        self.assertEqual(["g:a:v"], dlist.mvn_files)

    def test_whitespaces_entries_stripped(self):
        dlist = DeliveryList("\n\nsvn_file\n;\ng:a:v;")
        self.assertEqual(["svn_file"], dlist.svn_files)
        self.assertEqual(["g:a:v"], dlist.mvn_files)

    def test_none_as_empty_list(self):
        dlist = DeliveryList(None)
        self.assertEqual([], dlist.mvn_files)

    def test_delivery_list_inside_delivery(self):
        delivery = models.Delivery()
        delivery.mf_delivery_files_specified = "\n\nsvn_file\n;\ng:a:v;"
        dlist = delivery.delivery_list
        self.assertEqual(["svn_file", "g:a:v"], dlist.filelist)
        self.assertEqual(["svn_file", "g:a:v"], delivery.filelist)
        self.assertEqual(["svn_file"], dlist.svn_files)
        self.assertEqual(["svn_file"], delivery.svn_files)
        self.assertEqual(["g:a:v"], dlist.mvn_files)
        self.assertEqual(["g:a:v"], delivery.mvn_files)

    def test_dotted_pathes_parsed(self):
        dlist = DeliveryList(["./cards", "doc/.", "foo/./bar", "foo/../bar"])
        self.assertEqual(["cards", "doc", "foo/bar", "bar"], dlist.svn_files)

    def test_root_path_rejected(self):
        with self.assertRaises(InvalidPathError):
            DeliveryList(["."])
        with self.assertRaises(InvalidPathError):
            DeliveryList(["/"])
        with self.assertRaises(InvalidPathError):
            DeliveryList(["bar/.."])

    def test_parents_rejected(self):
        with self.assertRaises(InvalidPathError):
            DeliveryList([".."])
        with self.assertRaises(InvalidPathError):
            DeliveryList(["../foo"])
        with self.assertRaises(InvalidPathError):
            DeliveryList(["foo/../.."])

    def test_russian_symbols_processed(self):
        # actually it is a problem only if non-latin chars are passed
        _non_latin_str = 'что-нибудь-не-латинское'
        dlist = DeliveryList([_non_latin_str, ])
        self.assertEqual(["что-нибудь-не-латинское", ], dlist.svn_files)


class ClientModelTestSuite(django.test.TestCase):

    def test_client_reachable_initially(self):
        self.assertTrue(models.Client().is_reachable)

    def test_nonreachable_setup_detected(self):
        client, _ = models.Client.objects.get_or_create()
        models.FtpUploadClientOptions(client=client, can_receive=False).save()
        self.assertFalse(client.is_reachable)

    def test_reachable_setup_detected(self):
        client, _ = models.Client.objects.get_or_create()
        models.FtpUploadClientOptions(client=client, can_receive=True).save()
        self.assertTrue(client.is_reachable)

class DeliveryHistoryModelTestSuite(django.test.TestCase):
    """
    Do not hesitate for DeliveryHistoryTestSuite which tests historical records
    This one tests separate status change table. To be removed with this leagcy
    """
    def setUp(self):
        django.core.management.call_command('migrate', verbosity=0, interactive=False)

    def tearDown(self):
        django.core.management.call_command('flush', verbosity=0, interactive=False)

    def test_status_change(self):
        _m = models.Delivery(groupid="groupId.BOMBY", artifactid="artifactId", version="version")
        _m.mf_delivery_files_specified = 'g:a:v2:zip; b/r/t/g-g.txt'
        _m.save()

        _h = models.DeliveryHistory()
        _h.deliveryid = _m
        _h.change_by = 'user_1'
        _h.message = 'The Message'
        _h.time = datetime.datetime.now().replace(tzinfo=datetime.timezone.utc)
        _h.save()

        _h = models.DeliveryHistory()
        _h.deliveryid = _m
        _h.change_by = 'user_2'
        _h.message = 'The Message 2'
        _h.time = datetime.datetime.now().replace(tzinfo=datetime.timezone.utc)
        _h.flag_approved = True
        _h.save()

        _m.refresh_from_db()
        self.assertEqual(models.DeliveryHistory.objects.filter(deliveryid=_m).count(), 2)

class TestClientRelations(django.test.TestCase):
    def setUp(self):
        django.core.management.call_command('migrate', verbosity=0, interactive=False)

    def tearDown(self):
        django.core.management.call_command('flush', verbosity=0, interactive=False)

    def test_business_status(self):
        _bs = models.BusinessStatus()
        _bs.description = _bs.statuses_names.get('received')
        _bs.save()
        _m = models.Delivery(groupid="groupId.BOMBY", artifactid="artifactId", version="version")
        _m.mf_delivery_files_specified = 'g:a:v2:zip; b/r/t/g-g.txt'
        _m.business_status = _bs
        _m.save()
        self.assertEqual(_m.business_status.description, "Received by client")
        _bs = models.BusinessStatus()
        _bs.description = _bs.statuses_names.get('rejected')
        _bs.save()
        _m.business_status = _bs
        _m.save()
        self.assertEqual(_m.business_status.description, "Rejected by client")

    def test_client_language(self):
        _lng = models.ClientLanguage(code='SMTH', description="Something")
        _lng.save()
        _client = models.Client(code="SMTTEST", name="Sometning Test", is_active=False, language=_lng)
        _client.save()
        _client.refresh_from_db()
        self.assertEqual(_client.language.code, 'SMTH')

    def test_client_user(self):
        pass

    def test_client_mail(self):
        pass

    def test_jira_projects(self):
        pass
