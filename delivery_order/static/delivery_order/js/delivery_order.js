// Delivery Order App JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize delivery order functionality
    initDeliveryOrder();
});

function initDeliveryOrder() {
    // Initialize list functionality
    initDeliveryOrderList();
    
    // Initialize form functionality
    initDeliveryOrderForm();
    
    // Initialize search functionality
    initSearch();
}

function initDeliveryOrderList() {
    // Initialize status filter
    const statusFilter = document.getElementById('status');
    if (statusFilter) {
        statusFilter.addEventListener('change', function() {
            this.form.submit();
        });
    }
    
    // Initialize priority filter
    const priorityFilter = document.getElementById('priority');
    if (priorityFilter) {
        priorityFilter.addEventListener('change', function() {
            this.form.submit();
        });
    }
    
    // Initialize delete confirmations
    initDeleteConfirmations();
    
    // Initialize status updates
    initStatusUpdates();
}

function initDeliveryOrderForm() {
    const customerSelect = document.getElementById('id_customer');
    const grnSelect = document.getElementById('id_grn');
    
    if (customerSelect) {
        // Load customer info when customer is selected
        customerSelect.addEventListener('change', function() {
            loadCustomerInfo(this.value);
        });
    }
    
    if (grnSelect) {
        // Load GRN items when GRN is selected
        grnSelect.addEventListener('change', function() {
            loadGRNItems(this.value);
        });
    }
    
    // Initialize formset functionality
    initFormset();
}

function loadCustomerInfo(customerId) {
    if (!customerId) {
        clearCustomerInfo();
        return;
    }
    
    fetch(`/delivery_order/ajax/customer/${customerId}/`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                populateCustomerInfo(data.customer);
            } else {
                console.error('Error loading customer info:', data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
}

function populateCustomerInfo(customer) {
    // Auto-fill delivery address if empty - use shipping address if available, otherwise billing address
    const deliverToAddressField = document.getElementById('id_deliver_to_address');
    if (deliverToAddressField && !deliverToAddressField.value) {
        if (customer.shipping_address) {
            deliverToAddressField.value = customer.shipping_address;
        } else if (customer.billing_address) {
            deliverToAddressField.value = customer.billing_address;
        }
    }
    
    // Auto-fill delivery contact if empty
    const deliveryContactField = document.getElementById('id_delivery_contact');
    if (deliveryContactField && !deliveryContactField.value && customer.customer_name) {
        deliveryContactField.value = customer.customer_name;
    }
    
    // Auto-fill delivery phone if empty
    const deliveryPhoneField = document.getElementById('id_delivery_phone');
    if (deliveryPhoneField && !deliveryPhoneField.value && customer.phone) {
        deliveryPhoneField.value = customer.phone;
    }
    
    // Auto-fill delivery email if empty
    const deliveryEmailField = document.getElementById('id_delivery_email');
    if (deliveryEmailField && !deliveryEmailField.value && customer.email) {
        deliveryEmailField.value = customer.email;
    }
}

function clearCustomerInfo() {
    // Clear delivery information fields
    const fields = ['id_deliver_to_address', 'id_delivery_contact', 'id_delivery_phone', 'id_delivery_email'];
    fields.forEach(fieldId => {
        const field = document.getElementById(fieldId);
        if (field) {
            field.value = '';
        }
    });
}

function loadGRNItems(grnId) {
    if (!grnId) {
        return;
    }
    
    fetch(`/delivery_order/ajax/grn-items/${grnId}/`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                console.log('GRN items loaded:', data.items);
                // You can use this data to populate item dropdowns or show available items
            } else {
                console.error('Error loading GRN items:', data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
}

function initFormset() {
    // Add formset management functionality
    const addItemBtn = document.getElementById('add-item-btn');
    const formsetContainer = document.getElementById('formset-container');
    
    if (addItemBtn && formsetContainer) {
        addItemBtn.addEventListener('click', function(e) {
            e.preventDefault();
            addFormsetRow();
        });
    }
    
    // Initialize delete buttons for existing formsets
    initFormsetDeleteButtons();
}

function addFormsetRow() {
    const formsetContainer = document.getElementById('formset-container');
    const totalFormsInput = document.getElementById('id_items-TOTAL_FORMS');
    
    if (!formsetContainer || !totalFormsInput) return;
    
    const currentForms = parseInt(totalFormsInput.value);
    const newFormNum = currentForms;
    
    // Clone the first formset row
    const firstRow = formsetContainer.querySelector('.formset-row');
    if (!firstRow) return;
    
    const newRow = firstRow.cloneNode(true);
    
    // Update form indices
    newRow.querySelectorAll('input, select, textarea').forEach(input => {
        const name = input.getAttribute('name');
        if (name) {
            input.setAttribute('name', name.replace(/items-\d+/, `items-${newFormNum}`));
            input.setAttribute('id', input.getAttribute('id').replace(/items-\d+/, `items-${newFormNum}`));
        }
    });
    
    // Clear the values
    newRow.querySelectorAll('input, select, textarea').forEach(input => {
        if (input.type !== 'hidden') {
            input.value = '';
        }
    });
    
    // Add delete button
    const deleteBtn = document.createElement('button');
    deleteBtn.type = 'button';
    deleteBtn.className = 'btn btn-outline-danger btn-sm remove-row-btn';
    deleteBtn.innerHTML = '<i class="bi bi-trash"></i>';
    deleteBtn.onclick = function() {
        removeFormsetRow(this);
    };
    
    newRow.appendChild(deleteBtn);
    formsetContainer.appendChild(newRow);
    
    // Update total forms count
    totalFormsInput.value = currentForms + 1;
}

function removeFormsetRow(button) {
    const row = button.closest('.formset-row');
    if (row) {
        row.remove();
        updateFormsetIndices();
    }
}

function updateFormsetIndices() {
    const formsetContainer = document.getElementById('formset-container');
    const totalFormsInput = document.getElementById('id_items-TOTAL_FORMS');
    
    if (!formsetContainer || !totalFormsInput) return;
    
    const rows = formsetContainer.querySelectorAll('.formset-row');
    totalFormsInput.value = rows.length;
    
    rows.forEach((row, index) => {
        row.querySelectorAll('input, select, textarea').forEach(input => {
            const name = input.getAttribute('name');
            if (name) {
                input.setAttribute('name', name.replace(/items-\d+/, `items-${index}`));
                input.setAttribute('id', input.getAttribute('id').replace(/items-\d+/, `items-${index}`));
            }
        });
    });
}

function initFormsetDeleteButtons() {
    const deleteButtons = document.querySelectorAll('.remove-row-btn');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function() {
            removeFormsetRow(this);
        });
    });
}

function initDeleteConfirmations() {
    const deleteButtons = document.querySelectorAll('.btn-outline-danger');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to delete this delivery order? This action cannot be undone.')) {
                e.preventDefault();
            }
        });
    });
}

