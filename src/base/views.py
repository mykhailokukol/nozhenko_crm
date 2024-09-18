from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from base.models import Item, ItemBooking


def get_item_booking(request):
    item_id = request.GET.get('item_id')
    if item_id:
        try:
            item = Item.objects.get(article=item_id)
            return JsonResponse({'stock': item.count})
        except Item.DoesNotExist:
            return JsonResponse({'error': 'Товар не найден'}, status=404)
    return JsonResponse({'error': 'Некорректный запрос'}, status=400)


def check_item_booking(request, item_id, start_date, end_date):
    item = get_object_or_404(Item, article=item_id)
    active_bookings = ItemBooking.objects.filter(
        items=item, 
        is_approved=True, 
        end_date__gte=start_date, 
        start_date__lte=end_date
    )

    bookings_data = []
    if active_bookings.exists():
        for booking in active_bookings:
            bookings_data.append({
                "start_date": booking.start_date,
                "end_date": booking.end_date,
            })

    return JsonResponse({"bookings": bookings_data})
