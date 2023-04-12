# django models for checksum storing

from django.db import models
from simple_history.models import HistoricalRecords
import os

# DICTIONARY TABLES: BEG

# CI_TYPES: types of CI content
class CiTypes(models.Model):
    # ID is not needed, added automatically as primary key
    # capital letters code
    code = models.CharField(max_length=32, blank=False, null=False, unique=True)
    # display name
    name = models.CharField(max_length=64, blank=False, null=False, unique=True)
    # is_standard, default - no
    is_standard = models.CharField(max_length=8, blank=False, null=False, default="N")
    # is deliverable to customers
    is_deliverable = models.BooleanField(default=False)
    rn_artifactid = models.CharField(max_length=255, blank=True, null=True)
    # artifactid needed for documentation appending
    doc_artifactid = models.CharField(max_length=255, blank=True, null=True)

    def get_rn_gav(self, version):
        """
        Returns GAV of release notes of given version if artifactid is known, None otherwise
        """
        
        if any([not self.rn_artifactid, not version]):
            return None

        _group_id = '.'.join([
            os.getenv("MVN_PREFIX") or "com.example",
            os.getenv("MVN_RN_SUFFIX") or "rn.sfx",
            "release_notes"])

        return ":".join([_group_id, self.rn_artifactid, version, "txt"])

    def get_doc_gav(self, version):
        """
        Returns GAV (without packaging) of documentation for given version if artifactid is known, None otherwise
        """
        
        if any([not self.doc_artifactid, not version]):
            return None

        _group_id = '.'.join([
            os.getenv("MVN_PREFIX") or "com.example",
            os.getenv("MVN_DOC_SUFFIX") or "doc.sfx",
            "documentation"])

        return ":".join([_group_id, self.doc_artifactid, version])

    def __str__(self):
        return "%s:(%s)" % (self.code, self.name)

    class Meta:
        app_label = "checksums"

# CI_TYPE_GROUPS: groups of types
class CiTypeGroups(models.Model):
    # ID is not needed, added by Django automatically as primary key
    # capital letters code
    code = models.CharField(max_length=32, blank=False, null=False, unique=True)
    # display name
    name = models.CharField(max_length=64, blank=False, null=False)
    # Release notes artifactid
    rn_artifactid = models.CharField(max_length=255, blank=True, null=True)
    # artifactid needed for documentation appending
    doc_artifactid = models.CharField(max_length=255, blank=True, null=True)

    def get_rn_gav(self, version):
        """
        Returns GAV of release notes of given version if artifactid is known, None otherwise
        """
        
        if any([not self.rn_artifactid, not version]):
            return None

        _group_id = '.'.join([
            os.getenv("MVN_PREFIX") or "com.example",
            os.getenv("MVN_RN_SUFFIX") or "rn.sfx",
            "release_notes"])

        return ":".join([_group_id, self.rn_artifactid, version, "txt"])

    def get_doc_gav(self, version):
        """
        Returns GAV (without packaging) of documentation for given version if artifactid is known, None otherwise
        """
        
        if any([not self.doc_artifactid, not version]):
            return None

        _group_id = '.'.join([
            os.getenv("MVN_PREFIX") or "com.example",
            os.getenv("MVN_DOC_SUFFIX") or "doc.sfx",
            "documentation"])

        return ":".join([_group_id, self.doc_artifactid, version])

    def __str__(self):
        return "%s:(%s)" % (self.code, self.name)

    class Meta:
        app_label = "checksums"

# CI_TYPE_INCS: inclusions types to groups
class CiTypeIncs(models.Model):
    # ID is not needed, added by Django automatically as primary key
    # group code
    ci_type_group = models.ForeignKey(CiTypeGroups, to_field='code', on_delete=models.CASCADE, blank=False, null=False)
    # type code
    ci_type = models.ForeignKey(CiTypes, to_field='code', on_delete=models.CASCADE, blank=False, null=False)

    def __str__(self):
        return "'%s'<=='%s'" % (self.ci_type_group.code, self.ci_type.code)

    class Meta:
        app_label = "checksums"

# CS_TYPES: types of control sums
class CsTypes(models.Model):
    # ID is not needed, added automatically as primary key
    # capital letters code
    code = models.CharField(max_length=32, blank=False, null=False, unique=True)
    # display name
    name = models.CharField(max_length=64, blank=False, null=False, unique=True)

    def __str__(self):
        return self.code

    class Meta:
        app_label = "checksums"

# LOC_TYPES: types of locations for files
class LocTypes(models.Model):
    # ID is not needed, added automatically as primary key
    # capital letters code
    code = models.CharField(max_length=32, blank=False, null=False, unique=True)
    # display name
    name = models.CharField(max_length=64, blank=False, null=False, unique=True)

    def __str__(self):
        return "%s:(%s)" % (self.code, self.name)

    class Meta:
        app_label = "checksums"

# CI_REGEXP: regular expressions for file search for different systems
class CiRegExp(models.Model):
    # ID is not needed, added automatically as primary key
    # loc_type - type for location, reference to 'code'
    loc_type = models.ForeignKey(LocTypes, to_field='code', blank=False, null=False, on_delete=models.CASCADE)
    # ci_type - type of file, reference to 'code'
    ci_type = models.ForeignKey(CiTypes, to_field='code', blank=False, null=False, on_delete=models.CASCADE)
    # the python-styled regexp itself
    regexp = models.CharField(max_length=4096, blank=False, null=False)

    def __str__(self):
        return self.regexp

    class Meta:
        app_label = "checksums"

