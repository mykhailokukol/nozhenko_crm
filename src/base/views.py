from django.http import JsonResponse

from base.models import Item


def get_item_booking(request):
    item_id = request.GET.get('item_id')
    if item_id:
        try:
            item = Item.objects.get(article=item_id)
            return JsonResponse({'stock': item.count})
        except Item.DoesNotExist:
            return JsonResponse({'error': 'Товар не найден'}, status=404)
    return JsonResponse({'error': 'Некорректный запрос'}, status=400)
