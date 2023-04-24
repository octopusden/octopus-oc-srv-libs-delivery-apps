""" This command was used once to change some delivery parameters in batch and most probably is useless now. """


from django.core.management import base, call_command
from dlmanager.models import Delivery
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User
from django.db.models import Q, F, Min, Max, ExpressionWrapper, fields
import datetime


class Command(base.BaseCommand):
    help = 'Fix deliveries with shifted request_date. Use --dry_run to only show statistics'

    def add_arguments(self, parser):
        # Named (optional) arguments
        parser.add_argument(
            '--dry_run',
            action='store_true',
            dest='dry_run',
            default=False,
            help='Only show statistics',
        )

    def handle(self, *args, **kwargs):
        shifted = Delivery.objects.filter(
            creation_date__isnull=False, request_date__isnull=False, creation_date__gt=F("request_date"))

        date_from = shifted.aggregate(Min("creation_date"))[
            "creation_date__min"]
        date_to = shifted.aggregate(Max("creation_date"))["creation_date__max"]

        in_this_period = Delivery.objects.filter(
            creation_date__range=(date_from, date_to))
        in_this_period_notnull = in_this_period.filter(
            request_date__isnull=False, )

        print("shifts found: ", len(shifted.all()))
        print("total: ", len(Delivery.objects.all()))
        print("Shift period:", date_from, "...", date_to)
        print("In this period total:", len(in_this_period))
        print("In this period with request_date!=null:",
              len(in_this_period_notnull))

        if not kwargs.get("dry_run", False):
            in_this_period.update(request_date=F(
                "request_date")+datetime.timedelta(hours=3))
            print("Dates fixed")

        return
