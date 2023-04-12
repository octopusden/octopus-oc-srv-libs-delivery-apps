# controllers for dlcontents django models

from . import models
from . import archive_object
from django.db import transaction, IntegrityError
from oc_sql_helpers import wrapper, normalizer
from django.utils import timezone
import re
import hashlib
import magic
import tempfile
import os
import posixpath
import shutil
import logging

#BEG: DICTIONARIES
# specific calculations should be placed here if needed
#END: DICTIONARIES

# BEG: MAIN CONTROLLER


class CheckSumsController(object):
    __m_mag = None
    __sql_limit = 3 * 1024 * 1024  # 3M, maximum size of possble PL/SQL files

    def get_file_by_checksum(self, checksum, cs_type="MD5", cs_prov="Regular"):
        """
        function to get file objcect (from model) by checksum
        does not see is the str_cs_prov of 'strict' aprropriation or not.
        :param str checksum: checksum
        :param str cs_type: checksum type code
        :param str cs_prov: checksum provider( regular, wrapped, unwrapped, e.t.c. )
        :return: file instance of last stored file with a checksum provided; or None if nothing found
        """

        _csp = models.CsProv.objects.filter(
                cs_prov=cs_prov, cs__cs_type__code=cs_type, cs__checksum=checksum).order_by('id')

        if _csp.count() == 0:
            # see strict correspondance of checksum + cs_type
            _csp = models.CheckSums.objects.filter(cs_type__code=cs_type, checksum=checksum).order_by('id')

            if _csp.count() == 0:
                return None

            return _csp.last().file

        return _csp.last().cs.file

    def get_checksum_by_file(self, file_r, cs_type="MD5", cs_prov="Regular"):
        """
        returns checksum by file objcect instance (from model)
        does not filter 'strict' appropriation
        :param file_r: file instance (from database)
        :param str cs_type: checksum type code
        :param str cs_prov: checksum provider( regular, wrapped, unwrapped, e.t.c. )
        :return str: string with checksum, None if not found
        """
        _csp = models.CsProv.objects.filter(cs__file=file_r, cs__cs_type__code=cs_type, cs_prov=cs_prov).order_by('id')

        if _csp.count() == 0:
            return None

        return _csp.last().cs.checksum

    def get_file_by_location(self, location, loc_type, date_s=None, revision=None, history=True):
        """
        function to get file by location at date
        :param str location: file location path
        :param str loc_type: location type code
        :param datetime date_s: datetime object to check location at, now() by default
        :param revision: str or int, revision of an object in VCS (if exist), may be None
        :param bool history: search history for location or not
        :return: File instance or None if not found
        """
        location = location.strip()

        if not loc_type:
            raise ValueError("Location type is required")

        loc_type = loc_type.upper()

        if isinstance(revision, int):
            revision = "%d" % revision

        if not revision:
            if loc_type == "SVN":
                raise ValueError("Revision required for SVN location")

            revision = None


        if not date_s:
            date_s = timezone.now()

        # query to location table:
        _loc = models.Locations.objects.filter(loc_type__code=loc_type, path=location,
                input_date__lte=date_s, revision=revision, file_dst=None).order_by('input_date')

        if _loc.count() == 0 and history:
            _loc = models.Locations.history.filter(loc_type__code=loc_type, path=location,
                    input_date__lte=date_s, revision=revision, file_dst=None).order_by('input_date')

        if _loc.count() == 0:
            return None

        return _loc.last().file


    def is_file_exist(self, file_r, location, loc_type, date_s=None, revision=None):
        """
        function checks if given file was at given location at given date
        :param file_r: File instance (from database)
        :param str location: location path
        :param str loc_type: location type code
        :param datetime date_s: datetime to check existence for
        :param revision: str or int, revision of an object in VCS (if exist), may be None
        :return: boolean, True if file was there, False otherwise. If Location is marked deleted - False is returned.
        """
        _file_g = self.get_file_by_location(location, loc_type, date_s, revision, history=False)

        return bool(_file_g is not None and file_r == _file_g)

    def add_checksum(self, file_r, checksum, cs_type="MD5", cs_prov="Regular"):
        """
        adds checksum to file with given instance (from model)
        WARNING: does nothing if duplicate is trying to be added
        :param file_r: File instance (from database)
        :param str checksum: string with MD5 checksum
        :param str cs_type: checksum type code
        :param str cs_prov: checksum provider
        :return: new checksum object or None if failed
        """
        checksum = checksum.strip()
        cs_type = cs_type.strip()
        cs_prov = cs_prov.strip()

        _cs_type = models.CsTypes.objects.filter(code=cs_type).last()

        _cs = None
        try:
            with transaction.atomic():
                _cs = models.CheckSums(file=file_r, cs_type=_cs_type, checksum=checksum)
                _cs.save()

        except IntegrityError:
            _cs = models.CheckSums.objects.filter(file=file_r, cs_type=_cs_type, checksum=checksum).last()

            if not _cs:
                raise

            pass

        try:
            with transaction.atomic():
                _csprov = models.CsProv(cs=_cs, cs_prov=cs_prov)
                _csprov.save()

        except IntegrityError:
            if models.CsProv.objects.filter(cs=_cs, cs_prov=cs_prov).count() != 1:
                raise

            pass  # do not write duplicate

        return _cs

    def add_location(self, file_r, location, loc_type, revision=None):
        """
        adds location to given file
        duplicates are checken, none will be created if exist
        :param file_r: File instance (from database)
        :param str location: location path
        :param str loc_type: location type code
        :param revision: str or int, revision of an object in VCS (if exist), may be None
        :return: new location object of None if failed
        """
        location = location.strip()

        _loc_type = models.LocTypes.objects.filter(code=loc_type.upper()).last()

        if not _loc_type:
            raise ValueError("Location type is not found: %s" % loc_type)

        if isinstance(revision, int):
            revision = "%d" % revision

        if not revision:
            if _loc_type.code == "SVN":
                raise ValueError("'SVN' location type requires a revision.")

            revision = None

        try:
            with transaction.atomic():
                _loc = models.Locations(file=file_r, path=location, loc_type=_loc_type, revision=revision, file_dst=None)
                _loc.save()

        except IntegrityError:
            _loc = models.Locations.objects.filter(path=location, loc_type=_loc_type, revision=revision, file_dst=None).last()

            if not _loc:
                raise

            if _loc.file != file_r:
                _loc.file = file_r
                _loc._change_reason = 'Location overwritten with new file'
                _loc.save()

            pass

        return _loc

    def add_location_checksum(self, checksum, location, loc_type, ci_type, mime_type="Data", cs_type="MD5", cs_prov="Regular", revision=None):
        """
        universal function to add checksum for a location
        does checks for duplicates
        does not adds if 'cs_prov' is not of 'strict' appropriation
        :param str location: file location path
        :param str loc_type: location type code
        :param str ci_type: code of CI type of a file
        :param str mime_type: MIME-type of a file
        :param str checksum: checksum
        :param str cs_type: checksum type code
        :param str cs_prov: checksum provider
        :param revision: str or int, revision of an object in VCS (if exist), may be None
        :return bool: True on success, False otherwise
        """
        # get rid of trash in the arguments
        location = location.strip()
        loc_type = loc_type.strip().upper()
        ci_type = ci_type.strip().upper()
        mime_type = mime_type.strip()
        checksum = checksum.strip()
        cs_type = cs_type.strip().upper()
        cs_prov = cs_prov.strip()

        if not self._is_strict_cs_prov(cs_prov):
            return False

        # otherwise store all. IS_DELETED will be False by Model.
        _ci_type = models.CiTypes.objects.filter(code=ci_type).last()
        _loc = None
        _cs = None

        if not _ci_type:
            # do not using 'get' since it will raise unnecessary exception in case of failure
            _ci_type = models.CiTypes.objects.filter(code="FILE").last()

        try:
            with transaction.atomic():
                _file = models.Files(ci_type=_ci_type, mime_type=mime_type)
                _file.save()
                _loc = self.add_location(_file, location, loc_type, revision)
                _cs = self.add_checksum(_file, checksum, cs_type, cs_prov)
        except IntegrityError:
            # now check: file for this location or with such a checksum is already in database
            # if file was previously deleted from a location given then '_file_loc' will be None
            _file_cs = self.get_file_by_checksum(checksum, cs_type, cs_prov)
            _file_loc = self.get_file_by_location(location, loc_type, revision=revision, history=False)

            if (_file_cs is not None) and (_file_loc is not None) and (_file_cs == _file_loc):
                return True

            # if file by checksum is found store location only
            # also this case is for previously deleted file
            if (_file_cs is not None):
                return (self.add_location(_file_cs, location, loc_type, revision) is not None)

            # if file by checksum was not found - it is a crime, raise an exception
            raise

        return (_loc is not None) and (_cs is not None)

    def get_location_checksum(self, location, loc_type, cs_type="MD5", cs_prov="Regular", revision=None):
        """
        get checksum by location
        does not checks is 'cs_porv' of 'strict' appropriation or not
        does not support for a history, that is no 'deleted' locations checksums will be returned
        :param self: reference to self class instance
        :param str location: file location path
        :param str loc_type: location type code
        :param str cs_type: checksum type code
        :param str cs_prov: checksum provider
        :param revision: str or int, revision of an object in VCS (if exist), may be None
        :return: MD5 sum or None if not found
        """
        _file = self.get_file_by_location(location, loc_type, revision=revision, history=False)

        return self.get_checksum_by_file(_file, cs_type, cs_prov)

    def add_inclusion(self, fl_child, fl_parent, path):
        """
        Adds inclusion of file object one to another if not exist. Checks for duplicates
        WARNING: None objects are not permittable for the arguments.
        :param self: self class object reference
        :param fl_child: file record for a child to be included, from model, not file-system-like object
        :param fl_parent: file record for a parent child to be included to, from model, not file-system-like object
        :param str path: path inside the archive
        :return int: number of inclusions
        """
        if not path:
            raise ValueError("Path inside the archive is required")

        if not fl_child:
            raise ValueError("Child file record required")

        if not fl_parent:
            raise ValueError("Parent file record required")

        if fl_child == fl_parent:
            return 1  # file is always included to itself

        logging.debug("Inclusion: %d=>%d[%s]" % (fl_child.id, fl_parent.id, path))
        _loc_type = models.LocTypes.objects.filter(code="ARCH").last()

        if not _loc_type:
            raise ValueError("Location type 'ARCH' not found in database")

        _qs_inc = models.Locations.objects.filter(file=fl_child, file_dst=fl_parent, loc_type=_loc_type, path=path, revision=None)

        try:
            with transaction.atomic():
                _inc = models.Locations(file=fl_child, file_dst=fl_parent, loc_type=_loc_type, path=path, revision=None)
                _inc.save()
        except IntegrityError:
            if (_qs_inc.count() == 0):
                raise

            # otherwise we've got such a record already
            pass

        return _qs_inc.count()

    def add_inclusion_checksums(self, cs_child, cs_parent, path, cs_type_child="MD5", cs_type_parent="MD5", cs_prov_child="Regular", cs_prov_parent="Regular", skip_absent=False):
        """
        Adds inclustion record by given checksums.
        Does check that both 'cs_prov's are of 'strict' appropriation
        :param str cs_child: checksum of the file included
        :param str cs_parent: checksum of the file where 'str_md5_child' is included to
        :param str path: path of 'cs_child' in the archive 'cs_parent'
        :param str cs_type_child: checksum type code of 'str_md5_child'
        :param str cs_type_parent: checksum type code of 'str_md5_parent'
        :param str cs_prov_child: checksum provider of 'str_md5_child'
        :param str cs_prov_parent: checksum provider of 'str_md5_parent'
        :param bool skip_absent: do not raise an exception if 'cs_child' is not in database
        :return int: integer, how many inclusions of such a type are, should always be 1
        """
        if any([not self._is_strict_cs_prov(cs_prov_child), not self._is_strict_cs_prov(cs_prov_parent)]):
            return 0

        _fl_child = self.get_file_by_checksum(cs_child, cs_type_child, cs_prov_child)
        _fl_parent = self.get_file_by_checksum(cs_parent, cs_type_parent, cs_prov_parent)

        if skip_absent and any([not _fl_child, not _fl_parent]):
            # no such file in database, can't include - so skip if we forced to do so
            return 0

        return self.add_inclusion(_fl_child, _fl_parent, path)

    def ci_type_by_path(self, path, loc_type):
        """
        Get ci-type code by path given and location type. Searches by regexp's in database and returns first CI_TYPE which's regexp path given has met to.
        :param str path: location path
        :param loc_type: location type code
        :return str: ci-type code, or None if not found
        """

        if not loc_type:
            raise ValueError("Location type is mandatory")

        if not path:
            raise ValueError("Path is mandatory")

        for _regexp in models.CiRegExp.objects.filter(loc_type__code=loc_type).all():
            _regexp_s = _regexp.regexp.replace('_VERSION_', '[^:]*')

            if re.match(_regexp_s, path):
                return _regexp.ci_type.code

        return None

    def ci_type_by_gav(self, gav):
        """
        Get ci-type code by GAV from nexus. Compares GAV with regexp's in database and returns first CI_TYPE to which's regexp GAV given has met to.
        :param str gav: gav
        :return str: ci-type code, or None if not found
        """
        return self.ci_type_by_path(gav, "NXS")

    def md5(self, fl_o):
        """
        Calculates MD5 checksum of a file-like object given and returns it as string. File object have to be open already.
        NOTE:    seek() of file object is set to begin first. And after return from this function seek is set back to the original position.
            Original position is obtained by tell() method.
        :param fl_0: file or file-like python object, opened already in BINARY mode
        :return str: MD5 checksum
        """
        _pos = fl_o.tell()
        fl_o.seek(0, os.SEEK_SET)  # file postion to the beginning
        _hmd5 = hashlib.md5()
        while True:
            # read in 1M chunks, 16M was too much
            _chunk = fl_o.read(1 * 1024 * 1024)

            if not _chunk:
                break

            _hmd5.update(_chunk)

        fl_o.seek(_pos, os.SEEK_SET)  # set position back to original
        return _hmd5.hexdigest()

    def mime(self, fl_o):
        """
        Tries to gess MIME-type of a file-like object given and returns it as string. File object have to be open already.
        NOTE:    seek() of file object is set to begin first. 
            And after return from this function seek is set back to the original position.
            Original position is obtained by tell() method.
        :param fl_o: file or file-like python object, opened already in BINARY mode
        :return str: MIME-type of a file
        """
        _pos = fl_o.tell()
        fl_o.seek(0, os.SEEK_SET)  # file postion to the beginning

        if self.__m_mag is None:
            self.__m_mag = magic.Magic(mime=True)

        _mime = self.__m_mag.from_buffer(fl_o.read(512)) # 512 bytes is enough to guess type
        fl_o.seek(_pos, os.SEEK_SET)  # set position back to original

        return _mime

    def get_file_by_checksums_dict(self, cs_d, strict_only=True):
        """
        Returns dictionary with file object (from model) for given checksums dictionary 'cs_d'.
        :param dict cs_d: keys are 'cs_prov's and values are dictinaries where keys are 'cs_type's (currently MD5) and values are checksums.
        :param bool strict_only: True if "strict" appropriation is required only, False - see "non-strict" too
        :return: None if nothing found. Tuple with three values: (str 'cs_prov', fl_m 'file_object_from_model', bool 'is_strict' ).
        """

        # first see 'strict' appropriation
        # no checks for 'x' given since __cs_providers is private and hardcoded, so key absence is a bug
        _keys = sorted(self.__cs_providers.keys(), key=lambda x: self.__cs_providers.get(x).get("search"))
        _keys_strict = list(filter(lambda x: self._is_strict_cs_prov(x), _keys))

        for _key in list(filter(lambda x: x in cs_d, _keys_strict)):
            _cs_d_s = cs_d.get(_key)

            for _cs_type in _cs_d_s:
                _fl_m = self.get_file_by_checksum(cs_d.get(_key).get(_cs_type), cs_type=_cs_type, cs_prov=_key)

                if _fl_m:
                    return (_key, _fl_m, True)

        # nothing found in strict, see non-strict if allowed:
        if strict_only:
            return None

        _keys_non_strict = list(filter(lambda x: x not in _keys_strict, _keys))

        for _key in _keys_non_strict:
            for _key_s in filter(lambda x: x.startswith(_key), cs_d.keys()):

                _cs_d_s = cs_d.get(_key)

                for _cs_type in _cs_d_s:
                    _fl_m = self.get_file_by_checksum(cs_d.get(_key_s).get(_cs_type), cs_type=_cs_type, cs_prov=_key_s)

                    if _fl_m is not None:
                        return (_key_s, _fl_m, False)

        return None

    def _relink_file_duplicate(self, fr_orig, fr_dup):
        """
        Re-link duplicate - checksums, locations
        :param fr_orig: file record from model - original, not None
        :param fl_dup: file record from model - duplicate, not None
        :return: file record from model which is the real original file
        """
        # WARNING: strictly checking for *id* is not None, because 'not ...id' will give a false for zero
        if not fr_orig or fr_orig.id is None:
            raise ValueError('Original file record is mandatory')

        if not fr_dup or fr_dup.id is None:
            raise ValueError('Duplicate file record is mandatory')

        if fr_orig == fr_dup:
            raise ValueError('Unable to link duplicate to itself. FILE_ID = %s' % (fr_orig.id))

        fr_orig.refresh_from_db()
        fr_dup.refresh_from_db()
        _min_id = min(fr_orig.id, fr_dup.id)
        _max_id = max(fr_orig.id, fr_dup.id)
        _first_id = fr_orig.id
        _relink = list()

        # find reall original
        # this is a prevention from loop duplicate references
        while fr_orig.file_dup is not None and fr_orig.file_dup.id is not None:
            if fr_orig not in _relink:
                _relink.append(fr_orig)

            fr_orig = fr_orig.file_dup
            _min_id = min(_min_id, fr_orig.id)

            if fr_orig.file_dup is not None and fr_orig.file_dup.id == _first_id:
                break

        fr_orig = models.Files.objects.get(id=_min_id)
        # append file_dup from duplicate also
        _first_id = fr_dup.id

        while fr_dup.file_dup is not None and fr_dup.file_dup.id is not None:
            if fr_dup not in _relink:
                _relink.append(fr_dup)

            fr_dup = fr_dup.file_dup
            _max_id = max(_max_id, fr_dup.id)

            if fr_dup.file_dup is not None and fr_dup.file_dup.id == _first_id:
                break

        fr_dup = models.Files.objects.get(id=_max_id)

        if fr_dup not in _relink:
            _relink.append(fr_dup)

        if fr_orig not in _relink:
            _relink.append(fr_orig)

        for _fl_rel in _relink:
            # re-link checksums
            for _cs in models.CheckSums.objects.filter(file=_fl_rel).all():
                _cs.file = fr_orig
                _cs.save()

            # re-link locations
            for _loc in models.Locations.objects.filter(file=_fl_rel).all():
                _loc.file = fr_orig
                _loc.save()

            # re-link inclusions, but this should never happen
            for _loc in models.Locations.objects.filter(file_dst=_fl_rel).all():
                _loc.file_dst = fr_orig
                _loc.save()

            # link file as duplicate
            if _fl_rel != fr_orig:
                _fl_rel.file_dup = fr_orig
            else:
                _fl_rel.file_dup = None

            _fl_rel.save()

            self._update_current_inclusion_depth(fr_orig, _fl_rel.depth_level)

        fr_orig.refresh_from_db()

        return fr_orig

    def _reg_all_sql_cs_provs(self, file_r, cs_d, dup=False):
        """
        Helper to register all sql checksums from a given dictionary.
        :param file_r: file record from model, not None
        :param dict cs_d: dictionary with checksums calculated, not None. Keys are CS_PROViders, values are checksums itself as dict { 'TYPE':'value' }
        :param bool dup: re-link duplicate files found
        :return: file record from model to which all checksums was really linked to
        """
        for _cs_prov in cs_d.keys():
            for _cs_type, _cs_v in cs_d.get(_cs_prov).items():
                # add checksum
                _retry = True
                while _retry:
                    try:
                        with transaction.atomic():
                            self.add_checksum(file_r, _cs_v, cs_type=_cs_type, cs_prov=_cs_prov)
                        _retry = False
                    except IntegrityError:
                        if not dup:
                            raise

                        _file_r_dup = self.get_file_by_checksum(_cs_v, cs_type=_cs_type, cs_prov=_cs_prov)

                        if _file_r_dup == file_r:
                            raise

                        file_r = self._relink_file_duplicate(file_r, _file_r_dup)

                        _retry = True
                        pass

        return file_r

    def _register_sql(self, file_o, ci_type, loc_path=None, loc_type=None, loc_revision=None):
        """
        Registers sql file using normalization, wrapping, unwrapping, e.t.c
        :param file_o: python file or file-like object (not from model!), should be opened in BINARY mode
        :param str ci_type: CI_TYPE code, not None
        :param str loc_path: location path of file_o
        :param str loc_type: location type for loc_path. Will try to auto-detect if missing.
        :param loc_revision: str or int, location revision, may not be omitted for SVN location type
        :return: file record from model which was registered for an sql given
        """
        _file_pos = file_o.tell()
        _mime_type = self.mime(file_o)

        if not ci_type:
            ci_type = self.ci_type_by_path(loc_path, loc_type)

        _ci_type_r = models.CiTypes.objects.filter(code=ci_type).last()

        file_o.seek(0, os.SEEK_SET)
        _cs_d = self.get_all_sql_checksums(file_o)
        _fl_m_r = None
        try:
            with transaction.atomic():
                _fl_m_r = models.Files(ci_type=_ci_type_r, mime_type=_mime_type)
                _fl_m_r.save()
                _fl_m_r = self._reg_all_sql_cs_provs(_fl_m_r, _cs_d)

        except IntegrityError as _e:
            logging.exception(_e)
            _fl_m_r = self.get_file_by_checksums_dict(_cs_d)

            if _fl_m_r is None:
                raise

            _fl_m_r = _fl_m_r[1]  # get real file object from tuple
            _fl_m_r = self._reg_all_sql_cs_provs(_fl_m_r, _cs_d, dup=True)
            pass

        # check arguments is not needed since they are checked in sub-methods
        # one exception: location and location type have to be set in pair
        if loc_path and not loc_type:
            raise ValueError("loc_path is specified but loc_type is missing")

        if loc_path: 
            self.add_location(_fl_m_r, loc_path, loc_type, loc_revision)

        file_o.seek(_file_pos, 0)
        return _fl_m_r

    def _register_includes(self, file_o, file_r, ci_type_sub, inclusion_level, force_recalc, inclusion_level_calc):
        """
        unpack an archive from 'file_o' and register all files included to it
        :param file_o: file or file_like object of an archive from file system
        :param file_r: file record of an archive from model
        :param str ci_type_sub: ci_type for all included files. Will be set to FILE if not given
        :param int inclusion_level: try to register includes inside 'tar' or 'zip' archive at inclusion level specified in this parameter. 
        :param bool force_recalc: if True then all included archives contents is to be re-calculated even if it is found to be registered already
        :param int inclusion_level_calc: current inclusion level being calculated
        :return int: new inclusion level being calculated
        """
        # do not raise exception if file provided is not an archive
        _arch = None

        if not isinstance(inclusion_level, int) or inclusion_level <= 0:
            return inclusion_level_calc

        try:
            _arch = archive_object.ArchiveObject(file_o)
        except Exception as e:
            logging.exception(e)
            return inclusion_level_calc  # unable to open an archive, so do nothing

        if file_r is None:
            file_r = self.get_file_by_file_obj(file_o)

        if not ci_type_sub:
            ci_type_sub = 'FILE'

        inclusion_level_calc += 1
        if isinstance(inclusion_level, int):
            inclusion_level -= 1

        _inclusion_level_t = 0
        for _member_d in _arch.ls_files():
            _pth_utf, _pth_orig = list(_member_d.items()).pop()
            _file_o_memb = _arch.extract_temp(_pth_utf, _pth_orig)

            # to adjust the path we need: file_src, file_dst -> location record
            # file_dst is given already obj_loc_archive.file
            logging.debug("sub-member: [%d]%s" % (file_r.pk, _pth_utf))

            (_file_r_memb, _inclusion_level_t_u) = self._register_file_obj(_file_o_memb, ci_type_sub,
                    None, None, None, inclusion_level, ci_type_sub, force_recalc, inclusion_level_calc)
            self.add_inclusion(_file_r_memb, file_r, _pth_utf)
            _inclusion_level_t = max(_inclusion_level_t_u, _inclusion_level_t)
            _file_o_memb.close()

        inclusion_level_calc = max(inclusion_level_calc, _inclusion_level_t)

        return inclusion_level_calc

    def get_current_inclusion_depth(self, file_r):
        """
        Get inclusion level calculated from database
        :param file_r: file record from model, not None
        :return int: current inclusion level (may be None)
        """
        file_r.refresh_from_db()
        return file_r.depth_level

    def _update_current_inclusion_depth(self, file_r, inclusion_level):
        """
        Update inclusion level calculated in DB.
        :param file_r: file record from model, not None
        :param int inclusion_level: inclusion level to update, not None
        :return: modified file_r with new inclusion level set
        """
        file_r.refresh_from_db()
        file_r.depth_level = max(file_r.depth_level, inclusion_level)
        file_r.save()
        return file_r

    def register_file_obj(self, file_o, ci_type, loc_path=None, loc_type=None, loc_revision=None, inclusion_level=0, ci_type_sub=None, force_recalc=False):
        """
        Registers file or file-like object in the database. MD5 checksum and MIME-type of the file object will be calculated. 
        No duplicate locations and checksums will be stored.
        all possible checksums of '.sql' objects will be stored
        :param file_o: python file-like object, have to be opened already in BINARY mode.
        :param str ci_type:  ci_type code of file_object itself. Will be determined by regular expressions in database if not given.
        :param str loc_path: full path to file location. May be None or empty. This case 'ci_type' have to be specified.
        :param str loc_type: location_type code. Have to be neither None, noor empty.
        :param loc_revision: string or integer, location_revision (if applicable). May be None
        :param int inclusion_level: integer or None: try to register includes inside 'tar' or 'zip' archive at inclusion level specified in this parameter. 
        :param str ci_type_sub: ci_type of archive content files. Will be ignored if inclusion_level is zero. Will be set to 'FILE' if not given.
        :param bool force_recalc: if True then all included archives contents is to be re-calculated even if it is found to be registered already
        :return: file record from model, or None on failure
        """
        (_fl_r, _inclusion_level_calc) = self._register_file_obj(file_o, ci_type, loc_path,
                loc_type, loc_revision, inclusion_level, ci_type_sub, force_recalc, 0)
        return _fl_r

    def _register_file_obj(self, file_o, ci_type, loc_path, loc_type, loc_revision, inclusion_level, ci_type_sub, force_recalc, inclusion_level_calc):
        """
        Registers file or file-like object in the database. MD5 checksum and MIME-type of the file object will be calculated. 
        No duplicate locations and checksums will be stored.
        all possible checksums of '.sql' objects will be stored
        :param file_o: python file-like object, have to be opened already in BINARY mode.
        :param str ci_type: ci_type code of file_object itself. Will be determined by regular expressions in database if not given.
        :param str loc_path: full path to file location. May be None or empty. This case 'ci_type' have to be specified.
        :param str loc_type: location_type code. Have to be neither None, noor empty.
        :param loc_revision: int or str, location_revision if applicable. May be None
        :param int inclusion_level: try to register includes inside 'tar' or 'zip' archive at inclusion level specified by this parameter. 
        :param str ci_type_sub: ci_type of archive content files. Will be ignored if 'b_includes' is False. Will be set to FILE if not given.
        :param bool force_recalc: if True then all included archives contents is to be re-calculated even if it is found to be registered already
        :param int inclusion_level_calc:  current inclusion level, not None
        :return: Tuple (ci_file record from model or None on failure, inclusion level calculated as integer, None on error)
        """
        logging.debug('Path: [%s], LocType: [%s], Rev: [%s], CiType: [%s], Incl: [%s], InclCalc: [%s]' % 
                (loc_path, loc_type, str(loc_revision), ci_type, str(inclusion_level), str(inclusion_level_calc)))

        if not isinstance(inclusion_level_calc, int) or (inclusion_level_calc < 0):
            raise ValueError("Non-supported current inclusion level specified: %s" % str(inclusion_level_calc))

        _normalizer = normalizer.PLSQLNormalizer()
        _file_r_m = None

        _pos = file_o.tell()
        file_o.seek(0, 0)
        _inclusion_level_calc_src = inclusion_level_calc

        if not _normalizer.is_sql(file_o.read(self.__sql_limit)):
            # calculate file checksum
            _md5sum = self.md5(file_o)
            # register MD5 sum as "Regular" for non-sql files
            _file_r_m = self.register_file_md5(_md5sum, ci_type, 
                    self.mime(file_o), loc_path, loc_type, loc_revision, cs_prov="Regular")
            _inclusion_level_tmp = self.get_current_inclusion_depth(_file_r_m)
            _registered = (not force_recalc)\
                and (_inclusion_level_tmp is not None) \
                and (inclusion_level is not None) \
                and (_inclusion_level_tmp >= inclusion_level)

            if not _registered:
                inclusion_level_calc = self._register_includes(
                    file_o, _file_r_m, ci_type_sub, inclusion_level, force_recalc, inclusion_level_calc)
        else:
            try:
                _file_r_m = self._register_sql(file_o, ci_type, loc_path, loc_type, loc_revision)
                # here includes are impossible, so do nothing
            except:
                # unable to wrap-unwrap, register as 'flat' file
                _md5sum = self.md5(file_o)
                _file_r_m = self.register_file_md5(_md5sum, ci_type, 
                    self.mime(file_o), loc_path, loc_type, loc_revision, cs_prov="Regular")

        file_o.seek(_pos, os.SEEK_SET)

        self._update_current_inclusion_depth(_file_r_m, inclusion_level_calc - _inclusion_level_calc_src)

        return (_file_r_m, inclusion_level_calc)

    def register_file_md5(self, md5sum, ci_type, mime_type, loc_path=None, loc_type=None, loc_revision=None, cs_prov="Regular"):
        """
        Registers file or file-like object in the database. MD5 checksum and MIME-type have to be obtained somehow outside.
        No duplicate locations and checksums will be stored.
        Does not register files with not 'strict' cs_prov.
        :param str md5sum: MD5 checksum, not None and not empty.
        :param str mime_type: mime-type of file to register, not None and not empty.
        :param str ci_type: ci_type code. Will be determined by regular expressions in database if not given.
        :param str loc_path: path to file location. May be Non or empty. This case 'ci_type' have to be specified.
        :param str loc_type: location_type code. Have to be neither None, noor empty.
        :param loc_revision: str or int, location_revision if applicable. May be None.
        :param str cs_prov: checksums provider, used for specify "Wrapped", "Unwrapped" and so on...
        :return: file record  (from model) or None on failure
        """
        # check if 'cs_prov' is of 'strict' appropriation.
        # do nothing if not since whole file shall be registered otherwise.
        if not self._is_strict_cs_prov(cs_prov):
            return None

        # check arguments is not needed since they are checked in sub-methods
        # one exception: location and location type have to be set in pair
        if loc_path and not loc_type:
            raise ValueError("loc_path is specified but loc_type missing")

        if not ci_type:
            ci_type = self.ci_type_by_path(loc_path, loc_type)

        _ci_type_r = models.CiTypes.objects.filter(code=ci_type).last()
        _fl_r = None

        try:
            with transaction.atomic():
                _fl_r = models.Files(ci_type=_ci_type_r, mime_type=mime_type)
                _fl_r.save()
                self.add_checksum(_fl_r, md5sum)  # add checksum
        except IntegrityError:
            _fl_r = self.get_file_by_checksum(md5sum, cs_prov=cs_prov)

            if (_fl_r is None):  # no such file, crime
                raise

            self.add_checksum(_fl_r, md5sum, cs_prov=cs_prov)

        # here we've got a checksum and file object, so the location question is opened only
        # call 'add_location_checksum' since it checks for duplicates in contraverse to simple 'add_location'
        if loc_path:
            # if path and is given then add the location for this file
            self.add_location(_fl_r, loc_path,loc_type, revision=loc_revision)

        return _fl_r

    def get_file_by_file_obj(self, fl_o):
        """
        Get file object from model by python file-like object.
        :param fl_o: file-like object
        :return: file record from model, or None if not found
        """
        if not fl_o:
            return None

        _normalizer = normalizer.PLSQLNormalizer()
        _fl_r_m = None
        _pos = fl_o.tell()
        fl_o.seek(0, os.SEEK_SET)

        if not _normalizer.is_sql(fl_o.read(self.__sql_limit)):
            _fl_r_m = self.get_file_by_checksum(self.md5(fl_o))
        else:
            _fl_r_m = self.get_file_by_checksums_dict(
                self.get_all_sql_checksums(fl_o))

            if _fl_r_m is not None:
                _tempfile, _fl_r_m, _isstrict = _fl_r_m

        fl_o.seek(_pos, os.SEEK_SET)

        return _fl_r_m

    def add_inclusion_file_obj(self, fl_o_child, fl_o_parent, path):
        """
        Adds record in inclusions table (FILE_INCS): file 'fl_o_child' is included into 'fl_o_parent':
        :param fl_o_child: python file-like object of a "child" - file included into "file_o_parent". Have to be opened outside before calling this routine.
        :param fl_o_parent: python file-like object of a "parent" - file which "fl_o_child" is included into. Have to be opened outside before calling this routine.
        :param str path: required, not None, not empty: path of 'fl_o_child' in the archive 'fl_o_parent'
        :return: integer, how many inclusions of such a type are, should always be 1. Zero (0) is returned if one of files was not registered in the database before.
        """

        return self.add_inclusion(self.get_file_by_file_obj(fl_o_child), self.get_file_by_file_obj(fl_o_parent), path)

    # BEG: PL/SQL processing section
    """
    List of normalization suffixes and cs_providers.
    Key - uppercase letter or empty line, value - normalization flag
    """
    __normalization_suffixes = {
        "U": normalizer.PLSQLNormalizationFlags.uppercase,
        "S": normalizer.PLSQLNormalizationFlags.no_spaces,
        "C": normalizer.PLSQLNormalizationFlags.no_comments
    }

    """
    List of possible variants of normalization.
    All variants with space removings ( "S" flag ) are temporary disabled since of performance issues
    """
    #m_ls_norm_variant = [ "", "U", "C", "UC", "CS", "UCS" ];
    #m_ls_norm_variant = [ "", "U", "C", "UC" ];
    __normalization_variant = [""]

    def _norm_flags_by_suffixes(self, suffix):
        """
        Returns list of normalization flags depending on suffix given.
        :param self: self class object reference.
        :param str suffix: suffix (uppercase letters only)
        :return: list of flags, possible empty
        """
        if not suffix:
            return list()

        _result = list(filter(lambda x: x in self.__normalization_suffixes, suffix))
        _result = list(map(lambda x: self.__normalization_suffixes.get(x), _result))
        return _result

    # BEG: functions to process steps mentioned in __cs_providers
    def _sql_norm(self, fl_o, step):
        """
        Returns a dictionary with temporary objects of all-variant-normalization.
        :param fl_o: NamedTemporaryFile object
        :param str step: prefix of the step name to be appended to cs_prov name as prefix
        :return: dictionary where keys are sql normalization checksums providers (cs_provs, all starts from 'prefix') and values are temporary objects.
        """
        if not step:
            step = ""

        _result = dict()
        _normalizer = normalizer.PLSQLNormalizer()
        _pos = fl_o.tell()

        for _suffix in self.__normalization_variant:
            try:
                fl_o.seek(0, os.SEEK_SET)
                _result[step + _suffix] = tempfile.NamedTemporaryFile(suffix='.sql')
                _normalizer.normalize(fl_o, flags=self._norm_flags_by_suffixes(_suffix), 
                        write_to=_result[step + _suffix])
                _result[step + _suffix].seek(0, os.SEEK_SET)

            except Exception as _e:
                logging.exception(_e)
                _result = dict()
                pass

        fl_o.seek(_pos, os.SEEK_SET)

        return _result

    def _sql_wrap(self, fl_o, step):
        """
        Returns a dictionary with temporary object with wrapped content fl_o
        :param fl_o: NamedTemporaryFile object
        :param str tep: prefix of the step name to be appended to cs_prov name as prefix
        :return: dictionary where keys are sql wrap checksums providers (cs_prvs, all starts from 'prefix') and values are temporary objects.
        """

        if not step:
            step = ""

        _result = dict()

        try:
            _wrapper = wrapper.PLSQLWrapper()
            _result[step] = tempfile.NamedTemporaryFile(suffix=".plb")
            _wrapper.wrap_buf(fl_o, write_to=_result[step])
            _result[step].seek(0, os.SEEK_SET)

        except Exception as _e:
            logging.exception(_e)
            _result = dict()
            pass

        return _result

    def _sql_unwrap(self, fl_o, step):
        """
        Returns a dictionary with temporary object with wrapped content of obj_temp_file
        :param fl_o: NamedTemporaryFile object
        :param str step: prefix of the step name to be appended to cs_prov name as prefix
        :return: dictionary where keys are sql wrap checksums providers (cs_prvs, all starts from 'str_prefix') and values are temporary objects.
        """

        if not step:
            step = ""

        _result = dict()

        try:
            _wrapper = wrapper.PLSQLWrapper()
            _result[step] = tempfile.NamedTemporaryFile(suffix=".sql")
            _wrapper.unwrap_buf(fl_o, write_to=_result[step])

        except Exception as _e:
            logging.exception(_e)
            _result = dict()
            pass

        return _result

    def _is_wrapped(self, fl_o):
        """
        Checks fl_o has wrapped content.
        :param fl_o: NamedTemporaryFile object to check
        """
        _pos = fl_o.tell()
        fl_o.seek(0, os.SEEK_SET)
        _normalizer = normalizer.PLSQLNormalizer()
        _result = _normalizer.is_wrapped(fl_o)
        fl_o.seek(_pos, os.SEEK_SET)
        return _result

    # END: functions to process steps mentioned in __cs_providers

    def _perform_step(self, fl_o, step, is_first=True):
        """
        Performs a step which parms are given in the dict
        :param fl_o: file-like object to perform step upon
        :param str step: step name (cs_prov prefix)
        :param bool is_first: is it the first step
        :return: dictionary of step result where keys are step names (===cs_provs) and values are temporary file objects with step results
        """

        if step not in list(self.__cs_providers.keys()):
            raise ValueError("%s not found in providers list" % step)

        _result = dict()

        if "func" not in self.__cs_providers[step]:
            # do not unite above and below conditions into single one, because it will go to 'else' branch if we do so
            # but this case it will be a crime and unwanted exceptions
            if is_first:
                _result[step] = fl_o

        else:
            _func = getattr(self, self.__cs_providers[step]["func"])
            _result = _func(fl_o, step)

            if step not in _result:
                logging.warning("Step %s failed" % step)
                return dict()

        # additional checks
        if "check" in self.__cs_providers[step]:
            _func = getattr(self, self.__cs_providers[step]["check"])

            if not _func(_result[step]):
                logging.warning("Check failed for step %s" % step)
                return dict()

        if "next" in self.__cs_providers[step]:
            for _next_step in self.__cs_providers[step]["next"]:
                _result.update(self._perform_step(_result[step], _next_step, is_first=False))

        return _result

    def get_all_sql_checksums(self, fl_o):
        """
        Calculates all possible checksums for providers: 
        "Regular", "Normed" , "Wrapped", "Wrapped_Normed", "Unwrapped", "UnwrappedNormed".
        "Normed" may be provided with uppercase suffixes of normalization flags "U", "S", "C"
        "S" is disabled now because of performance issues
        Currently MD5 checksums are supported only.
        If file comes wrapped then "Regular" and "Normed" checksums are not calculated. 
        This case we shall try to find out what the file it is by other providers.
        In most cases "UnwrappedNormed" checksum will match.
        No additional checks about PL/SQL syntax are done.
        :param fl_o: file or file-like python object
        :return: a dictionary where keys are cs_prov's and values are dictionaries of the appropriated checksums (keys - 'cs_type's and values are checksums itselves).
        """

        _result = dict()
        _pos = fl_o.tell()
        fl_o.seek(0, os.SEEK_SET)

        _step = "Regular"

        if self._is_wrapped(fl_o):
            _step = "Wrapped"

        _result = self._perform_step(fl_o, _step)
        _result_m = dict()

        for _key, _tmpf in _result.items():
            if not _tmpf:
                continue

            _result_m[_key] = {"MD5": self.md5(_tmpf)}

        fl_o.seek(_pos, os.SEEK_SET)

        return _result_m

    def _is_strict_cs_prov(self, cs_prov="Regular"):
        """
        Determines is the 'cs_prov' given considered as of 'strict' appropriation or not.
        :param self: self class object reference
        :param str cs_prov: string, cs_provider
        :return: boolean, if True than provider is considered as 'strict' appropriation, False otherwise.
        """

        _prov_conf = self.__cs_providers.get(cs_prov)

        if not _prov_conf:
            return False

        return _prov_conf.get("strict", True)

    """
    Dictionary of possible PL/SQL process steps
    "func" - function to obtain step result, if None - input file is assumed to be a result already,
        exception is "Wrapped" - wrapped file may be provided, so a result will not be produced this case
    "next" - list of next possible steps to process
    "search" - search order while finding the appropriate checksum from database by-file-object. Integer. Zero is the highest priority. Can not be omitted.
    NOTE #1: "Normed" steps produces all possible normalization 'cs_prov' variants, but only 'clean' (without additional flags) is provided to next step
    NOTE #2: Caution: no duplicated search orders allowed. Result is not defined if duplicates found in this field.
    """
    __cs_providers = {
        "Regular": {"next": ["Normed", "Wrapped"],
                    "search": 0},
        "Normed": {"func": "_sql_norm",
                   "next": ["Normed_Wrapped"],
                   "search": 1},
        "Wrapped": {"func": "_sql_wrap",
                    "next": ["Wrapped_Normed", "Unwrapped"],
                    "check": "_is_wrapped",
                    "search": 2},
        "Wrapped_Normed": {"func": "_sql_norm",
                           "search": 3},
        "Normed_Wrapped": {"check": "_is_wrapped",
                           "func": "_sql_wrap",
                           "next": ["Normed_Wrapped_Normed"],
                           "search": 4},
        "Unwrapped": {"func": "_sql_unwrap",
                      "next": ["Unwrapped_Normed"],
                      "search": 5},
        "Normed_Wrapped_Normed": {"func": "_sql_norm",
                                  "search": 6},
        "Normed_Wrapped_Unwrapped": {"func": "_sql_unwrap",
                                     "next": ["Normed_Wrapped_Unwrapped_Normed"],
                                     "search": 7},
        "Unwrapped_Normed": {"func": "_sql_norm",
                             "search": 8},
        "Normed_Wrapped_Unwrapped_Normed": {"func": "_sql_norm",
                                            "search": 9},
        "FullNormed":   {"search": 10, "strict": False}
    }
    # END: PL/SQL processing section

    # BEG: LOCATIONS:IS_DELETED methods support
    def delete_location_cascade(self, loc_r, reason=None):
        """
        Delete location object given and all location objects with the same attributes but 'file'.
        Name was not changed due to historical reason
        :param loc_r: location record from Model
        :param str reason: reason of deletion
        """
        if not loc_r:
            return  # nothing to 'delete'

        loc_r._change_reason = reason
        loc_r.delete()

        return

    def delete_location(self, loc_path, loc_type, date_s=None, revision=None, reason=None):
        """
        Drop location objects before or at 'date_s'.
        All records made after 'date_s' will be leaved unchange.
        :param str loc_path: location path, not None.
        :param str loc_type: location type code, not None.
        :param revision: str or int, revision of a location given, may be None or empty.
        :param DateTime date_s: Date when location is to be marked 'deleted'. 
                All previous records for this location will be marked 'deleted' also.
                Current date-time will be used if this argument omitted.
        :param str reason: reason of deletion
        """
        # check arguments. These two lines will raise an exception if None given
        # this is exactly we need since path and type may not be empty.

        loc_path = loc_path.strip()
        loc_type = loc_type.strip()

        if not loc_path:
            raise ValueError("Location path is required.")

        if not loc_type:
            raise ValueError("Location type is requred.")

        loc_type = loc_type.strip().upper()

        if isinstance(revision, int):
            revision = "%d" % revision

        if not revision:
            if loc_type == "SVN":
                raise ValueError("Revision required for SVN location")

            revision = None

        if not date_s:
            date_s = timezone.now()

        # query to location table:
        for _loc in models.Locations.objects.filter(
                loc_type__code=loc_type,
                path=loc_path,
                input_date__lte=date_s,
                revision=revision,
                file_dst=None).all():
            self.delete_location_cascade(_loc, reason=reason)

    def is_location_deleted(self, loc_path, loc_type, date_s=None, revision=None):
        """
        Checks if a location given is marked as 'deleted'.
        :param str loc_path: location path, not None.
        :param str loc_type: location type code, not None.
        :param revision: str or int, revision of a location given, may be None or empty.
        :param DateTime date_s: Date when location is to be marked 'deleted'. 
                All previous records for this location will be marked 'deleted' also.
                Current date-time will be used if this argument omitted.
        :return bool: True if deleted, False otherwise.
            True is returned if no such location was registered before.
        """

        return self.get_file_by_location(loc_path, loc_type, date_s=date_s, revision=revision, history=False) is None
    # END: LOCATIONS:IS_DELETED methods support

    ###BEG: CI_TYPE_GROUP
    def add_ci_type_inclusion(self, ci_group, ci_type):
        """
        Checks if 'ci_type' is included to 'ci_group'
        Adds if not.
        :param str ci_group: CI types group code, not None
        :param str ci_type: CI type code, not None
        :return int: amount of inclusions found, should be 1 if everything is OK
        """
        _type = models.CiTypes.objects.filter(code=ci_type).last()

        if not _type:
            return 0

        _group = models.CiTypeGroups.objects.filter(code=ci_group).last()

        if not _group:
            return 0

        _amnt = models.CiTypeIncs.objects.filter(ci_type_group=_group, ci_type=_type).count()

        if _amnt > 0:
            return _amnt

        models.CiTypeIncs(ci_type_group=_group, ci_type=_type).save()

        return models.CiTypeIncs.objects.filter(ci_type_group=_group, ci_type=_type).count()

    def get_rn_gav(self, ci_type, version):
        """
        Returns GAV of ci_type release notes artifact.
        :param str ci_type: CI type code, not None
        :return str: GAV of release notes artifact, or None if not found.
        """
        ci_type = ci_type.strip().upper()

        if not ci_type:
            raise ValueError("CI_TYPE is mandatory")

        if not version:
            raise ValueError("Version is mandatory")

        _citype = models.CiTypes.objects.get(code=ci_type)
        _rn_gavs = list(map(lambda x: x.ci_type_group.get_rn_gav(version), _citype.citypeincs_set.all()))
        _rn_gavs = list(filter(lambda x: x, _rn_gavs))

        if not _rn_gavs:
            return None

        return _rn_gavs.pop(0)

    def get_ci_group_regexp(self, ci_group, loc_type=None):
        """
        Get list of regular expressions for a CI Types Group with code 'ci_group'.
        :param self: self class object reference
        :param str ci_group: CI type group code, not None
        :param str loc_type: location type, if None - return for all location types
        :return: list of strings with regular expressions for all CI Types included into CI Group with code 'ci_group'. List may be empty if nothing found.
        """
        _result = list()

        for _ci_type in list(map(lambda x: x.ci_type, 
                models.CiTypeIncs.objects.filter(ci_type_group__code=ci_group).all())):

            for _regexp in models.CiRegExp.objects.filter(ci_type=_ci_type).all():
                if not _regexp.regexp:
                    continue

                if _regexp.regexp in _result:
                    continue

                if not loc_type or (loc_type == _regexp.loc_type.code):
                    _result.append(_regexp.regexp)

        return _result

    ###END: CI_TYPE_GROUP
    def get_ci_type_dms_id(self, ci_type):
        """
        Get DMS id of ci_type by its code.
        :param str ci_type: ci_type code, not None
        :return str: dms_id, or None if not specified yet
        """
        if not ci_type:
            raise ValueError("CI TYPE is not specified")

        _prm = models.CiTypeDms.objects.filter(ci_type__code=ci_type.upper())

        if (_prm.count() == 0):
            return None

        return _prm.last().dms_id

    def add_ci_type_dms_id(self, ci_type, dms_id):
        """
        Add DMS id of ci_type to the database.
        :param str ci_type: ci_type code
        :param str dms_id: DMS ID, not None
        """
        if not ci_type:
            raise ValueError("CI TYPE is not specified")

        ci_type = ci_type.upper()

        if not dms_id:
            raise ValueError("DMS ID is not specified")

        _ci_type = models.CiTypes.objects.filter(code=ci_type).last()

        if _ci_type is None:
            raise ValueError("Non-existent ci_type: %s" % ci_type)

        # do not allow duplicates
        _prm = models.CiTypeDms.objects.filter(ci_type=_ci_type).last()

        if not _prm:
            _prm = models.CiTypeDms(ci_type=_ci_type)

        _prm.dms_id=dms_id
        _prm.save()

    def get_current_inclusion_depth_calc(self, file_r):
        """
        Return current inclusion level which was calculated for now. For using outside of self class.
        :param self: self reference
        :param file_r: file record from model
        :return int: calculated inclusion level, or None if object was not found in the database.
        """
        return self._get_current_inclusion_depth_calc(file_r, None)

    def _get_current_inclusion_depth_calc(self, file_r, inclusion_level_current):
        """
        Return current inclusion level which was calculated for now - for internal class usage.
        :param self: self reference
        :param file_r: file record from model
        :param int inclusion_level_current: current inclusion level investigation, should never be used outside of CheckSumsController.
        :return int: calculated inclusion level, or None if object was not found in the database.
        """
        if not file_r:
            return None

        # if there is at least one checksum - level is zero.
        _cs_cnt = models.CheckSums.objects.filter(file=file_r).count()

        if not _cs_cnt:
            return None

        if not isinstance(inclusion_level_current, int):
            inclusion_level_current = 0
        else:
            inclusion_level_current += 1

        _inclusion_level_max = None
        for _loc_inc in models.Locations.objects.filter(loc_type__code="ARCH", file_dst=file_r, revision=None):
            _inclusion_level_sub = self._get_current_inclusion_depth_calc(_loc_inc.file, inclusion_level_current)

            if _inclusion_level_sub is None:
                # do not use 'not _inclusion_level_sub' since it may be zero which is falsy
                continue

            if _inclusion_level_max is None:
                # do not use 'not _inclusion_level_sub' since it may be zero which is falsy
                _inclusion_level_max = _inclusion_level_sub

            _inclusion_level_max = max(_inclusion_level_max, _inclusion_level_sub)

        if _inclusion_level_max is not None:
            inclusion_level_current = max(inclusion_level_current, _inclusion_level_max)

        return inclusion_level_current
# END: MAIN TABLES
