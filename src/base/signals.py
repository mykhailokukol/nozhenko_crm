from django.dispatch import receiver
from django.db.models.signals import post_delete, post_save

from base.models import ItemBooking


@receiver(post_save, sender=ItemBooking)
def book_item(sender, instance, **kwargs):
    if instance.is_approved:
        instance.item.count -= instance.count
        instance.item.is_booked = True
        instance.item.project = instance.project
        instance.item.save()


@receiver(post_delete, sender=ItemBooking)
def unbooking_item(sender, instance, **kwargs):
    instance.item.is_booked = False
    instance.item.project = None
    instance.item.save()