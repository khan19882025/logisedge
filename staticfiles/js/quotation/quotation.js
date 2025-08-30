// Quotation JavaScript

// Test VAT calculation function
function testVatCalculation() {
    console.log('Testing VAT calculation...');
    
    // Test basic calculation
    const testTotal = 100;
    const testVat = testTotal * 0.05;
    const testTotalWithVat = testTotal + testVat;
    
    console.log('Test calculation:', {
        total: testTotal,
        vat: testVat,
        totalWithVat: testTotalWithVat
    });
    
    // Test checkbox functionality
    const vatCheckboxes = document.querySelectorAll('.item-vat-checkbox');
    console.log('Found VAT checkboxes:', vatCheckboxes.length);
    
    vatCheckboxes.forEach((checkbox, index) => {
        console.log(`Checkbox ${index}:`, checkbox.checked);
    });
}

document.addEventListener('DOMContentLoaded', function() {
    // Initialize quotation functionality
    initQuotationForm();
    initItemFormset();
    initCalculations();
    initStatusUpdates();
    initSearchFilters();
    
    // Test VAT calculation after a short delay
    setTimeout(testVatCalculation, 1000);
    
    // Add service selection event listeners
    const itemsContainer = document.getElementById('items-container');
    if (itemsContainer) {
        itemsContainer.addEventListener('change', function(e) {
            if (e.target.name && e.target.name.includes('service')) {
                populateUnitPriceFromService(e.target);
            }
        });
    }
});

function initQuotationForm() {
    const form = document.getElementById('quotationForm');
    if (!form) return;

    // Form validation
    form.addEventListener('submit', function(e) {
        if (!validateForm()) {
            e.preventDefault();
            showFirstTabWithErrors();
        }
    });

    // Auto-calculate totals when financial fields change
    const additionalTaxField = document.getElementById('id_additional_tax_amount');
    const discountField = document.getElementById('id_discount_amount');
    
    if (additionalTaxField) {
        additionalTaxField.addEventListener('input', calculateTotals);
    }
    if (discountField) {
        discountField.addEventListener('input', calculateTotals);
    }
}

function initItemFormset() {
    const addItemBtn = document.getElementById('add-item');
    const itemsContainer = document.getElementById('items-container');
    
    if (!addItemBtn || !itemsContainer) return;

    addItemBtn.addEventListener('click', function() {
        addNewItem();
    });

    // Test VAT button (for debugging)
    const testVatBtn = document.getElementById('test-vat');
    if (testVatBtn) {
        testVatBtn.addEventListener('click', function() {
            console.log('Manual VAT test triggered');
            testVatCalculation();
            
            // Trigger calculation for all items
            const itemForms = document.querySelectorAll('.item-form');
            itemForms.forEach(form => {
                const quantityField = form.querySelector('input[name*="quantity"]');
                const unitPriceField = form.querySelector('input[name*="unit_price"]');
                if (quantityField && unitPriceField) {
                    calculateItemTotal(quantityField);
                }
            });
        });
    }

    // Handle item deletion
    itemsContainer.addEventListener('change', function(e) {
        if (e.target.type === 'checkbox' && e.target.name.includes('DELETE')) {
            const itemForm = e.target.closest('.item-form');
            const notesRow = itemForm.nextElementSibling;
            
            if (e.target.checked) {
                itemForm.style.opacity = '0.5';
                itemForm.style.pointerEvents = 'none';
                if (notesRow && notesRow.classList.contains('item-notes-row')) {
                    notesRow.style.display = 'none';
                }
            } else {
                itemForm.style.opacity = '1';
                itemForm.style.pointerEvents = 'auto';
                if (notesRow && notesRow.classList.contains('item-notes-row')) {
                    notesRow.style.display = 'table-row';
                }
            }
        }
        
        // Handle service selection for auto-populating unit price
        if (e.target.name && e.target.name.includes('service')) {
            populateUnitPriceFromService(e.target);
        }
        
        // Handle VAT checkbox changes
        if (e.target.classList.contains('item-vat-checkbox')) {
            console.log('VAT checkbox changed:', e.target.checked); // Debug log
            calculateItemTotal(e.target);
        }
    });

    // Auto-calculate item totals
    itemsContainer.addEventListener('input', function(e) {
        if (e.target.name.includes('quantity') || e.target.name.includes('unit_price')) {
            calculateItemTotal(e.target);
        }
    });
    
    // Handle Tab key on unit price field to add new row
    itemsContainer.addEventListener('keydown', function(e) {
        if (e.key === 'Tab' && e.target.name && e.target.name.includes('unit_price')) {
            console.log('Tab pressed on unit price field'); // Debug log
            
            // Check if this is the last unit price field
            const currentForm = e.target.closest('.item-form');
            const allForms = itemsContainer.querySelectorAll('.item-form');
            const currentIndex = Array.from(allForms).indexOf(currentForm);
            const isLastForm = currentIndex === allForms.length - 1;
            
            console.log('Current form index:', currentIndex, 'Total forms:', allForms.length, 'Is last:', isLastForm); // Debug log
            
            // If this is the last form, add new row
            if (isLastForm) {
                e.preventDefault(); // Prevent default tab behavior
                console.log('Adding new item...'); // Debug log
                
                // Call the fixed addNewItem function
                addNewItem();
                
                // Focus on the service field of the new row
                setTimeout(() => {
                    const newForm = itemsContainer.lastElementChild;
                    const newServiceField = newForm.querySelector('select[name*="service"]');
                    if (newServiceField) {
                        newServiceField.focus();
                        console.log('Focused on new service field'); // Debug log
                    }
                }, 100);
            }
        }
    });
    
    // Initialize service price population for existing forms
    const existingServiceFields = itemsContainer.querySelectorAll('select[name*="service"]');
    existingServiceFields.forEach(field => {
        if (field.value) {
            populateUnitPriceFromService(field);
        }
    });
}

