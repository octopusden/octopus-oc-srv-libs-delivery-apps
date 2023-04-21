""" This command was used once to initialize delivery history and most probably is useless now. """


from django.core.management import base, call_command
from dlmanager.models import Delivery, BusinessStatus
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User
from django.db.models import Q, F
from django.db import connection
from django.db.models.expressions import RawSQL
import os


class Command(base.BaseCommand):
    help = 'Recreates delivery history by flushing existing history and creating up to 2 entries per delivery (initial and current versions)'

    def handle(self, *args, **kwargs):
        self.setup_business_statuses()
        self.fix_author_names()

        # clean existing history and create one entry per delivery
        Delivery.history.all().delete()
        call_command('populate_history', auto=True,
                     stdout=self.stdout, stderr=self.stderr)

        self.create_initial_revisions()
        return

    def setup_business_statuses(self):
        for name, description in BusinessStatus.statuses_names.items():
            BusinessStatus.objects.get_or_create(description=description)
        self.stdout.write("Added required business statuses")
        return

    def fix_author_names(self):
        for author in Delivery.objects.filter(mf_delivery_author__contains="\n"):
            author.mf_delivery_author = author.mf_delivery_author.replace(
                "\n", "")
            author.save()
        self.stdout.write("Fixed author names")

    def create_initial_revisions(self):
        self.stdout.write("Updating revisions...")
        # mf_delivery_author and request_by are usernames, not foreign keys
        # so we prefetch ids to perform batch operations later
        ext_history = Delivery.history.annotate(
            id_req_by=RawSQL(
                "select id from auth_user where username=request_by", ()),
            id_cr_by=RawSQL(
                "select id from auth_user where username=mf_delivery_author", ()),
        )

        # following operations will modify history entries
        # so we need to keep list of originally created entries
        original_pks = [res[0] for res in Delivery.history.values_list("pk")]

        # save current state for modified if request_date is known
        modified = ext_history.filter(Q(flag_approved=True) | Q(flag_uploaded=True)
                                      | Q(flag_failed=True)).exclude(
            request_date__isnull=True)
        modified.update(history_date=F("request_date"), comment="Status changed",
                        history_user_id=F("id_req_by"))
        # save it as new entries
        # unfortunately cannot do it in batch
        for mod in modified:
            mod.pk = None
            mod.save()

        self.stdout.write("Saved current state of deliveries")

        self.stdout.write("Saving initial states...")
        # reset all original entries to initial state
        # ! SQLite fails on pk_in=original_pks because it's too long, so split it
        for pks_range in [original_pks[num:num+500]
                          for num in xrange(0, len(original_pks), 500)]:
            # skip creation_date=null - simple_history requires history date
            original = ext_history.filter(pk__in=pks_range)
            with_initial = original.exclude(creation_date__isnull=True)
            with_initial.update(history_date=F("creation_date"), flag_approved=False,
                                flag_uploaded=False, flag_failed=False,
                                comment="Delivery created",
                                history_user_id=F("id_cr_by"))
            # if no creation_date is given, delete this history entry
            no_initial = original.filter(creation_date__isnull=True)
            no_initial.delete()

        self.stdout.write("Done")
        return
