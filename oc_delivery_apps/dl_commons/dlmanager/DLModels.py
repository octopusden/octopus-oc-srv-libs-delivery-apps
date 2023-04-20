""" General entities used all around delivery infrastructure. """


import datetime
from configobj import ConfigObj
import re
import pytz
from oc_cdtapi import NexusAPI
from fs.path import normpath
from fs.errors import IllegalBackReference


class Delivery(object):
    """ Represents a set of files sent to client and saved under specific gav.
    Previously was used on its own but now all the work is done via dlmanager.models.Delivery subclass
    """
    client_name = property(lambda self: self.groupid.split('.')[-1])
    filelist = property(lambda self: self.delivery_list.filelist)
    svn_files= property(lambda self: self.delivery_list.svn_files) 
    mvn_files= property(lambda self: self.delivery_list.mvn_files)
    gav = property(lambda self: ":".join([self.groupid, self.artifactid, self.version, "zip"]))
    delivery_name = property(lambda self: self.artifactid+"-"+self.version)
    delivery_list=property(lambda self: DeliveryList(self.mf_delivery_files_specified))

    def __str__(self):
        return self.gav

    def __set_who(self, who=None):
        if who != None:
            self.request_by = who
        self.request_date = datetime.datetime.now(pytz.utc)
        self.comment=self.get_flags_description()
        self.save()

    def set_uploaded(self, value=True, who=None):
        """ Changes the value of flag_uploaded and saves instance """
        if self.flag_uploaded != value: 
            self.flag_uploaded = value
            self.__set_who(who)

    def set_approved(self, value=True, who=None):
        """ Changes the value of flag_approved and saves instance """
        if self.flag_approved != value: 
            self.flag_approved = value
            self.__set_who(who)

    def set_failed(self, value=True, who=None):
        """ Changes the value of flag_failed and saves instance """
        if self.flag_failed != value:
            self.flag_failed = value
            self.__set_who(who)

    def get_flags_description(self):
        """ Returns textual description of delivery's current technical status

        :returns: string describing combination of flag_... values
        """
        flags = (self.flag_approved, self.flag_uploaded, self.flag_failed)
        code = ("A" if flags[0] else "-") + ("U" if flags[1] else "-") + (
                "F" if flags[2] else "-")
        code_statuses = {
            "---": "New",
            "A--": "Approved, waiting for delivery",
            "AU-": "Delivered",
            "-U-": "Delivered",
            "--F": "Marked as bad (not delivered)",
            "A-F": "Marked as bad (not delivered)",
            "-UF": "Marked as bad after delivery",
            "AUF": "Marked as bad after delivery",
        }
        return code_statuses.get(code, "Invalid status")


    class Meta: # TODO: find out why this meta does not work in inheritance
        db_table = 'deliveries'	
        abstract = True	


class InvalidPathError(Exception):
    pass


class DeliveryList(object):
    """ Represents list of files included in delivery """
    svn_files= property(lambda self: list (filter(lambda name: not self._is_gav(name), self.filelist)) )
    mvn_files= property(lambda self: list (filter(self._is_gav, self.filelist)) )

    def __init__(self, list_raw):
        """ List given as an argument is parsed and checked

        :param list_raw: either ;- or newline-separated string or list of filenames 
        """
        if not list_raw:
            list_raw=[]
        if isinstance(list_raw, str):
            list_raw=self._split_merged_list(list_raw)
        elif isinstance(list_raw, list):
            list_raw = list ( filter (None, list_raw) )
        else:
            raise ValueError("Delivery list can be created from single string or list of strings only")

        # currently we support only svn files and maven artifacts
        mvn_files=filter(self._is_gav, list_raw)
        raw_svn_files=filter(lambda name: not self._is_gav(name), list_raw)
        svn_files=map(self._preprocess_svn_path, raw_svn_files) 
        self.filelist=list (svn_files) + list (mvn_files)

    def _split_merged_list(self, merged):
        return list ( filter(None, [element.strip() for element in
                             merged.replace(';','\n').splitlines()]) )

    def _is_gav(self, name):
        try:
            NexusAPI.parse_gav(name)
            return True
        except ValueError: # raised by gav parser
            return False

    def _preprocess_svn_path(self, raw_path):
        """ Forces forward slashes and resolves relative path characters """
        raw_path=raw_path.replace("\\", "/").strip("/")
        try:
            path=normpath(raw_path)
        except IllegalBackReference:
            raise InvalidPathError("Cannot reach specified path: '%s'" % raw_path)
        if path in ["", ".", "/"]:
            raise InvalidPathError("Cannot include full SVN branch: '%s'" % raw_path)
        return path
