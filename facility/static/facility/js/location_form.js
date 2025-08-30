// Location Form JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Auto-select facility if provided in URL
    const facilitySelect = document.getElementById('id_facility');
    const urlParams = new URLSearchParams(window.location.search);
    const facilityId = urlParams.get('facility');
    
    if (facilitySelect && facilityId) {
        facilitySelect.value = facilityId;
    }

    // Form validation
    const form = document.getElementById('locationForm');
    if (form) {
        form.addEventListener('submit', function(e) {
            let isValid = true;
            const requiredFields = form.querySelectorAll('.required-field');
            
            requiredFields.forEach(function(label) {
                const fieldId = label.getAttribute('for');
                const field = document.getElementById(fieldId);
                if (field && !field.value.trim()) {
                    field.classList.add('is-invalid');
                    isValid = false;
                } else if (field) {
                    field.classList.remove('is-invalid');
                }
            });
            
            if (!isValid) {
                e.preventDefault();
                // Show first tab with errors
                const firstInvalidField = form.querySelector('.is-invalid');
                if (firstInvalidField) {
                    const tabId = firstInvalidField.closest('.tab-pane').id;
                    const tabButton = document.querySelector(`[data-bs-target="#${tabId}"]`);
                    if (tabButton) {
                        const tab = new bootstrap.Tab(tabButton);
                        tab.show();
                    }
                }
            }
        });
    }

    // Auto-calculate capacity from dimensions
    const lengthField = document.getElementById('id_length');
    const widthField = document.getElementById('id_width');
    const heightField = document.getElementById('id_height');
    const capacityField = document.getElementById('id_capacity');

    function calculateCapacity() {
        if (lengthField && widthField && heightField && capacityField) {
            const length = parseFloat(lengthField.value) || 0;
            const width = parseFloat(widthField.value) || 0;
            const height = parseFloat(heightField.value) || 0;
            
            if (length > 0 && width > 0 && height > 0) {
                const capacity = length * width * height;
                capacityField.value = capacity.toFixed(2);
            }
        }
    }

    [lengthField, widthField, heightField].forEach(function(field) {
        if (field) {
            field.addEventListener('input', calculateCapacity);
        }
    });

    // Auto-generate location code if empty
    const locationCodeField = document.getElementById('id_location_code');
    const locationNameField = document.getElementById('id_location_name');
    
    if (locationNameField && locationCodeField) {
        locationNameField.addEventListener('input', function() {
            if (!locationCodeField.value.trim()) {
                const name = this.value.trim();
                if (name) {
                    // Generate a simple code from the name
                    const code = name.replace(/[^A-Za-z0-9]/g, '').toUpperCase().substring(0, 8);
                    locationCodeField.value = code;
                }
            }
        });
    }
}); 