function initCalculations() {
    // Initial calculation
    calculateTotals();
    
    // Initialize VAT checkboxes for existing forms
    const existingVatCheckboxes = document.querySelectorAll('.item-vat-checkbox');
    existingVatCheckboxes.forEach(checkbox => {
        console.log('Found VAT checkbox:', checkbox.checked); // Debug log
        if (checkbox.checked) {
            calculateItemTotal(checkbox);
        }
    });
    
    // Recalculate when items change
    const itemsContainer = document.getElementById('items-container');
    if (itemsContainer) {
        const observer = new MutationObserver(calculateTotals);
        observer.observe(itemsContainer, { childList: true, subtree: true });
    }
}

function initStatusUpdates() {
    // Handle status update buttons
    document.querySelectorAll('.status-update-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const quotationId = this.dataset.quotationId;
            const newStatus = this.dataset.status;
            updateQuotationStatus(quotationId, newStatus);
        });
    });
}

function initSearchFilters() {
    // Auto-submit search form on filter change
    const searchForm = document.querySelector('form[method="get"]');
    if (searchForm) {
        const autoSubmitFields = searchForm.querySelectorAll('select[name="status"], select[name="sort"]');
        autoSubmitFields.forEach(field => {
            field.addEventListener('change', function() {
                searchForm.submit();
            });
        });
    }
}

function validateForm() {
    let isValid = true;
    const requiredFields = document.querySelectorAll('.required-field');
    
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
    
    return isValid;
}

function showFirstTabWithErrors() {
    const firstInvalidField = document.querySelector('.is-invalid');
    if (firstInvalidField) {
        const tabId = firstInvalidField.closest('.tab-pane').id;
        const tabButton = document.querySelector(`[data-bs-target="#${tabId}"]`);
        if (tabButton) {
            const tab = new bootstrap.Tab(tabButton);
            tab.show();
        }
    }
}