function initStatusUpdates() {
    const statusButtons = document.querySelectorAll('.status-update-btn');
    statusButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const deliveryOrderId = this.dataset.deliveryOrderId;
            const newStatus = this.dataset.status;
            
            if (confirm(`Are you sure you want to update the status to "${newStatus}"?`)) {
                updateDeliveryOrderStatus(deliveryOrderId, newStatus);
            }
        });
    });
}

function updateDeliveryOrderStatus(deliveryOrderId, status) {
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = `/delivery_order/${deliveryOrderId}/status/`;
    
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    const csrfInput = document.createElement('input');
    csrfInput.type = 'hidden';
    csrfInput.name = 'csrfmiddlewaretoken';
    csrfInput.value = csrfToken;
    
    const statusInput = document.createElement('input');
    statusInput.type = 'hidden';
    statusInput.name = 'status';
    statusInput.value = status;
    
    form.appendChild(csrfInput);
    form.appendChild(statusInput);
    document.body.appendChild(form);
    form.submit();
}

function initSearch() {
    const searchInput = document.getElementById('search');
    if (searchInput) {
        let searchTimeout;
        
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                this.form.submit();
            }, 500);
        });
    }
}

// Utility functions
function showLoading(element) {
    element.classList.add('loading');
}

function hideLoading(element) {
    element.classList.remove('loading');
}

function showMessage(message, type = 'info') {
    // Create toast notification
    const toast = document.createElement('div');
    toast.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    toast.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    toast.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(toast);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (toast.parentNode) {
            toast.remove();
        }
    }, 5000);
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

function formatNumber(number) {
    return new Intl.NumberFormat('en-US').format(number);
} 