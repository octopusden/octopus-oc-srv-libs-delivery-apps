#!/usr/bin/env python3

"""
Archive object wrapper
"""

# BEG: Helper class, registering archive content
import zipfile
import tarfile
import tempfile
import os
from oc_sql_helpers import str_decoder
import posixpath
import shutil

class ArchiveException(Exception):
    pass

class ArchiveObject(object):
    _mode = None  # mode - tar or zip
    _tmp = None  # temporary object
    _arch = None

    def __init__(self, fl_in):
        """ 
        initializaqtion consructor
        :param fl_in: file object to process, have to be opened in binary mode ('rb' at least)
        """
        try:
            fl_in.tell()
            fl_in.seek(0, 0)
        except:
            self._tmp = tempfile.NamedTemporaryFile()
            self._tmp.seek(0, os.SEEK_SET)
            shutil.copyfileobj(fl_in, self._tmp)
            self._tmp.flush()
            self._tmp.seek(0, os.SEEK_SET)
            fl_in = self._tmp
            pass

        self.__open(fl_in)

    def __open(self, fl_in):
        """
        Try to open an archive from _fl_tmp
        :param fl_in: file object to process, have to be opened in binary mode('rb' at least)
        """
        if self._mode is not None:
            # opened already
            return

        fl_in.seek(0, os.SEEK_SET)

        if(zipfile.is_zipfile(fl_in)):
            fl_in.seek(0, os.SEEK_SET)
            self._arch = zipfile.ZipFile(fl_in, 'r')
            self._mode = 'ZIP'
            return

        try:
            fl_in.seek(0, os.SEEK_SET)
            self._arch = tarfile.open(fileobj=fl_in, mode='r:*')
            self._mode = 'TAR'
            return
        except:
            self._mode = None
            pass

        raise ArchiveException(
            'Provided file is neither ZIP, noor TAR archive. Other types of archives are not supported yet.')

    def __del__(self):
        """
        What to do while deleting object
        """
        self.__close()

    def ls_files(self):
        """
        Returns a list of file names from the archive.
        :return list: dicts: each hast _utf decoded path as key and real path inside an archive as value
        """

        if self._mode == 'TAR':
            _ms = list(filter(lambda x: x.isfile(), self._arch.getmembers()))
            _ms = list(map(lambda x: {self.__decode_to_utf(x.name): x.name}, _ms))
            return _ms

        elif self._mode == 'ZIP':
            _ms = list(filter(lambda x: x.file_size and not self.__decode_to_utf(x.filename).endswith(posixpath.sep), self._arch.infolist()))
            _ms = list(map(lambda x: {self.__decode_to_utf(x.filename): x.filename}, _ms))
            return _ms

        raise ArchiveException('Archive content reading error.')

    def extract_temp(self, pth_e, pth):
        """
        Extract a member by an '_name' given to the temporary location and return temporary file object.
        :param str pth_e: path decoded to UTF-8
        :param pth: str or bytes object to the path object, as it returned by corresponding module
        :return NamedTemporaryFile:
        """

        # make suffix as extension only - needed for 'wrap' to work correctly
        # limit it to five characters - usually it is enough for real extensions
        _rs = tempfile.NamedTemporaryFile(suffix=list(posixpath.splitext(pth_e)).pop()[0:5])

        if self._mode == 'TAR':
            # unfortunately 'shutil.copyfileobj' does not work properly here
            # because 'tarfile' has no support for 'chunk' reading
            _rs.write(self._arch.extractfile(pth).read())
        elif self._mode == 'ZIP':
            with self._arch.open(pth) as _f:
                shutil.copyfileobj(_f, _rs)

        _rs.flush()
        _rs.seek(0, 0)

        return _rs

    def __close(self):
        """
        Closes the archive and deletes from temporary location
        """
        if self._arch is not None:
            self._arch.close()
            self._arch = None

        if self._tmp is not None:
            self._tmp.close()
            self._tmp = None

        self._mode = None

    def __decode_to_utf(self, todec):
        """
        Autodetects encoding of 'todec' and returns re-coded to UTF-8 (as 'str' object always)
        :param todec: str or bytes to decode
        :return str: string decoded to UTF-8 (unicode object)
        """

        # 'zipfile' and 'tarfile' are always trying to represent filenames in UTF, but this may be ugly for Win-created archives
        # Thus it is necessary to force decoding to 'bytes' object and try to auto-detect encoding.

        if isinstance(todec, str) :
            todec = todec.encode('utf-8', 'surrogateescape')

        if not isinstance(todec, bytes):
            # return an object itself this case because no encoding detection may be done
            return todec

        return str_decoder.decode_to_str(todec)
# END: Helper class for registering archive content


