/**
 * Stock Transfer Application JavaScript
 * Handles dynamic functionality for stock transfers
 */

document.addEventListener('DOMContentLoaded', function() {
    initializeStockTransferApp();
});

function initializeStockTransferApp() {
    // Initialize item search functionality
    initializeItemSearch();
    
    // Initialize form validation
    initializeFormValidation();
    
    // Initialize dynamic form fields
    initializeDynamicFields();
    
    // Initialize tooltips
    initializeTooltips();
    
    // Initialize confirmation dialogs
    initializeConfirmations();
}

/**
 * Initialize item search functionality
 */
function initializeItemSearch() {
    const itemSearchInputs = document.querySelectorAll('.item-search');
    
    itemSearchInputs.forEach(input => {
        let searchTimeout;
        
        input.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            const query = this.value.trim();
            
            if (query.length >= 2) {
                searchTimeout = setTimeout(() => {
                    searchItems(query, this);
                }, 300);
            } else {
                hideSearchResults(this);
            }
        });
        
        // Hide results when clicking outside
        document.addEventListener('click', function(e) {
            if (!input.contains(e.target)) {
                hideSearchResults(input);
            }
        });
    });
}

/**
 * Search items via AJAX
 */
function searchItems(query, inputElement) {
    const searchUrl = '/stock_transfer/ajax/search-items/';
    
    fetch(`${searchUrl}?q=${encodeURIComponent(query)}`)
        .then(response => response.json())
        .then(data => {
            if (data.results && data.results.length > 0) {
                showSearchResults(inputElement, data.results);
            } else {
                hideSearchResults(inputElement);
            }
        })
        .catch(error => {
            console.error('Error searching items:', error);
        });
}

/**
 * Show search results dropdown
 */
function showSearchResults(inputElement, results) {
    // Remove existing results
    hideSearchResults(inputElement);
    
    // Create results container
    const resultsContainer = document.createElement('div');
    resultsContainer.className = 'search-results';
    resultsContainer.style.cssText = `
        position: absolute;
        top: 100%;
        left: 0;
        right: 0;
        background: white;
        border: 1px solid #dee2e6;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 1000;
        max-height: 200px;
        overflow-y: auto;
    `;
    
    // Add results
    results.forEach(item => {
        const resultItem = document.createElement('div');
        resultItem.className = 'search-result-item';
        resultItem.style.cssText = `
            padding: 0.5rem 0.75rem;
            cursor: pointer;
            border-bottom: 1px solid #f8f9fa;
        `;
        resultItem.textContent = item.text;
        
        resultItem.addEventListener('click', function() {
            selectItem(inputElement, item);
        });
        
        resultItem.addEventListener('mouseenter', function() {
            this.style.backgroundColor = '#f8f9fa';
        });
        
        resultItem.addEventListener('mouseleave', function() {
            this.style.backgroundColor = 'white';
        });
        
        resultsContainer.appendChild(resultItem);
    });
    
    // Position and show results
    const inputRect = inputElement.getBoundingClientRect();
    resultsContainer.style.top = `${inputRect.height}px`;
    
    inputElement.parentNode.style.position = 'relative';
    inputElement.parentNode.appendChild(resultsContainer);
}

/**
 * Hide search results
 */
function hideSearchResults(inputElement) {
    const existingResults = inputElement.parentNode.querySelector('.search-results');
    if (existingResults) {
        existingResults.remove();
    }
}

/**
 * Select an item from search results
 */
function selectItem(inputElement, item) {
    // Set the input value
    inputElement.value = item.text;
    
    // Hide results
    hideSearchResults(inputElement);
    
    // Trigger item selection event
    const event = new CustomEvent('itemSelected', { detail: item });
    inputElement.dispatchEvent(event);
    
    // Get item details
    getItemDetails(item.id, inputElement);
}

/**
 * Get item details via AJAX
 */
function getItemDetails(itemId, inputElement) {
    const detailsUrl = '/stock_transfer/ajax/get-item-details/';
    const sourceFacilityId = document.getElementById('id_source_facility')?.value;
    
    fetch(detailsUrl, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify({
            item_id: itemId,
            source_facility_id: sourceFacilityId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            populateItemFields(inputElement, data.item);
        } else {
            console.error('Error getting item details:', data.error);
        }
    })
    .catch(error => {
        console.error('Error getting item details:', error);
    });
}