# CI_TYPE_PARMS: additional CI_TYPE-s parameters
class CiTypeDms(models.Model):
    # ID is not needed, added automatically as primary key
    # ci_type - type for parameter, reference to 'code'
    ci_type = models.ForeignKey(CiTypes, to_field='code', on_delete=models.CASCADE, blank=False, null=False)
    # DMS ID value
    dms_id = models.CharField(max_length=256, blank=True, null=True)

    class Meta:
        app_label = "checksums"


# DICTIONARY TABLES: END

#########################

# MAIN TABLES: BEG

# FILES: file entities
class Files(models.Model):
    # ID is not needed, added automatically as primary key
    # MIME-type
    mime_type = models.CharField(max_length=512, blank=False)
    # CI Type - code from CiTypes
    ci_type = models.ForeignKey(CiTypes, to_field='code', blank=False, null=False, on_delete=models.CASCADE)
    # FILE_DUP - for SQL files, if one is a possbie duplicate of another
    file_dup = models.ForeignKey('self', blank=True, null=True, on_delete=models.CASCADE)
    # DEPTH_LEVEL - a depth level of archive calculation (if was performed)
    depth_level = models.PositiveIntegerField(blank=False, null=False, default=0)

    def __str__(self):
        return ":".join([str(self.id), self.mime_type, self.ci_type.code])

    class Meta:
        app_label = "checksums"


# CHECKSUMS: checksums of one or more file state, for strict correspondance
class CheckSums(models.Model):
    # ID is not needed, added automatically as primary key
    # FILE - ID from Files
    file = models.ForeignKey(Files, on_delete=models.CASCADE, blank=False, null=False)
    # CS_TYPE - type of checksum - from CS_TYPES
    cs_type = models.ForeignKey(CsTypes, to_field='code', on_delete=models.CASCADE, blank=False, null=False)
    # checksum, initially by MD5 alg
    checksum = models.CharField(max_length=64, blank=False, null=False)

    def __str__(self):
        return ':'.join([str(self.file.id), self.cs_type.code, self.checksum])

    class Meta:
        app_label = "checksums"
        # indexes to reduce serarch time
        unique_together = (("checksum", "cs_type"))

# CS_PROV: checksums providers
class CsProv(models.Model):
    # ID is not needced, added automatically as primary key
    # CS - ID from CheckSums table
    cs = models.ForeignKey(CheckSums, on_delete=models.CASCADE, blank=False, null=False)
    # CS_PROV - provider ( wrapped, unwrapped, regular, e.t.c.)
    cs_prov = models.CharField(max_length=64, blank=False, null=False)

    def __str__(self):
        return ":".join([self.cs.checksum, self.cs_prov])

    class Meta:
        app_label = "checksums"
        unique_together = (("cs", "cs_prov"))

# CHECKSUMS_NST: checksums for non-strict correspondance of SQL files
class CheckSumsNst(models.Model):
    # ID is not needed, added automatically as primary key
    # FILE - ID from Files
    file = models.ForeignKey(Files, on_delete=models.CASCADE, blank=False, null=False)
    # CS_TYPE - type of checksum - from CS_TYPES
    cs_type = models.ForeignKey(CsTypes, to_field='code', on_delete=models.CASCADE, blank=False, null=False)
    # checksum - calculated by MD5 alg initially.
    checksum = models.CharField(max_length=64, blank=False, null=False)

    def __str__(self):
        return ':'.join([str(self.file.id), self.cs_type.code, self.checksum])

    class Meta:
        app_label = "checksums"
        #indexes to reduce serarch time
        index_together = [["checksum", "cs_type"]]

# CS_PROV_NST: providers for non-strict correspondance of SQL files
class CsProvNst(models.Model):
    # ID is not needced, added automatically as primary key
    # CS - ID from CheckSums table
    cs = models.ForeignKey(CheckSumsNst, on_delete=models.CASCADE, blank=False, null=False)
    # CS_PROV - provider ( wrapped, unwrapped, regular, e.t.c.)
    cs_prov = models.CharField(max_length=64, blank=False, null=False)

    def __str__(self):
        return ":".join([self.cs.checksum, self.cs_prov])

    class Meta:
        app_label = "checksums"
        index_together = [["cs", "cs_prov"]]


# LOCATIONS: where the file could be found
class Locations(models.Model):
    # ID is not needed, added automatically as primary key
    # FILE - ID from Files
    file = models.ForeignKey(Files, on_delete=models.CASCADE, blank=False, null=False)
    # PATH - full path to the object
    path = models.CharField(max_length=4096, blank=False, null=False)
    # TYPE - from LocTypes dictionary
    loc_type = models.ForeignKey(LocTypes, to_field='code', on_delete=models.CASCADE)
    # INPUT_DATE - date when this record was added
    input_date = models.DateTimeField(auto_now_add=True)
    # REVISION
    revision = models.CharField(max_length=64, blank=True, null=True)
    # HISTORY
    history = HistoricalRecords()
    # FILE_ID_DST (archive file ID if loc_type is 'ARCH')
    file_dst = models.ForeignKey(
        Files, related_name='FileIdDst+', null=True, blank=True, on_delete=models.CASCADE)

    def __str__(self):
        return ":".join([
            str(self.file.id),
            self.loc_type.code,
            self.path if not self.file_dst else "%d[%s]" % (self.file_dst.id, self.path),
            str(self.input_date)])

    class Meta:
        app_label = "checksums"

# MAIN TABLES: END
