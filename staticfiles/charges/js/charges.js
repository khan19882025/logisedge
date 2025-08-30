/**
 * Charges Module JavaScript
 * Handles interactive functionality for the charges system
 */

document.addEventListener('DOMContentLoaded', function() {
    initializeChargesModule();
});

function initializeChargesModule() {
    // Initialize tooltips
    initializeTooltips();
    
    // Initialize form validation
    initializeFormValidation();
    
    // Initialize dynamic form behavior
    initializeDynamicForms();
    
    // Initialize table sorting
    initializeTableSorting();
    
    // Initialize export functionality
    initializeExportFunctionality();
}

function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

function initializeFormValidation() {
    // Add custom validation for date ranges
    const dateFromInputs = document.querySelectorAll('input[name*="from"]');
    const dateToInputs = document.querySelectorAll('input[name*="to"]');
    
    dateFromInputs.forEach(input => {
        input.addEventListener('change', function() {
            validateDateRange(this);
        });
    });
    
    dateToInputs.forEach(input => {
        input.addEventListener('change', function() {
            validateDateRange(this);
        });
    });
}

function validateDateRange(input) {
    const form = input.closest('form');
    const fromInput = form.querySelector('input[name*="from"]');
    const toInput = form.querySelector('input[name*="to"]');
    
    if (fromInput && toInput && fromInput.value && toInput.value) {
        const fromDate = new Date(fromInput.value);
        const toDate = new Date(toInput.value);
        
        if (fromDate > toDate) {
            showValidationError(toInput, 'End date must be after start date');
        } else {
            clearValidationError(toInput);
        }
    }
}

function showValidationError(input, message) {
    input.classList.add('is-invalid');
    
    // Remove existing error message
    const existingError = input.parentNode.querySelector('.invalid-feedback');
    if (existingError) {
        existingError.remove();
    }
    
    // Add new error message
    const errorDiv = document.createElement('div');
    errorDiv.className = 'invalid-feedback';
    errorDiv.textContent = message;
    input.parentNode.appendChild(errorDiv);
}

function clearValidationError(input) {
    input.classList.remove('is-invalid');
    const errorDiv = input.parentNode.querySelector('.invalid-feedback');
    if (errorDiv) {
        errorDiv.remove();
    }
}

function initializeDynamicForms() {
    // Handle customer and item selection in charge form
    const customerSelect = document.getElementById('customer-select');
    const itemSelect = document.getElementById('item-select');
    
    if (customerSelect && itemSelect) {
        [customerSelect, itemSelect].forEach(select => {
            select.addEventListener('change', function() {
                if (customerSelect.value && itemSelect.value) {
                    loadExistingCharges(customerSelect.value, itemSelect.value);
                } else {
                    clearExistingCharges();
                }
            });
        });
    }
    
    // Handle charge type changes
    const chargeTypeSelect = document.getElementById('charge-type-select');
    if (chargeTypeSelect) {
        chargeTypeSelect.addEventListener('change', function() {
            updateRatePlaceholder(this.value);
        });
    }
}

function initializeTableSorting() {
    const tables = document.querySelectorAll('.table-sortable');
    
    tables.forEach(table => {
        const headers = table.querySelectorAll('th[data-sortable]');
        
        headers.forEach((header, index) => {
            header.addEventListener('click', function() {
                sortTable(table, index);
            });
            
            // Add sort indicator
            header.innerHTML += ' <span class="sort-indicator">↕</span>';
        });
    });
}

function sortTable(table, columnIndex) {
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    const header = table.querySelector(`th[data-sortable]:nth-child(${columnIndex + 1})`);
    const currentOrder = header.getAttribute('data-sort') || 'none';
    
    // Determine new sort order
    const newOrder = currentOrder === 'asc' ? 'desc' : 'asc';
    
    // Sort rows
    rows.sort((a, b) => {
        const aValue = getCellValue(a, columnIndex);
        const bValue = getCellValue(b, columnIndex);
        
        if (newOrder === 'asc') {
            return aValue.localeCompare(bValue, undefined, { numeric: true });
        } else {
            return bValue.localeCompare(aValue, undefined, { numeric: true });
        }
    });
    
    // Reorder rows in table
    rows.forEach(row => tbody.appendChild(row));
    
    // Update sort indicators
    updateSortIndicators(table, columnIndex, newOrder === 'asc');
    
    // Update header data attribute
    header.setAttribute('data-sort', newOrder);
}

function getCellValue(row, columnIndex) {
    const cell = row.querySelector(`td:nth-child(${columnIndex + 1})`);
    return cell ? cell.textContent.trim() : '';
}

