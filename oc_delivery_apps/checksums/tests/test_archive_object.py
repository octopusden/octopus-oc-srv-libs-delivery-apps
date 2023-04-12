#!/usr/bin/env python3

import unittest
import zipfile
import tarfile
import random
import tempfile
import os
from ..archive_object import ArchiveObject, ArchiveException

class ArchiveObjectTest(unittest.TestCase):
    ## most of tests are not classic 'unit' tests because we need to check exact module integration also
    ## each test comes with: file structure, opening, list files (with national characters), extract
    ## no encoding detection tests included since this is unusual case and should be avoided

    ## cases:
    ## 1. normal zip archive
    ## 2. normal tar archive
    ## 3. normal tar.gz archive
    ## 4. normal tar.bz2 archive
    ## 5. corrupted zip archive
    ## 6. corrupted tar archive
    ## 7. normal zip archive in IOFileBuffer (does not support 'seek' operation but may be 'copyfileobj'-ed)

    # helper
    def _cyrillic_filename(self):
        _cyr_str = 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя'
        _cyr_str += _cyr_str.upper()

        _len = random.randint(5,10)
        _res = ""

        while len(_res) < _len:
            _res += random.choice(_cyr_str)

        return _res

    def setUp(self):
        # prepare filesystem with random archive content
        self._archive_content = list()
        self._archive_fs = tempfile.TemporaryDirectory()
        _files = random.randint(5, 10)

        while len(self._archive_content) < _files:
            _name = self._cyrillic_filename()
            self._archive_content.append(_name)
            _size = random.randint(10, 20)

            with open(os.path.join(self._archive_fs.name, _name), mode='wb') as _fl_out:
                _fl_out.write(random.choice(_name).encode('utf-8'))

    def tearDown(self):
        self.archive_content = None

        if self._archive_fs:
            self._archive_fs.cleanup()
            self._archive_f = None

    def __pack_zipfile(self):
        _zip_bin = tempfile.NamedTemporaryFile()
        _zip_a = zipfile.ZipFile(_zip_bin, mode='w')
        
        for _filename in self._archive_content:
            _zip_a.write(os.path.join(self._archive_fs.name, _filename), _filename)

        _zip_a.close()

        _zip_bin.flush()
        _zip_bin.seek(0, os.SEEK_SET)

        self.assertTrue(zipfile.is_zipfile(_zip_bin))

        _zip_bin.seek(0, os.SEEK_SET)

        return _zip_bin

    def test_zip_archive__ok(self):
        # create archive
        # using unicode here, because
        # 'zip' has a very strange scenarios for encoding non-ascii filenames on different OS-es, and they are poorly documented

        _zip_bin = self.__pack_zipfile()
        _ao = ArchiveObject(_zip_bin)
        self.assertEqual(_ao._mode, 'ZIP')
        self.__assert_lists_and_decompressions(_ao)
        _zip_bin.close()

    def __assert_lists_and_decompressions(self, archive):
        # assert archive content
        # assertion of lists is made in loop since 'assertEqual' may fail because of element order
        _expected = list(map(lambda x: {x: x}, self._archive_content))
        _actual = archive.ls_files()

        self.assertEqual(len(_expected), len(_actual))

        for _t in _expected:
            self.assertIn(_t, _actual)

        # test decompression and assert files
        for _x in _expected:
            for _k, _v in _x.items():
                # should be single value, but there is no method in 'dict' to get a key only
                with open(os.path.join(self._archive_fs.name, _k), mode='rb') as _byi:
                    _kyi = archive.extract_temp(_k, _v)
                    _kyi.seek(0, os.SEEK_SET)
                    self.assertEqual(_byi.read(), _kyi.read())
                    _kyi.close()


    def __pack_tarfile(self, mode):
        # helper to pack a tar with a compression given
        _arch = tempfile.NamedTemporaryFile()

        with tarfile.open(fileobj=_arch, mode=mode) as _tar_a:
            for _filename in self._archive_content:
                _tar_a.add(os.path.join(self._archive_fs.name, _filename), arcname=_filename, recursive=False)

            _tar_a.close()

        _arch.flush()
        _arch.seek(0, os.SEEK_SET)
        return _arch


    def test_tar_archive__ok(self):
        _tar_bin = self.__pack_tarfile("w:")
        _ao = ArchiveObject(_tar_bin)
        self.__assert_lists_and_decompressions(_ao)
        _tar_bin.close()


    def test_tar_gz_archive__ok(self):
        _tar_bin = self.__pack_tarfile("w:gz")
        _ao = ArchiveObject(_tar_bin)
        self.__assert_lists_and_decompressions(_ao)
        _tar_bin.close()


    def test_tar_bz_archive__ok(self):
        _tar_bin = self.__pack_tarfile("w:bz2")
        _ao = ArchiveObject(_tar_bin)
        self.__assert_lists_and_decompressions(_ao)
        _tar_bin.close()

    def test_archive__fail(self):
        # get real archive and corrupt it by skipping odd bytes
        _zip_bin = self.__pack_zipfile()
        _corrupted_bin = tempfile.NamedTemporaryFile()
        _zip_bin.seek(0, os.SEEK_SET)

        while True:
            _b = _zip_bin.read(1)

            if not _b:
                break

            _corrupted_bin.write(_b)
            _zip_bin.seek(1, os.SEEK_CUR)

        with self.assertRaises(ArchiveException):
            _ao = ArchiveObject(_corrupted_bin)

        _corrupted_bin.close()
        _zip_bin.close()

    def test_tar_archie__fail(self):
        # get real archive and corrupt it by skipping odd bytes
        _tar_bin = self.__pack_tarfile("w:")
        _corrupted_bin = tempfile.NamedTemporaryFile()
        _tar_bin.seek(0, os.SEEK_SET)

        while True:
            _b = _tar_bin.read(1)

            if not _b:
                break

            _corrupted_bin.write(_b)
            _tar_bin.seek(1, os.SEEK_CUR)

        with self.assertRaises(ArchiveException):
            _ao = ArchiveObject(_corrupted_bin)

        _corrupted_bin.close()
        _tar_bin.close()


    def test_buffer__ok(self):
        # pack zip into tar and try to read it
        _zip_f = self.__pack_zipfile()
        _zip_n = os.path.basename(_zip_f.name)
        _tar_bin = tempfile.NamedTemporaryFile()
        _tar_a = tarfile.open(fileobj=_tar_bin, mode='w:')
        _tar_a.add(_zip_f.name, arcname=_zip_n, recursive=False)
        _tar_a.close()
        _tar_bin.flush()
        _tar_bin.seek(0, 0)
        _zip_f.close()
        _tar_a = tarfile.open(fileobj=_tar_bin, mode='r:*')
        _zip_bin = _tar_a.extractfile(_zip_n)
        _ao = ArchiveObject(_zip_bin)
        self.__assert_lists_and_decompressions(_ao)
        _zip_bin.close()
        _tar_bin.close()
