from random import randint

from django.db.models import F
from django.db import transaction
from django.dispatch import receiver
from django.db.models.signals import post_delete, post_save, pre_delete, pre_save

from base.models import (
    Item,
    ItemStock,
    ItemRefund,
    ItemBooking,
    ItemRecovery,
    ItemConsumption,
    ItemRefundItemM2M,
    ItemBookingItemM2M,
)


@receiver(pre_save, sender=Item)
def item_article(sender, instance, **kwargs):
    if not instance.pk:
        while True:
            random_number = f"{randint(0, 999999):06}"
            if not Item.objects.filter(article=random_number).exists():
                instance.article = random_number
                break


@receiver(post_save, sender=ItemStock)
def item_stock_approved(sender, instance, created, **kwargs):
    """
    Creates (or adds count to existing) Item instance if ItemStock instance is approved.
    Deletes ItemStock instance if it's approved.
    """
    if created:
        return
    if instance.request_type != "new":
        with transaction.atomic():
            item = instance.existing_item
            item.count += instance.count
            item.save()
            
            instance.is_archived = True
            post_save.disconnect(item_stock_approved, sender=ItemStock)
            instance.save()
            post_save.connect(item_stock_approved, sender=ItemStock)
        return
    
    if instance.is_approved:
        with transaction.atomic():
            item = Item(
                name=instance.new_item_name,
                description=instance.new_item_description,
                weight=instance.new_item_weight,
                height=instance.new_item_height,
                width=instance.new_item_width,
                length=instance.new_item_length,
                count=instance.count,
                project=instance.new_item_project,
                client=instance.new_item_client,
                storage=instance.new_item_storage,
                category=instance.new_item_category,
                arrival_date=instance.new_item_arrival_date,
                expiration_date=instance.new_item_expiration_date,
                status=instance.new_item_status,
            )
            item.save()
            for image in instance.images.all():
                image.item = item
                image.item_stock = None
                image.save()

            instance.is_archived = True
            post_save.disconnect(item_stock_approved, sender=ItemStock)
            instance.save()
            post_save.connect(item_stock_approved, sender=ItemStock)


@receiver(post_save, sender=ItemConsumption)
def item_consumption_approved(sender, instance, created, **kwargs):
    """
    Отнять кол-во товара в расходе от кол-ва товара на складе
    Например: Было 10 товаров на складе, подтвердили расход
        2 (двух), на складе стало 8 товаров
    """
    if created:
        return
    
    if instance.is_approved:
        with transaction.atomic():
            for booking in ItemBookingItemM2M.objects.filter(booking=instance.booking):
                item = booking.item
                if item.count - booking.item_count >= 0:
                    item.count -= booking.item_count
                    item.save()
            instance.is_archived = True
            post_save.disconnect(item_consumption_approved, sender=ItemConsumption)
            instance.save()
            post_save.connect(item_consumption_approved, sender=ItemConsumption)


@receiver(post_save, sender=ItemRefund)
def item_refund(sender, instance, created, **kwargs):
    if created:
        return
    
    if instance.is_approved:
        with transaction.atomic():
            refund_items = instance.item_refunds.all()
            for refund_item in refund_items:
                refund_item.item.count = F("count") + refund_item.item_count
                refund_item.item.save()
            instance.is_archived = True
            post_save.disconnect(item_refund, sender=ItemRefund)
            instance.save()
            post_save.connect(item_refund, sender=ItemRefund)


@receiver(post_save, sender=ItemRecovery)
def item_recovery(sender, instance, created, **kwargs):
    if created:
        return
    
    if instance.is_approved:
        with transaction.atomic():
            instance.item.count = F("count") - instance.count
            instance.item.save()
            instance.is_archived = True
            post_save.disconnect(item_recovery, sender=ItemRecovery)
            instance.save()
            post_save.connect(item_recovery, sender=ItemRecovery)


@receiver(post_save, sender=ItemBooking)
def item_booking(sender, instance, created, **kwargs):
    if created:
        return
    
    if instance.is_approved:
        for item in instance.items.all():
            item.is_booked = True
            item.save()


@receiver(pre_delete, sender=ItemBooking)
def item_unbooking(sender, instance, **kwargs):
    for item in instance.items.all():
        bookings_count = ItemBooking.objects.filter(
            items=item,
        ).count()
        if bookings_count > 1:
            continue
        else:
            item.is_booked = False
            item.save()