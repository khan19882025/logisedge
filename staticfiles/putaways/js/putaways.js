// Putaways App JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize putaways functionality
    initPutaways();
});

function initPutaways() {
    // Initialize form functionality
    initPutawayForm();
    
    // Initialize list functionality
    initPutawayList();
    
    // Initialize search functionality
    initSearch();
}

function initPutawayForm() {
    const grnSelect = document.getElementById('id_grn');
    const itemSelect = document.getElementById('id_item');
    const quantityInput = document.getElementById('id_quantity');
    
    if (grnSelect && itemSelect) {
        // Load items when GRN is selected
        grnSelect.addEventListener('change', function() {
            loadGRNItems(this.value, itemSelect, quantityInput);
        });
        
        // Auto-fill quantity when item is selected
        itemSelect.addEventListener('change', function() {
            autoFillQuantity(this, quantityInput);
        });
    }
}

function loadGRNItems(grnId, itemSelect, quantityInput) {
    if (!grnId) {
        itemSelect.innerHTML = '<option value="">Select Item</option>';
        return;
    }
    
    // Show loading state
    itemSelect.disabled = true;
    itemSelect.innerHTML = '<option value="">Loading items...</option>';
    
    fetch(`/putaways/get-grn-items/${grnId}/`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                populateItemSelect(itemSelect, data.items);
            } else {
                console.error('Error loading items:', data.error);
                itemSelect.innerHTML = '<option value="">Error loading items</option>';
            }
        })
        .catch(error => {
            console.error('Error:', error);
            itemSelect.innerHTML = '<option value="">Error loading items</option>';
        })
        .finally(() => {
            itemSelect.disabled = false;
        });
}

function populateItemSelect(itemSelect, items) {
    itemSelect.innerHTML = '<option value="">Select Item</option>';
    
    items.forEach(item => {
        const option = document.createElement('option');
        option.value = item.id;
        option.textContent = `${item.name} (${item.code}) - Available: ${item.available_qty}`;
        option.dataset.availableQty = item.available_qty;
        itemSelect.appendChild(option);
    });
}

function autoFillQuantity(itemSelect, quantityInput) {
    const selectedOption = itemSelect.options[itemSelect.selectedIndex];
    if (selectedOption && selectedOption.dataset.availableQty) {
        quantityInput.value = selectedOption.dataset.availableQty;
    }
}

function initPutawayList() {
    // Initialize status filter
    const statusFilter = document.getElementById('status');
    if (statusFilter) {
        statusFilter.addEventListener('change', function() {
            this.form.submit();
        });
    }
    
    // Initialize delete confirmations
    initDeleteConfirmations();
    
    // Initialize status updates
    initStatusUpdates();
}

function initDeleteConfirmations() {
    const deleteButtons = document.querySelectorAll('.btn-outline-danger');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to delete this putaway? This action cannot be undone.')) {
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
            const putawayId = this.dataset.putawayId;
            const newStatus = this.dataset.status;
            
            if (confirm(`Are you sure you want to update the status to "${newStatus}"?`)) {
                updatePutawayStatus(putawayId, newStatus);
            }
        });
    });
}

function updatePutawayStatus(putawayId, status) {
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = `/putaways/${putawayId}/status/`;
    
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

// Export functions for global use
window.PutawaysApp = {
    showMessage,
    formatDate,
    formatNumber,
    loadGRNItems,
    updatePutawayStatus
}; 