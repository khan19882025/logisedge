// Items Module JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize form validation
    initializeFormValidation();
    
    // Initialize search functionality
    initializeSearch();
    
    // Initialize tab switching for forms with errors
    initializeTabSwitching();
    
    // Initialize price calculation
    initializePriceCalculation();
    
    // Initialize item code generation
    initializeItemCodeGeneration();
    
    // Initialize event listeners for buttons
    initializeEventListeners();
});

// Initialize event listeners for buttons
function initializeEventListeners() {
    // Quick view buttons
    document.querySelectorAll('.quick-view-btn').forEach(button => {
        button.addEventListener('click', function() {
            const itemId = this.getAttribute('data-item-id');
            quickView(itemId);
        });
    });
    
    // Delete buttons
    document.querySelectorAll('.delete-item-btn').forEach(button => {
        button.addEventListener('click', function() {
            const itemId = this.getAttribute('data-item-id');
            const itemName = this.getAttribute('data-item-name');
            deleteItem(itemId, itemName);
        });
    });
}

// Form Validation
function initializeFormValidation() {
    const form = document.getElementById('itemForm');
    if (form) {
        form.addEventListener('submit', function(e) {
            if (!validateForm()) {
                e.preventDefault();
                showFormErrors();
            }
        });
    }
}

function validateForm() {
    let isValid = true;
    const requiredFields = ['item_code', 'item_name'];
    
    requiredFields.forEach(fieldName => {
        const field = document.getElementById(`id_${fieldName}`);
        if (field && !field.value.trim()) {
            isValid = false;
            field.classList.add('is-invalid');
        } else if (field) {
            field.classList.remove('is-invalid');
        }
    });
    
    // Validate item code format
    const itemCodeField = document.getElementById('id_item_code');
    if (itemCodeField && itemCodeField.value) {
        const itemCodePattern = /^[A-Z0-9-]+$/;
        if (!itemCodePattern.test(itemCodeField.value.toUpperCase())) {
            isValid = false;
            itemCodeField.classList.add('is-invalid');
            showFieldError(itemCodeField, 'Item code must contain only uppercase letters, numbers, and hyphens.');
        }
    }
    
    // Validate pricing
    const costPriceField = document.getElementById('id_cost_price');
    const sellingPriceField = document.getElementById('id_selling_price');
    
    if (costPriceField && sellingPriceField && costPriceField.value && sellingPriceField.value) {
        const costPrice = parseFloat(costPriceField.value);
        const sellingPrice = parseFloat(sellingPriceField.value);
        
        if (costPrice > sellingPrice) {
            isValid = false;
            costPriceField.classList.add('is-invalid');
            sellingPriceField.classList.add('is-invalid');
            showFieldError(costPriceField, 'Cost price cannot be higher than selling price.');
        }
    }
    
    return isValid;
}

function showFormErrors() {
    // Switch to first tab with errors
    const firstErrorTab = document.querySelector('.tab-pane .is-invalid');
    if (firstErrorTab) {
        const tabId = firstErrorTab.closest('.tab-pane').id;
        const tabButton = document.querySelector(`[data-bs-target="#${tabId}"]`);
        if (tabButton) {
            const tab = new bootstrap.Tab(tabButton);
            tab.show();
        }
    }
    
    // Show error message
    showAlert('Please correct the errors below.', 'danger');
}

function showFieldError(field, message) {
    // Remove existing error message
    const existingError = field.parentNode.querySelector('.invalid-feedback');
    if (existingError) {
        existingError.remove();
    }
    
    // Add new error message
    const errorDiv = document.createElement('div');
    errorDiv.className = 'invalid-feedback d-block';
    errorDiv.textContent = message;
    field.parentNode.appendChild(errorDiv);
}

// Search Functionality
function initializeSearch() {
    const searchForm = document.querySelector('form[method="get"]');
    if (searchForm) {
        const searchInput = searchForm.querySelector('input[name="search_term"]');
        if (searchInput) {
            let searchTimeout;
            searchInput.addEventListener('input', function() {
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(() => {
                    searchForm.submit();
                }, 500);
            });
        }
    }
}

