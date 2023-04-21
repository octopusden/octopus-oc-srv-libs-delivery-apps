""" Description of Django database models related to delivery infrastructure """


from __future__ import unicode_literals
import datetime
from configobj import ConfigObj
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from simple_history.models import HistoricalRecords
from oc_delivery_apps.dl_commons.dlmanager import DLModels


class UserAwareHistoricalRecords(HistoricalRecords):
    """ Extension of base simple_history HistoricalRecords which tries to set history_user based on delivery parameters """

    def get_history_user(self, instance):
        """ If default search fails on new delivery, set author as history_user """
        found_user = super(UserAwareHistoricalRecords,
                           self).get_history_user(instance)
        if not found_user and not instance.history.exists():
            try:
                found_user = User.objects.get(
                    username=instance.mf_delivery_author)
            except ObjectDoesNotExist:
                found_user = None
        return found_user

    class Meta:
        app_label = "dlmanager"


class Delivery(models.Model, DLModels.Delivery):
    """ Represents set of files prepared for send to client """
    # GAV components of delivery archive
    groupid = models.CharField(max_length=255, db_column="groupId")
    artifactid = models.CharField(max_length=127, db_column="artifactId")
    version = models.CharField(max_length=63)

    mf_delivery_files_specified = models.TextField(
        blank=True, null=True)  # delivery list in plain text

    # technical statuses
    flag_approved = models.BooleanField(default=False)
    flag_uploaded = models.BooleanField(default=False)
    flag_failed = models.BooleanField(default=False)

    # latest technical status change info
    request_date = models.DateTimeField(blank=True, null=True)
    request_by = models.CharField(blank=True, null=True, max_length=127)

    # SVN branches which is delivery based on
    mf_source_svn = models.CharField(blank=True, null=True, max_length=511)
    mf_tag_svn = models.CharField(blank=True, null=True, max_length=511)
    mf_delivery_revision = models.IntegerField(blank=True, null=True)

    # creation info
    mf_delivery_author = models.CharField(
        blank=True, null=True, max_length=127)
    mf_ci_build = models.IntegerField(blank=True, null=True)
    mf_ci_job = models.CharField(blank=True, null=True, max_length=63)
    mf_delivery_comment = models.TextField(blank=True, null=True)
    creation_date = models.DateTimeField(
        blank=True, null=True)  # creation timestamp

    build_status = models.CharField(
        blank=True, null=True, max_length=127)  # legacy - should be removed

    # history-related fields
    business_status = models.ForeignKey(
        "BusinessStatus", null=True, on_delete=models.CASCADE)
    comment = models.CharField(max_length=1000, blank=True)
    history = UserAwareHistoricalRecords()

    def __str__(self):
        return self.groupid + ':' + self.artifactid + ':' + self.version

    class Meta:
        managed = True
        app_label = "dlmanager"
        db_table = 'deliveries'
        unique_together = (('groupid', 'artifactid', 'version'),)
        ordering = ['-request_date']


class BusinessStatus(models.Model):
    """ Hardcoded list of possible business statuses """
    description = models.CharField(max_length=100, blank=False)
    history = HistoricalRecords()
    statuses_names = {
        "received": "Received by client",
        "deployed_test": "Deployed to client's test environment ",
        "deployed_prod": "Deployed to client's production environment ",
        "testing_ow": "Internal OW testing ",
        "testing_client": "Internal client testing ",
        "testing_uat": "UAT testing",
        "failed": "Failed",
        "rejected": "Rejected by client",
        "defected_ow": "Found defect by OW",
        "defected_client": "Found defect by client",
        "other": "Other"
    }

    def __str__(self):
        return self.description

    class Meta:
        app_label = "dlmanager"


class ClientLanguage(models.Model):
    """ Dictionary model for languages used for client documentation etc. """
    code = models.CharField(blank=False, null=False,
                            max_length=20, unique=True)
    description = models.CharField(
        blank=False, null=False, max_length=20, unique=True)

    class Meta:
        app_label = "dlmanager"


