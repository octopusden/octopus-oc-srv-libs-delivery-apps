# -*- coding: utf-8 -*-
from django.db import migrations, models

# removing BS 'DELETED'
dict_bs_deleted = {"deleted": "Delivery has been deleted from storage"}


def ff(apps, schema_editor):
    """ forward function """
    BusinessStatus = apps.get_model("dlmanager", "BusinessStatus")
    Delivery = apps.get_model("dlmanager", "Delivery")
    DeliveryHistory = apps.get_model("dlmanager", "historicaldelivery")

    obj_bs = BusinessStatus.objects.filter(
        description=dict_bs_deleted["deleted"]).last()

    if (obj_bs is None):  # no such object - nothing to migrate
        return

    # first change business status to previous one
    for obj_dl_hist in DeliveryHistory.objects.filter(business_status=obj_bs).all():
        obj_orig = Delivery.objects.filter(id=obj_dl_hist.id).last()

        if obj_orig.business_status != obj_bs:
            continue  # OK, changed already

        # get latest non-deleted bs
        qs_bs_hist = DeliveryHistory.objects.filter(id=obj_dl_hist.id).exclude(
            business_status=obj_bs).order_by("-history_date")

        if qs_bs_hist.count() == 0:
            obj_orig.business_status = None

        else:
            obj_orig.business_status = qs_bs_hist.first().business_status

        obj_orig.save()

    # delete all records for 'deleted' status.
    # WARNING: never do it in previous loop since another one history record is created
    #          while updating original (parent) one in main table!
    for obj_dl_hist in DeliveryHistory.objects.filter(business_status=obj_bs).all():
        obj_dl_hist.delete()

    obj_bs.delete()

    return


def bw(apps, schema_editor):
    """ backward function """
    BusinessStatus = apps.get_model("dlmanager", "BusinessStatus")
    BusinessStatus.objects.get_or_create(
        description=dict_bs_deleted["deleted"])


class Migration(migrations.Migration):
    dependencies = [
        ('dlmanager', '0014_auto_20180221_0312'),
    ]

    operations = [
        migrations.RunPython(ff, bw)
    ]