function addNewItem() {
    const itemsContainer = document.getElementById('items-container');
    if (!itemsContainer) return;
    
    // Find the management form fields
    const totalFormsField = document.querySelector('input[name*="TOTAL_FORMS"]');
    const maxFormsField = document.querySelector('input[name*="MAX_NUM_FORMS"]');
    
    if (!totalFormsField) {
        console.error('Could not find TOTAL_FORMS field');
        return;
    }
    
    const currentFormCount = parseInt(totalFormsField.value) || 0;
    const maxForms = maxFormsField ? parseInt(maxFormsField.value) || 1000 : 1000;
    
    // Check if we can add more forms
    if (currentFormCount >= maxForms) {
        console.log('Maximum number of forms reached');
        return;
    }
    
    // Clone the first item form (table row)
    const firstForm = itemsContainer.querySelector('.item-form');
    const firstNotesRow = itemsContainer.querySelector('.item-notes-row');
    if (!firstForm) {
        console.error('Could not find first form to clone');
        return;
    }
    
    const newForm = firstForm.cloneNode(true);
    const newNotesRow = firstNotesRow ? firstNotesRow.cloneNode(true) : null;
    
    // Update form indices - find the current pattern and replace with new index
    const currentPattern = /quotationitem_set-\d+/g;
    const newIndex = currentFormCount;
    newForm.innerHTML = newForm.innerHTML.replace(currentPattern, `quotationitem_set-${newIndex}`);
    if (newNotesRow) {
        newNotesRow.innerHTML = newNotesRow.innerHTML.replace(currentPattern, `quotationitem_set-${newIndex}`);
    }
    
    // Clear form values
    newForm.querySelectorAll('input, select, textarea').forEach(field => {
        if (field.type === 'checkbox') {
            field.checked = false;
        } else {
            field.value = '';
        }
    });
    
    // Clear VAT checkbox specifically
    const vatCheckbox = newForm.querySelector('.item-vat-checkbox');
    if (vatCheckbox) {
        vatCheckbox.checked = false;
    }
    
    // Clear total displays
    const totalDisplay = newForm.querySelector('.item-total');
    const vatDisplay = newForm.querySelector('.item-vat');
    const totalVatDisplay = newForm.querySelector('.item-total-vat');
    
    if (totalDisplay) totalDisplay.textContent = '0.00';
    if (vatDisplay) vatDisplay.textContent = '0.00';
    if (totalVatDisplay) totalVatDisplay.textContent = '0.00';
    
    // Add delete checkbox
    const deleteCheckbox = newForm.querySelector('input[name*="DELETE"]');
    if (deleteCheckbox) {
        deleteCheckbox.checked = false;
    }
    
    // Append new form to tbody
    const tbody = itemsContainer.querySelector('tbody');
    if (tbody) {
        tbody.appendChild(newForm);
        
        if (newNotesRow) {
            tbody.appendChild(newNotesRow);
        }
    }
    
    // Update total forms count
    totalFormsField.value = newIndex + 1;
    
    // Recalculate totals
    calculateTotals();
    
    console.log(`Added new item form. Total forms: ${totalFormsField.value}`);
}

function calculateItemTotal(field) {
    const itemForm = field.closest('.item-form');
    const quantityField = itemForm.querySelector('input[name*="quantity"]');
    const unitPriceField = itemForm.querySelector('input[name*="unit_price"]');
    
    if (quantityField && unitPriceField) {
        const quantity = parseFloat(quantityField.value) || 0;
        const unitPrice = parseFloat(unitPriceField.value) || 0;
        const total = quantity * unitPrice;
        
        // Check if VAT checkbox is checked
        const vatCheckbox = itemForm.querySelector('.item-vat-checkbox');
        const hasVat = vatCheckbox ? vatCheckbox.checked : false;
        
        console.log('Calculating item total:', { quantity, unitPrice, total, hasVat }); // Debug log
        
        const vatRate = 0.05; // 5% VAT
        const vatAmount = hasVat ? total * vatRate : 0;
        const totalWithVat = total + vatAmount;
        
        console.log('VAT calculation:', { vatAmount, totalWithVat }); // Debug log
        
        // Update total display
        const totalDisplay = itemForm.querySelector('.item-total');
        if (totalDisplay) {
            totalDisplay.textContent = total.toFixed(2);
        }
        
        // Update VAT display
        const vatDisplay = itemForm.querySelector('.item-vat');
        if (vatDisplay) {
            vatDisplay.textContent = vatAmount.toFixed(2);
            // Add CSS class for visual feedback
            if (!hasVat) {
                vatDisplay.classList.add('no-vat');
            } else {
                vatDisplay.classList.remove('no-vat');
            }
        }
        
        // Update total with VAT display
        const totalVatDisplay = itemForm.querySelector('.item-total-vat');
        if (totalVatDisplay) {
            totalVatDisplay.textContent = totalWithVat.toFixed(2);
        }
    }
    
    calculateTotals();
}

function calculateTotals() {
    let subtotal = 0;
    let totalVat = 0;
    
    // Calculate subtotal and VAT from items
    const itemForms = document.querySelectorAll('.item-form');
    itemForms.forEach(form => {
        const deleteCheckbox = form.querySelector('input[name*="DELETE"]');
        if (!deleteCheckbox || !deleteCheckbox.checked) {
            const quantityField = form.querySelector('input[name*="quantity"]');
            const unitPriceField = form.querySelector('input[name*="unit_price"]');
            
            if (quantityField && unitPriceField) {
                const quantity = parseFloat(quantityField.value) || 0;
                const unitPrice = parseFloat(unitPriceField.value) || 0;
                const itemTotal = quantity * unitPrice;
                
                // Check if VAT checkbox is checked
                const vatCheckbox = form.querySelector('.item-vat-checkbox');
                const hasVat = vatCheckbox ? vatCheckbox.checked : false;
                const itemVat = hasVat ? itemTotal * 0.05 : 0; // 5% VAT only if enabled
                
                subtotal += itemTotal;
                totalVat += itemVat;
            }
        }
    });
    
    // Get additional tax and discount amounts
    const additionalTaxField = document.getElementById('id_additional_tax_amount');
    const discountField = document.getElementById('id_discount_amount');
    
    const additionalTax = parseFloat(additionalTaxField?.value) || 0;
    const discountAmount = parseFloat(discountField?.value) || 0;
    
    // Calculate total (subtotal + VAT + additional tax - discount)
    const total = subtotal + totalVat + additionalTax - discountAmount;
    
    // Update display
    updateSummaryDisplay(subtotal, totalVat + additionalTax, discountAmount, total);
}

