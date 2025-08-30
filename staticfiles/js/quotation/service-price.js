// Service Price Auto-population JavaScript

document.addEventListener('DOMContentLoaded', function() {
    initServicePricePopulation();
});

function initServicePricePopulation() {
    const itemsContainer = document.getElementById('items-container');
    if (!itemsContainer) return;
    
    // Add event listener for service selection changes
    itemsContainer.addEventListener('change', function(e) {
        if (e.target.name && e.target.name.includes('service')) {
            populateUnitPriceFromService(e.target);
        }
    });
    
    // Initialize for existing service selections
    const existingServiceFields = itemsContainer.querySelectorAll('select[name*="service"]');
    existingServiceFields.forEach(field => {
        if (field.value) {
            populateUnitPriceFromService(field);
        }
    });
}

function populateUnitPriceFromService(serviceField) {
    const serviceId = serviceField.value;
    if (!serviceId) return;
    
    // Get the unit price field in the same form
    const itemForm = serviceField.closest('.item-form');
    const unitPriceField = itemForm.querySelector('input[name*="unit_price"]');
    
    if (!unitPriceField) return;
    
    // Fetch service price from server
    fetch(`/service/${serviceId}/price/`)
        .then(response => response.json())
        .then(data => {
            if (data.success && data.sale_price) {
                unitPriceField.value = data.sale_price;
                // Trigger calculation if the function exists
                if (typeof calculateItemTotal === 'function') {
                    calculateItemTotal(unitPriceField);
                }
            }
        })
        .catch(error => {
            console.error('Error fetching service price:', error);
        });
} 