(function($) {
    console.log('jQuery version:', $.fn.jquery);  // Проверяем версию jQuery
    $(document).ready(function() {
        console.log('Document ready');
        $('#id_item').change(function() {
            console.log('Item selected');
            var itemId = $(this).val();
            if (itemId) {
                console.log('Item ID:', itemId);
                $.ajax({
                    url: '/utils/get_item_booking/',
                    data: {
                        'item_id': itemId
                    },
                    success: function(data) {
                        console.log('AJAX success', data);
                        $('#item-stock-info').remove();
                        $('#id_item').after('<p id="item-stock-info">Количество на складе: ' + data.stock + '</p>');
                    }
                });
            }
        });
    });
})(django.jQuery);