function updateSortIndicators(table, columnIndex, isAscending) {
    const headers = table.querySelectorAll('th[data-sortable]');
    
    headers.forEach((header, index) => {
        const indicator = header.querySelector('.sort-indicator');
        if (index === columnIndex) {
            indicator.textContent = isAscending ? ' ↑' : ' ↓';
        } else {
            indicator.textContent = ' ↕';
        }
    });
}

function initializeExportFunctionality() {
    // Add export buttons if they don't exist
    addExportButtons();
    
    // Handle export clicks
    document.addEventListener('click', function(e) {
        if (e.target.matches('.export-btn')) {
            const format = e.target.getAttribute('data-format');
            exportData(format);
        }
    });
}

function addExportButtons() {
    const tableHeaders = document.querySelectorAll('.table-responsive .card-header');
    
    tableHeaders.forEach(header => {
        if (!header.querySelector('.export-buttons')) {
            const exportDiv = document.createElement('div');
            exportDiv.className = 'export-buttons';
            exportDiv.innerHTML = `
                <button class="btn btn-sm btn-outline-primary export-btn" data-format="csv">
                    <i class="bi bi-download"></i> CSV
                </button>
                <button class="btn btn-sm btn-outline-primary export-btn" data-format="excel">
                    <i class="bi bi-file-earmark-excel"></i> Excel
                </button>
            `;
            header.appendChild(exportDiv);
        }
    });
}

function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // Add to page
    document.body.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 5000);
}

function setLoadingState(loading) {
    const buttons = document.querySelectorAll('button[type="submit"]');
    const loadingText = '<span class="spinner-border spinner-border-sm me-2"></span>Processing...';
    
    buttons.forEach(button => {
        if (loading) {
            button.disabled = true;
            button.dataset.originalText = button.innerHTML;
            button.innerHTML = loadingText;
        } else {
            button.disabled = false;
            if (button.dataset.originalText) {
                button.innerHTML = button.dataset.originalText;
            }
        }
    });
}

function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}

function formatDate(date) {
    return new Intl.DateTimeFormat('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    }).format(new Date(date));
}

// Event listeners for dynamic behavior
document.addEventListener('click', function(e) {
    // Handle confirmation dialogs
    if (e.target.matches('[data-confirm]')) {
        const message = e.target.getAttribute('data-confirm');
        if (!confirm(message)) {
            e.preventDefault();
            return false;
        }
    }
    
    // Handle bulk actions
    if (e.target.matches('.bulk-action-btn')) {
        const action = e.target.getAttribute('data-action');
        const selectedIds = getSelectedChargeIds();
        
        if (selectedIds.length === 0) {
            showNotification('Please select at least one charge', 'warning');
            return;
        }
        
        if (confirm(`Are you sure you want to ${action} the selected charges?`)) {
            performBulkAction(action, selectedIds);
        }
    }
});

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + Enter to submit forms
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        const form = document.querySelector('form:focus-within');
        if (form) {
            form.submit();
        }
    }
    
    // Escape to close modals
    if (e.key === 'Escape') {
        const modals = document.querySelectorAll('.modal.show');
        modals.forEach(modal => {
            const modalInstance = bootstrap.Modal.getInstance(modal);
            if (modalInstance) {
                modalInstance.hide();
            }
        });
    }
});

function exportData(format) {
    const currentUrl = new URL(window.location);
    currentUrl.searchParams.set('export', format);
    
    const link = document.createElement('a');
    link.href = currentUrl.toString();
    link.download = `charges_export_${new Date().toISOString().split('T')[0]}.${format}`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    showNotification(`Exporting data as ${format.toUpperCase()}...`, 'info');
}

function selectAllCharges() {
    const checkboxes = document.querySelectorAll('.charge-checkbox');
    const selectAllCheckbox = document.getElementById('select-all-charges');
    
    checkboxes.forEach(checkbox => {
        checkbox.checked = selectAllCheckbox.checked;
    });
    
    updateBulkActionsVisibility();
}

function updateBulkActionsVisibility() {
    const selectedCheckboxes = document.querySelectorAll('.charge-checkbox:checked');
    const bulkActions = document.querySelector('.bulk-actions');
    const selectedCount = document.getElementById('selected-count');
    
    if (bulkActions) {
        if (selectedCheckboxes.length > 0) {
            bulkActions.style.display = 'block';
            if (selectedCount) {
                selectedCount.textContent = selectedCheckboxes.length;
            }
        } else {
            bulkActions.style.display = 'none';
        }
    }
}