function updateSummaryDisplay(subtotal, totalTax, discount, total) {
    const subtotalDisplay = document.getElementById('subtotal');
    const vatDisplay = document.getElementById('vat-display');
    const additionalTaxDisplay = document.getElementById('additional-tax-display');
    const discountDisplay = document.getElementById('discount-display');
    const totalDisplay = document.getElementById('total-display');
    
    // Calculate VAT from items (only for items with VAT checkbox checked)
    let itemVat = 0;
    const itemForms = document.querySelectorAll('.item-form');
    itemForms.forEach(form => {
        const deleteCheckbox = form.querySelector('input[name*="DELETE"]');
        if (!deleteCheckbox || !deleteCheckbox.checked) {
            const quantityField = form.querySelector('input[name*="quantity"]');
            const unitPriceField = form.querySelector('input[name*="unit_price"]');
            const vatCheckbox = form.querySelector('.item-vat-checkbox');
            
            if (quantityField && unitPriceField) {
                const quantity = parseFloat(quantityField.value) || 0;
                const unitPrice = parseFloat(unitPriceField.value) || 0;
                const itemTotal = quantity * unitPrice;
                const hasVat = vatCheckbox ? vatCheckbox.checked : false;
                
                if (hasVat) {
                    itemVat += itemTotal * 0.05; // 5% VAT
                }
            }
        }
    });
    
    const additionalTax = totalTax - itemVat;
    
    if (subtotalDisplay) subtotalDisplay.textContent = subtotal.toFixed(2);
    if (vatDisplay) vatDisplay.textContent = itemVat.toFixed(2);
    if (additionalTaxDisplay) additionalTaxDisplay.textContent = additionalTax.toFixed(2);
    if (discountDisplay) discountDisplay.textContent = discount.toFixed(2);
    if (totalDisplay) totalDisplay.textContent = total.toFixed(2);
}

function updateQuotationStatus(quotationId, newStatus) {
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    
    fetch(`/quotation/${quotationId}/status/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': csrfToken,
        },
        body: `status=${newStatus}`
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update status badge
            const statusBadge = document.querySelector(`[data-quotation-id="${quotationId}"] .status-badge`);
            if (statusBadge) {
                statusBadge.textContent = getStatusLabel(newStatus);
                statusBadge.className = `badge bg-${newStatus}`;
            }
            
            // Show success message
            showMessage('Status updated successfully', 'success');
        } else {
            showMessage('Failed to update status', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showMessage('An error occurred while updating status', 'error');
    });
}

function getStatusLabel(status) {
    const statusLabels = {
        'draft': 'Draft',
        'sent': 'Sent',
        'accepted': 'Accepted',
        'rejected': 'Rejected',
        'expired': 'Expired'
    };
    return statusLabels[status] || status;
}

function showMessage(message, type) {
    // Create message element
    const messageDiv = document.createElement('div');
    messageDiv.className = `alert alert-${type === 'success' ? 'success' : 'danger'} alert-dismissible fade show`;
    messageDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // Insert at top of container
    const container = document.querySelector('.container-fluid');
    if (container) {
        container.insertBefore(messageDiv, container.firstChild);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (messageDiv.parentNode) {
                messageDiv.remove();
            }
        }, 5000);
    }
}

// Utility function to format currency
function formatCurrency(amount, currency = 'AED') {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: currency
    }).format(amount);
}

// Function to populate unit price from selected service
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
                
                // Set VAT checkbox based on service VAT setting (optional - for convenience)
                const vatCheckbox = itemForm.querySelector('.item-vat-checkbox');
                if (vatCheckbox && data.has_vat) {
                    vatCheckbox.checked = data.has_vat;
                }
                
                // Trigger calculation
                calculateItemTotal(unitPriceField);
            }
        })
        .catch(error => {
            console.error('Error fetching service price:', error);
        });
}

// Export functions for use in other scripts
window.QuotationApp = {
    calculateTotals,
    addNewItem,
    updateQuotationStatus,
    formatCurrency
}; 