class Client(models.Model):
    """ List of clients retrieved from SVN. Obsolete clients are not removed but marked as inactive """
    code = models.CharField(blank=False, null=False, max_length=63)
    country = models.CharField(blank=False, null=False, max_length=63)
    is_active = models.BooleanField(blank=False, null=False, default=False)
    language = models.ForeignKey(
        ClientLanguage, null=True, on_delete=models.CASCADE)

    @property
    def is_reachable(self):
        """ Shortcut for check if delivery can be sent to client """
        # currently only FTP upload is implemented, so check FTP availability
        try:
            return self.ftpuploadclientoptions.can_receive
        except FtpUploadClientOptions.DoesNotExist:
            return True

    def __str__(self):
        return self.code

    class Meta:
        app_label = "dlmanager"


class ClientUser(models.Model):
    """ Many-to-many relation used to mark some users as client's representatives """
    userid = models.ForeignKey(
        User, db_column='userId', on_delete=models.CASCADE)
    clientid = models.ForeignKey(
        Client, db_column='clientId', on_delete=models.CASCADE)

    def __str__(self):
        return self.userid.username

    class Meta:
        app_label = "dlmanager"


class DeliveryHistory(models.Model):
    """ **Legacy class to be removed ** """
    deliveryid = models.ForeignKey(
        Delivery, db_column='deliveryId', on_delete=models.CASCADE)
    time = models.DateTimeField()
    change_by = models.TextField(blank=True, null=True)
    flag_approved = models.NullBooleanField()
    flag_uploaded = models.NullBooleanField()
    flag_failed = models.NullBooleanField()
    message = models.TextField(blank=True, null=True)

    class Meta:
        managed = True
        app_label = "dlmanager"
        db_table = 'delivery_history'


class ClientEmailAddress(models.Model):
    """ One-to-many table to store client's emails """
    clientid = models.ForeignKey(
        Client, db_column='clientId', on_delete=models.CASCADE)
    email_address = models.CharField(max_length=255)

    def __str__(self):
        return self.clientid.code + ' ' + self.email_address

    class Meta:
        app_label = "dlmanager"


class FtpUploadClientOptions(models.Model):
    """ Client settings used for dl_jobs.ftp_upload.
    ClientEmailAddress in future should be merged into this model """
    client = models.OneToOneField(Client, on_delete=models.CASCADE)
    # whether this client's deliveries can be processed and sent to him
    can_receive = models.BooleanField(default=True)
    # whether delivery for this client should be encrypted with his public keys
    should_encrypt = models.BooleanField(default=True)

    class Meta:
        app_label = "dlmanager"


class PrivateFile(models.Model):
    """ Defines file type which shouldn't be sent to client """
    regexp = models.CharField(max_length=1000)


class JiraInstances(models.Model):
    """
    The list of all JIRA instances and their urls respectively for both internal and external portals.
    """
    name = models.CharField(blank=True, null=True, max_length=255)
    code = models.CharField(blank=True, null=True, max_length=255)
    priority = models.IntegerField(default=0)
    api_url = models.CharField(blank=True, null=True, max_length=255)
    int_url_prefix = models.CharField(blank=True, null=True, max_length=255)
    ext_url_prefix = models.CharField(blank=True, null=True, max_length=255)

    class Meta:
        managed = True
        app_label = "dlmanager"


class JiraProjects(models.Model):
    """
    The list of all Jira projects
    """
    project_id = models.IntegerField(blank=True, null=True)
    code = models.CharField(blank=True, null=True, max_length=255)
    name = models.CharField(blank=True, null=True, max_length=255)
    instance_id = models.ForeignKey(
        JiraInstances, on_delete=models.CASCADE, blank=True, null=True)
    unique_together = ("project_id", "instance_id")

    class Meta:
        managed = True
        app_label = "dlmanager"
