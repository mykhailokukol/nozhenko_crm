document.addEventListener('DOMContentLoaded', function() {
    const requestTypeField = document.querySelector('#id_request_type');
    const newItemFields = document.querySelectorAll('[id^="id_new_item_"]');
    const existingItemField = document.querySelector('#id_existing_item');
    const countField = document.querySelector('#id_count');
    const isApprovedField = document.querySelector('#id_is_approved');

    function toggleFields() {
        const requestType = requestTypeField ? requestTypeField.value : null;

        // Hide all fields initially
        newItemFields.forEach(field => {
            if (field) {
                const formRow = field.closest('.form-row');
                if (formRow) formRow.style.display = 'none';
            }
        });
        if (existingItemField) {
            const formRow = existingItemField.closest('.form-row');
            if (formRow) formRow.style.display = 'none';
        }
        if (countField) {
            const formRow = countField.closest('.form-row');
            if (formRow) formRow.style.display = 'none';
        }
        if (isApprovedField) {
            const formRow = isApprovedField.closest('.form-row');
            if (formRow) formRow.style.display = 'none';
        }

        // Show appropriate fields based on request_type value
        if (requestType === 'new') {
            newItemFields.forEach(field => {
                if (field) {
                    const formRow = field.closest('.form-row');
                    if (formRow) formRow.style.display = '';
                }
            });
        } else if (requestType === 'existing') {
            if (existingItemField) {
                const formRow = existingItemField.closest('.form-row');
                if (formRow) formRow.style.display = '';
            }
        }

        // Always show count and is_approved fields
        if (countField) {
            const formRow = countField.closest('.form-row');
            if (formRow) formRow.style.display = '';
        }
        if (isApprovedField) {
            const formRow = isApprovedField.closest('.form-row');
            if (formRow) formRow.style.display = '';
        }
    }

    // Run on page load
    if (requestTypeField) {
        toggleFields();
        // Run every time request_type is changed
        requestTypeField.addEventListener('change', toggleFields);
    }
});