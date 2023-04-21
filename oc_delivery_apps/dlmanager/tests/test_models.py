# coding: utf-8 --*
import django.test
from . import django_settings
from oc_delivery_apps.dlmanager.DLModels import DeliveryList, InvalidPathError
from oc_delivery_apps.dlmanager.models import Delivery, Client, FtpUploadClientOptions


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
        delivery = Delivery()
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
        self.assertTrue(Client().is_reachable)

    def test_nonreachable_setup_detected(self):
        client, _ = Client.objects.get_or_create()
        FtpUploadClientOptions(client=client, can_receive=False).save()
        self.assertFalse(client.is_reachable)

    def test_reachable_setup_detected(self):
        client, _ = Client.objects.get_or_create()
        FtpUploadClientOptions(client=client, can_receive=True).save()
        self.assertTrue(client.is_reachable)