// Tab Switching for Forms with Errors
function initializeTabSwitching() {
    const form = document.getElementById('itemForm');
    if (form) {
        // Check if there are any validation errors
        const hasErrors = form.querySelector('.is-invalid');
        if (hasErrors) {
            // Find the first tab with errors and switch to it
            const errorTab = hasErrors.closest('.tab-pane');
            if (errorTab) {
                const tabId = errorTab.id;
                const tabButton = document.querySelector(`[data-bs-target="#${tabId}"]`);
                if (tabButton) {
                    const tab = new bootstrap.Tab(tabButton);
                    tab.show();
                }
            }
        }
    }
}

// Price Calculation
function initializePriceCalculation() {
    const costPriceField = document.getElementById('id_cost_price');
    const sellingPriceField = document.getElementById('id_selling_price');
    
    if (costPriceField && sellingPriceField) {
        [costPriceField, sellingPriceField].forEach(field => {
            field.addEventListener('input', calculateProfit);
        });
    }
}

function calculateProfit() {
    const costPriceField = document.getElementById('id_cost_price');
    const sellingPriceField = document.getElementById('id_selling_price');
    
    if (costPriceField && sellingPriceField) {
        const costPrice = parseFloat(costPriceField.value) || 0;
        const sellingPrice = parseFloat(sellingPriceField.value) || 0;
        
        if (costPrice > 0 && sellingPrice > 0) {
            const profitAmount = sellingPrice - costPrice;
            const profitMargin = (profitAmount / costPrice) * 100;
            
            // Update profit display if it exists
            const profitDisplay = document.getElementById('profitDisplay');
            if (profitDisplay) {
                profitDisplay.innerHTML = `
                    <div class="alert alert-info">
                        <strong>Profit Amount:</strong> ${profitAmount.toFixed(2)} <br>
                        <strong>Profit Margin:</strong> ${profitMargin.toFixed(1)}%
                    </div>
                `;
            }
        }
    }
}

// Item Code Generation
function initializeItemCodeGeneration() {
    const itemCodeField = document.getElementById('id_item_code');
    if (itemCodeField) {
        // Auto-uppercase
        itemCodeField.addEventListener('input', function() {
            this.value = this.value.toUpperCase();
        });
        
        // Generate button if it doesn't exist
        if (!document.getElementById('generateCodeBtn')) {
            const generateBtn = document.createElement('button');
            generateBtn.type = 'button';
            generateBtn.id = 'generateCodeBtn';
            generateBtn.className = 'btn btn-outline-secondary btn-sm ms-2';
            generateBtn.innerHTML = '<i class="bi bi-magic"></i> Generate';
            generateBtn.onclick = generateItemCode;
            
            itemCodeField.parentNode.appendChild(generateBtn);
        }
    }
}

function generateItemCode() {
    const itemNameField = document.getElementById('id_item_name');
    const itemCodeField = document.getElementById('id_item_code');
    
    if (itemNameField && itemCodeField) {
        const itemName = itemNameField.value.trim();
        if (itemName) {
            // Generate code based on item name
            const prefix = 'ITM';
            const timestamp = Date.now().toString().slice(-4);
            const nameCode = itemName.substring(0, 3).toUpperCase().replace(/[^A-Z0-9]/g, '');
            const generatedCode = `${prefix}-${nameCode}-${timestamp}`;
            
            itemCodeField.value = generatedCode;
            itemCodeField.classList.remove('is-invalid');
        } else {
            showAlert('Please enter an item name first.', 'warning');
        }
    }
}

// Quick View Functionality
function quickView(itemId) {
    fetch(`/items/${itemId}/quick-view/`)
        .then(response => response.text())
        .then(html => {
            document.getElementById('quickViewContent').innerHTML = html;
            const modal = new bootstrap.Modal(document.getElementById('quickViewModal'));
            modal.show();
        })
        .catch(error => {
            console.error('Error loading quick view:', error);
            showAlert('Error loading item details.', 'danger');
        });
}