/**
 * Populate item fields with details
 */
function populateItemFields(inputElement, itemData) {
    // Find the form row containing this input
    const formRow = inputElement.closest('.form-row') || inputElement.closest('tr');
    
    if (formRow) {
        // Populate available quantity
        const availableQtyField = formRow.querySelector('[name*="available_quantity"]');
        if (availableQtyField) {
            availableQtyField.value = itemData.available_quantity || 0;
        }
        
        // Populate unit of measure
        const unitField = formRow.querySelector('[name*="unit_of_measure"]');
        if (unitField) {
            unitField.value = itemData.unit_of_measure || 'PCS';
        }
        
        // Populate unit cost
        const costField = formRow.querySelector('[name*="unit_cost"]');
        if (costField && itemData.unit_cost) {
            costField.value = itemData.unit_cost;
        }
        
        // Populate unit weight
        const weightField = formRow.querySelector('[name*="unit_weight"]');
        if (weightField && itemData.unit_weight) {
            weightField.value = itemData.unit_weight;
        }
        
        // Populate unit volume
        const volumeField = formRow.querySelector('[name*="unit_volume"]');
        if (volumeField && itemData.unit_volume) {
            volumeField.value = itemData.unit_volume;
        }
        
        // Calculate totals
        calculateItemTotals(formRow);
    }
}

/**
 * Initialize form validation
 */
function initializeFormValidation() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!validateForm(this)) {
                e.preventDefault();
                return false;
            }
        });
        
        // Real-time validation
        const inputs = form.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            input.addEventListener('blur', function() {
                validateField(this);
            });
            
            input.addEventListener('input', function() {
                clearFieldError(this);
            });
        });
    });
}

/**
 * Validate form
 */
function validateForm(form) {
    let isValid = true;
    const requiredFields = form.querySelectorAll('[required]');
    
    requiredFields.forEach(field => {
        if (!validateField(field)) {
            isValid = false;
        }
    });
    
    // Validate transfer items
    const itemRows = form.querySelectorAll('.item-row');
    if (itemRows.length > 0) {
        itemRows.forEach(row => {
            if (!validateItemRow(row)) {
                isValid = false;
            }
        });
    }
    
    return isValid;
}

/**
 * Validate individual field
 */
function validateField(field) {
    const value = field.value.trim();
    const isRequired = field.hasAttribute('required');
    
    clearFieldError(field);
    
    if (isRequired && !value) {
        showFieldError(field, 'This field is required.');
        return false;
    }
    
    // Validate quantity fields
    if (field.name && field.name.includes('quantity')) {
        const numValue = parseFloat(value);
        if (isNaN(numValue) || numValue <= 0) {
            showFieldError(field, 'Please enter a valid positive number.');
            return false;
        }
    }
    
    // Validate available quantity vs transfer quantity
    if (field.name && field.name.includes('quantity') && !field.name.includes('available')) {
        const row = field.closest('.form-row') || field.closest('tr');
        if (row) {
            const availableField = row.querySelector('[name*="available_quantity"]');
            const availableQty = parseFloat(availableField?.value || 0);
            const transferQty = parseFloat(value || 0);
            
            if (transferQty > availableQty) {
                showFieldError(field, `Transfer quantity cannot exceed available quantity (${availableQty}).`);
                return false;
            }
        }
    }
    
    return true;
}

/**
 * Validate item row
 */
function validateItemRow(row) {
    let isValid = true;
    const requiredFields = row.querySelectorAll('[required]');
    
    requiredFields.forEach(field => {
        if (!validateField(field)) {
            isValid = false;
        }
    });
    
    return isValid;
}

/**
 * Show field error
 */
function showFieldError(field, message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'invalid-feedback';
    errorDiv.textContent = message;
    errorDiv.style.display = 'block';
    
    field.classList.add('is-invalid');
    field.parentNode.appendChild(errorDiv);
}

