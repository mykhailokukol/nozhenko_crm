from celery import shared_task
from django.utils.timezone import now

from base.models import ItemBooking


@shared_task
def archive_expired_bookings():
    today = now().date()
    expired_bookings = ItemBooking.objects.filter(end_date__lt=today, is_archived=False)
    
    for booking in expired_bookings:
        booking.is_archived = True
        booking.save()
        
        booking.items.update(is_booked=False)