// Delete Item Functionality
function deleteItem(itemId, itemName) {
    document.getElementById('deleteItemName').textContent = itemName;
    document.getElementById('deleteForm').action = `/items/${itemId}/delete/`;
    
    const modal = new bootstrap.Modal(document.getElementById('deleteModal'));
    modal.show();
}

// Status Toggle Functionality
function toggleItemStatus(itemId) {
    fetch(`/items/${itemId}/toggle-status/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json',
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update the status display
            const statusCell = document.querySelector(`[data-item-id="${itemId}"] .status-badge`);
            if (statusCell) {
                statusCell.className = `badge ${data.status === 'active' ? 'bg-success' : 'bg-warning'}`;
                statusCell.textContent = data.status.charAt(0).toUpperCase() + data.status.slice(1);
            }
            showAlert(data.message, 'success');
        } else {
            showAlert(data.message, 'danger');
        }
    })
    .catch(error => {
        console.error('Error toggling status:', error);
        showAlert('Error updating item status.', 'danger');
    });
}

// Utility Functions
function showAlert(message, type) {
    const alertContainer = document.getElementById('alertContainer');
    if (!alertContainer) {
        // Create alert container if it doesn't exist
        const container = document.createElement('div');
        container.id = 'alertContainer';
        container.className = 'position-fixed top-0 end-0 p-3';
        container.style.zIndex = '9999';
        document.body.appendChild(container);
    }
    
    const alertId = 'alert-' + Date.now();
    const alertHtml = `
        <div id="${alertId}" class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    document.getElementById('alertContainer').insertAdjacentHTML('beforeend', alertHtml);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        const alert = document.getElementById(alertId);
        if (alert) {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }
    }, 5000);
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// DataTable Enhancement (if using DataTables)
function initializeDataTable() {
    const table = document.getElementById('itemsTable');
    if (table && typeof $.fn.DataTable !== 'undefined') {
        $('#itemsTable').DataTable({
            pageLength: 20,
            order: [[1, 'asc']], // Sort by item name by default
            responsive: true,
            language: {
                search: "Search items:",
                lengthMenu: "Show _MENU_ items per page",
                info: "Showing _START_ to _END_ of _TOTAL_ items",
                paginate: {
                    first: "First",
                    last: "Last",
                    next: "Next",
                    previous: "Previous"
                }
            }
        });
    }
}

// Export Functionality
function exportItems(format = 'csv') {
    const searchParams = new URLSearchParams(window.location.search);
    const exportUrl = `/items/export/?${searchParams.toString()}`;
    
    window.location.href = exportUrl;
}

// Keyboard Shortcuts
document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + N for new item
    if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
        e.preventDefault();
        const createUrl = document.querySelector('a[href*="/create/"]');
        if (createUrl) {
            window.location.href = createUrl.href;
        }
    }
    
    // Ctrl/Cmd + F for search
    if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
        e.preventDefault();
        const searchInput = document.querySelector('input[name="search_term"]');
        if (searchInput) {
            searchInput.focus();
        }
    }
    
    // Escape to close modals
    if (e.key === 'Escape') {
        const modals = document.querySelectorAll('.modal.show');
        modals.forEach(modal => {
            const bsModal = bootstrap.Modal.getInstance(modal);
            if (bsModal) {
                bsModal.hide();
            }
        });
    }
});

// Form Auto-save (optional)
function initializeAutoSave() {
    const form = document.getElementById('itemForm');
    if (form) {
        let autoSaveTimeout;
        
        form.addEventListener('input', function() {
            clearTimeout(autoSaveTimeout);
            autoSaveTimeout = setTimeout(() => {
                // Auto-save logic here
                console.log('Auto-saving form...');
            }, 2000);
        });
    }
}

// Initialize all features
document.addEventListener('DOMContentLoaded', function() {
    initializeAutoSave();
    initializeDataTable();
}); 