function formatDateToISO(dateString) {
    // Разделяем дату в формате DD.MM.YYYY
    const [day, month, year] = dateString.split('.');
    return `${year}-${month}-${day}`;
}

document.addEventListener('DOMContentLoaded', function () {
    const itemSelectElements = document.querySelectorAll('select[name$="-item"]');
    const startDateElement = document.querySelector('input[name="start_date"]');
    const endDateElement = document.querySelector('input[name="end_date"]');

    itemSelectElements.forEach(function (selectElement) {
        selectElement.addEventListener('change', function () {
            const itemId = this.value;
            const startDate = formatDateToISO(startDateElement.value);
            const endDate = formatDateToISO(endDateElement.value);

            if (itemId && startDate && endDate) {
                fetch(`/utils/check_item_booking/${itemId}/${startDate}/${endDate}/`)
                    .then(response => response.json())
                    .then(data => {
                        let messageElement = document.getElementById(`booking-message-${itemId}`);
                        if (!messageElement) {
                            messageElement = document.createElement('div');
                            messageElement.id = `booking-message-${itemId}`;
                            this.parentNode.appendChild(messageElement);
                        }

                        if (data.bookings.length > 0) {
                            let messages = data.bookings.map(
                                booking => `Товар забронирован с ${booking.start_date} по ${booking.end_date}`
                            ).join('<br>');
                            messageElement.innerHTML = `<div style="color: red;">${messages}</div>`;
                        } else {
                            messageElement.innerHTML = '';
                        }
                    });
            }
        });
    });
});