function getSelectedChargeIds() {
    const checkboxes = document.querySelectorAll('.charge-checkbox:checked');
    return Array.from(checkboxes).map(checkbox => checkbox.value);
}

function performBulkAction(action, chargeIds) {
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = '/charges/bulk-action/';
    
    const actionInput = document.createElement('input');
    actionInput.type = 'hidden';
    actionInput.name = 'action';
    actionInput.value = action;
    
    const idsInput = document.createElement('input');
    idsInput.type = 'hidden';
    idsInput.name = 'charge_ids';
    idsInput.value = chargeIds.join(',');
    
    const csrfInput = document.createElement('input');
    csrfInput.type = 'hidden';
    csrfInput.name = 'csrfmiddlewaretoken';
    csrfInput.value = document.querySelector('[name=csrfmiddlewaretoken]').value;
    
    form.appendChild(actionInput);
    form.appendChild(idsInput);
    form.appendChild(csrfInput);
    
    document.body.appendChild(form);
    form.submit();
}

// AJAX Functions for Charge Form
function loadExistingCharges(customerId, itemId) {
    const container = document.getElementById('existing-charges-display');
    if (!container) return;
    
    container.innerHTML = '<div class="text-center"><div class="spinner-border spinner-border-sm" role="status"></div> Loading...</div>';
    
    fetch(`/charges/ajax/get-charges/?customer_id=${customerId}&item_id=${itemId}`)
        .then(response => response.json())
        .then(data => {
            displayExistingCharges(data.charges);
        })
        .catch(error => {
            console.error('Error loading charges:', error);
            container.innerHTML = '<p class="text-danger">Error loading existing charges</p>';
        });
}

function displayExistingCharges(charges) {
    const container = document.getElementById('existing-charges-display');
    if (!container) return;
    
    if (charges.length === 0) {
        container.innerHTML = '<p class="text-muted">No existing charges found for this customer-item combination</p>';
        return;
    }
    
    let html = '<div class="list-group list-group-flush">';
    charges.forEach(charge => {
        const chargeTypeText = getChargeTypeText(charge.charge_type);
        const effectiveDate = new Date(charge.effective_date).toLocaleDateString();
        
        html += `
            <div class="list-group-item px-0">
                <div class="d-flex justify-content-between align-items-start">
                    <div>
                        <h6 class="mb-1">${chargeTypeText}</h6>
                        <small class="text-muted">Rate: $${charge.rate}</small>
                    </div>
                    <small class="text-muted">${effectiveDate}</small>
                </div>
            </div>
        `;
    });
    html += '</div>';
    
    container.innerHTML = html;
}

function clearExistingCharges() {
    const container = document.getElementById('existing-charges-display');
    if (container) {
        container.innerHTML = '<p class="text-muted">Select customer and item to view existing charges</p>';
    }
}

function getChargeTypeText(chargeType) {
    const chargeTypes = {
        'per_cbm_days': 'Per CBM/Days',
        'per_sqmts_days': 'Per SQMTS/Days',
        'per_weight_days': 'Per Weight/Days',
        'fixed': 'Fixed',
        'weekly': 'Weekly',
        'monthly': 'Monthly'
    };
    return chargeTypes[chargeType] || chargeType;
}

function updateRatePlaceholder(chargeType) {
    const rateInput = document.getElementById('rate-input');
    if (!rateInput) return;
    
    const placeholders = {
        'per_cbm_days': 'Rate per cubic meter per day',
        'per_sqmts_days': 'Rate per square meters per day',
        'per_weight_days': 'Rate per weight unit per day',
        'fixed': 'Fixed amount',
        'weekly': 'Rate per week',
        'monthly': 'Rate per month'
    };
    
    rateInput.placeholder = placeholders[chargeType] || 'Enter rate';
}

// Utility Functions
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// Search functionality
const searchInputs = document.querySelectorAll('.search-input');
searchInputs.forEach(input => {
    input.addEventListener('input', debounce(function() {
        // Trigger search form submission
        const form = this.closest('form');
        if (form) {
            form.submit();
        }
    }, 500));
});

// Auto-save functionality for forms
const autoSaveForms = document.querySelectorAll('.auto-save');
autoSaveForms.forEach(form => {
    const inputs = form.querySelectorAll('input, select, textarea');
    inputs.forEach(input => {
        input.addEventListener('change', debounce(function() {
            // Auto-save logic can be implemented here
            console.log('Auto-saving form...');
        }, 1000));
    });
}); 