/**
 * Clear field error
 */
function clearFieldError(field) {
    field.classList.remove('is-invalid');
    const errorDiv = field.parentNode.querySelector('.invalid-feedback');
    if (errorDiv) {
        errorDiv.remove();
    }
}

/**
 * Initialize dynamic form fields
 */
function initializeDynamicFields() {
    // Handle source facility change
    const sourceFacilitySelect = document.getElementById('id_source_facility');
    if (sourceFacilitySelect) {
        sourceFacilitySelect.addEventListener('change', function() {
            updateAvailableQuantities(this.value);
        });
    }
    
    // Handle quantity changes for total calculations
    document.addEventListener('input', function(e) {
        if (e.target.name && (e.target.name.includes('quantity') || e.target.name.includes('unit_cost'))) {
            const row = e.target.closest('.form-row') || e.target.closest('tr');
            if (row) {
                calculateItemTotals(row);
            }
        }
    });
}

/**
 * Update available quantities based on source facility
 */
function updateAvailableQuantities(facilityId) {
    const itemRows = document.querySelectorAll('.item-row');
    
    itemRows.forEach(row => {
        const itemSelect = row.querySelector('select[name*="item"]');
        if (itemSelect && itemSelect.value) {
            getItemDetails(itemSelect.value, itemSelect);
        }
    });
}

/**
 * Calculate item totals
 */
function calculateItemTotals(row) {
    const quantityField = row.querySelector('[name*="quantity"]:not([name*="available"])');
    const unitCostField = row.querySelector('[name*="unit_cost"]');
    const unitWeightField = row.querySelector('[name*="unit_weight"]');
    const unitVolumeField = row.querySelector('[name*="unit_volume"]');
    
    const quantity = parseFloat(quantityField?.value || 0);
    const unitCost = parseFloat(unitCostField?.value || 0);
    const unitWeight = parseFloat(unitWeightField?.value || 0);
    const unitVolume = parseFloat(unitVolumeField?.value || 0);
    
    // Calculate total value
    const totalValueField = row.querySelector('[name*="total_value"]');
    if (totalValueField) {
        totalValueField.value = (quantity * unitCost).toFixed(2);
    }
    
    // Calculate total weight
    const totalWeightField = row.querySelector('[name*="total_weight"]');
    if (totalWeightField) {
        totalWeightField.value = (quantity * unitWeight).toFixed(2);
    }
    
    // Calculate total volume
    const totalVolumeField = row.querySelector('[name*="total_volume"]');
    if (totalVolumeField) {
        totalVolumeField.value = (quantity * unitVolume).toFixed(2);
    }
}

/**
 * Initialize tooltips
 */
function initializeTooltips() {
    const tooltipElements = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    tooltipElements.forEach(element => {
        new bootstrap.Tooltip(element);
    });
}

/**
 * Initialize confirmation dialogs
 */
function initializeConfirmations() {
    const confirmButtons = document.querySelectorAll('[data-confirm]');
    
    confirmButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            const message = this.getAttribute('data-confirm');
            if (!confirm(message)) {
                e.preventDefault();
                return false;
            }
        });
    });
}

/**
 * Get CSRF token
 */
function getCSRFToken() {
    const tokenElement = document.querySelector('[name=csrfmiddlewaretoken]');
    return tokenElement ? tokenElement.value : '';
}

/**
 * Show notification
 */
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show`;
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // Add to page
    const container = document.querySelector('.stock-transfer-container') || document.body;
    container.insertBefore(notification, container.firstChild);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 5000);
}

/**
 * Format number with commas
 */
function formatNumber(number) {
    return new Intl.NumberFormat().format(number);
}

/**
 * Format currency
 */
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}

/**
 * Add loading state to element
 */
function setLoadingState(element, isLoading) {
    if (isLoading) {
        element.classList.add('loading');
        element.disabled = true;
    } else {
        element.classList.remove('loading');
        element.disabled = false;
    }
}

/**
 * Export functions for global use
 */
window.StockTransferApp = {
    showNotification,
    formatNumber,
    formatCurrency,
    setLoadingState,
    searchItems,
    getItemDetails
}; 