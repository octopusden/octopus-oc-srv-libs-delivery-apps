# coding: utf-8 --*
from django import test
from oc_delivery_apps.dlmanager.DLModels import DeliveryList, InvalidPathError
from oc_delivery_apps.dlmanager.models import Delivery, Client, FtpUploadClientOptions


class DeliveryListTestSuite(test.SimpleTestCase):

    def test_delivery_list_from_empty_list(self):
        dlist = DeliveryList([])
        self.assertEquals([], dlist.svn_files)
        self.assertEquals([], dlist.mvn_files)

    def test_delivery_list_from_empty_string(self):
        dlist = DeliveryList([])
        self.assertEquals([], dlist.svn_files)
        self.assertEquals([], dlist.mvn_files)

    def test_delivery_list_from_single_file(self):
        dlist = DeliveryList(["svn_file"])
        self.assertEquals(["svn_file"], dlist.svn_files)
        self.assertEquals([], dlist.mvn_files)

    def test_file_types_distinguished(self):
        dlist = DeliveryList(["svn_file", "g:a:v"])
        self.assertEquals(["svn_file"], dlist.svn_files)
        self.assertEquals(["g:a:v"], dlist.mvn_files)

    def test_all_files(self):
        dlist = DeliveryList(["svn_file", "g:a:v"])
        self.assertEquals(["svn_file", "g:a:v"], dlist.filelist)

    def test_string_filelist_parsed(self):
        dlist = DeliveryList("\n".join(["svn_file", "g:a:v"]))
        self.assertEquals(["svn_file"], dlist.svn_files)
        self.assertEquals(["g:a:v"], dlist.mvn_files)

    def test_string_with_colons_parsed(self):
        dlist = DeliveryList(";".join(["svn_file", "g:a:v"]))
        self.assertEquals(["svn_file"], dlist.svn_files)
        self.assertEquals(["g:a:v"], dlist.mvn_files)

    def test_empty_entries_skipped(self):
        dlist = DeliveryList(["svn_file", "", "g:a:v", ""])
        self.assertEquals(["svn_file"], dlist.svn_files)
        self.assertEquals(["g:a:v"], dlist.mvn_files)

    def test_whitespaces_entries_stripped(self):
        dlist = DeliveryList("\n\nsvn_file\n;\ng:a:v;")
        self.assertEquals(["svn_file"], dlist.svn_files)
        self.assertEquals(["g:a:v"], dlist.mvn_files)

    def test_none_as_empty_list(self):
        dlist = DeliveryList(None)
        self.assertEquals([], dlist.mvn_files)

    def test_delivery_list_inside_delivery(self):
        delivery = Delivery()
        delivery.mf_delivery_files_specified = "\n\nsvn_file\n;\ng:a:v;"
        dlist = delivery.delivery_list
        self.assertEquals(["svn_file", "g:a:v"], dlist.filelist)
        self.assertEquals(["svn_file", "g:a:v"], delivery.filelist)
        self.assertEquals(["svn_file"], dlist.svn_files)
        self.assertEquals(["svn_file"], delivery.svn_files)
        self.assertEquals(["g:a:v"], dlist.mvn_files)
        self.assertEquals(["g:a:v"], delivery.mvn_files)

    def test_dotted_pathes_parsed(self):
        dlist = DeliveryList(["./cards", "doc/.", "foo/./bar", "foo/../bar"])
        self.assertEquals(["cards", "doc", "foo/bar", "bar"], dlist.svn_files)

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
        # actually it is a problem only if russian chars are passed not as type(unicode)
        # 'Россия' in bytes
        #        rus_bytes=bytearray([0xD0, 0xA0, 0xD0, 0xBE, 0xD1, 0x81,
        #                             0xD1, 0x81, 0xD0, 0xB8, 0xD1, 0x8F])
        rus_str = 'Россия'
        dlist = DeliveryList([rus_str, ])
        self.assertEqual(["Россия", ], dlist.svn_files)


class ClientModelTestSuite(test.TestCase):

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
