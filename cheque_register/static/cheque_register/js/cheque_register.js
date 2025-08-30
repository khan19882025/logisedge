// Cheque Register JavaScript

document.addEventListener('DOMContentLoaded', function() {
    initializeChequeRegister();
});

function initializeChequeRegister() {
    // Initialize form functionality
    initializeForms();
    
    // Initialize dynamic party selection
    initializePartySelection();
    
    // Initialize status change functionality
    initializeStatusChanges();
    
    // Initialize bulk actions
    initializeBulkActions();
    
    // Initialize alerts
    initializeAlerts();
}

// Form Initialization
function initializeForms() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        // Add validation
        form.addEventListener('submit', handleFormSubmit);
        
        // Add real-time validation
        const inputs = form.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            input.addEventListener('blur', validateField);
            input.addEventListener('input', clearFieldError);
        });
    });
}

// Party Selection Functionality
function initializePartySelection() {
    const partyTypeSelect = document.querySelector('select[name="party_type"]');
    const customerSelect = document.querySelector('select[name="customer"]');
    const supplierSelect = document.querySelector('select[name="supplier"]');
    
    if (partyTypeSelect) {
        partyTypeSelect.addEventListener('change', function() {
            const partyType = this.value;
            
            // Hide both selects initially
            if (customerSelect) customerSelect.style.display = 'none';
            if (supplierSelect) supplierSelect.style.display = 'none';
            
            // Show relevant select
            if (partyType === 'customer' && customerSelect) {
                customerSelect.style.display = 'block';
                customerSelect.required = true;
                if (supplierSelect) supplierSelect.required = false;
            } else if (partyType === 'supplier' && supplierSelect) {
                supplierSelect.style.display = 'block';
                supplierSelect.required = true;
                if (customerSelect) customerSelect.required = false;
            }
        });
        
        // Trigger change event on load
        partyTypeSelect.dispatchEvent(new Event('change'));
    }
}

// Status Change Functionality
function initializeStatusChanges() {
    const statusChangeForms = document.querySelectorAll('.status-change-form');
    
    statusChangeForms.forEach(form => {
        form.addEventListener('submit', handleStatusChange);
    });
}

// Bulk Actions Functionality
function initializeBulkActions() {
    const selectAllCheckbox = document.getElementById('selectAll');
    const chequeCheckboxes = document.querySelectorAll('.cheque-checkbox');
    const bulkActionsDiv = document.getElementById('bulkActions');
    
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function() {
            chequeCheckboxes.forEach(checkbox => {
                checkbox.checked = this.checked;
            });
            updateBulkActionsVisibility();
        });
    }
    
    chequeCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            updateBulkActionsVisibility();
            updateSelectAllState();
        });
    });
}

// Alert Functionality
function initializeAlerts() {
    const alertCloseButtons = document.querySelectorAll('.alert-close');
    
    alertCloseButtons.forEach(button => {
        button.addEventListener('click', function() {
            const alert = this.closest('.alert');
            if (alert) {
                alert.remove();
            }
        });
    });
}

// Form Submission Handler
function handleFormSubmit(event) {
    const form = event.target;
    const submitButton = form.querySelector('button[type="submit"]');
    
    if (!validateForm(form)) {
        event.preventDefault();
        return false;
    }
    
    // Show loading state
    if (submitButton) {
        const originalText = submitButton.innerHTML;
        submitButton.innerHTML = '<span class="spinner"></span> Processing...';
        submitButton.disabled = true;
        
        // Re-enable after a delay (in case of validation errors)
        setTimeout(() => {
            submitButton.innerHTML = originalText;
            submitButton.disabled = false;
        }, 5000);
    }
}

// Field Validation
function validateField(event) {
    const field = event.target;
    const value = field.value.trim();
    const fieldName = field.name;
    
    // Clear previous errors
    clearFieldError(field);
    
    // Required field validation
    if (field.hasAttribute('required') && !value) {
        showFieldError(field, 'This field is required.');
        return false;
    }
    
    // Specific field validations
    switch (fieldName) {
        case 'cheque_number':
            if (value && value.length < 3) {
                showFieldError(field, 'Cheque number must be at least 3 characters.');
                return false;
            }
            break;
            
        case 'amount':
            if (value && (isNaN(value) || parseFloat(value) <= 0)) {
                showFieldError(field, 'Please enter a valid amount greater than 0.');
                return false;
            }
            break;
            
        case 'cheque_date':
            if (value) {
                const selectedDate = new Date(value);
                const today = new Date();
                today.setHours(0, 0, 0, 0);
                
                if (selectedDate < today) {
                    // Allow past dates but show warning
                    showFieldWarning(field, 'This is a past date. Please verify.');
                }
            }
            break;
    }
    
    return true;
}

// Form Validation
function validateForm(form) {
    const requiredFields = form.querySelectorAll('[required]');
    let isValid = true;
    
    requiredFields.forEach(field => {
        if (!validateField({ target: field })) {
            isValid = false;
        }
    });
    
    return isValid;
}

// Error Display Functions
function showFieldError(field, message) {
    clearFieldError(field);
    
    field.classList.add('is-invalid');
    
    const errorDiv = document.createElement('div');
    errorDiv.className = 'invalid-feedback';
    errorDiv.textContent = message;
    
    field.parentNode.appendChild(errorDiv);
}

function showFieldWarning(field, message) {
    clearFieldWarning(field);
    
    field.classList.add('is-warning');
    
    const warningDiv = document.createElement('div');
    warningDiv.className = 'warning-feedback';
    warningDiv.textContent = message;
    warningDiv.style.color = '#f59e0b';
    warningDiv.style.fontSize = '0.75rem';
    warningDiv.style.marginTop = '0.25rem';
    
    field.parentNode.appendChild(warningDiv);
}

function clearFieldError(field) {
    field.classList.remove('is-invalid');
    const errorDiv = field.parentNode.querySelector('.invalid-feedback');
    if (errorDiv) {
        errorDiv.remove();
    }
}

function clearFieldWarning(field) {
    field.classList.remove('is-warning');
    const warningDiv = field.parentNode.querySelector('.warning-feedback');
    if (warningDiv) {
        warningDiv.remove();
    }
}

// Status Change Handler
function handleStatusChange(event) {
    event.preventDefault();
    
    const form = event.target;
    const formData = new FormData(form);
    const submitButton = form.querySelector('button[type="submit"]');
    
    if (submitButton) {
        submitButton.innerHTML = '<span class="spinner"></span> Updating...';
        submitButton.disabled = true;
    }
    
    fetch(form.action, {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': getCSRFToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('Status updated successfully!', 'success');
            setTimeout(() => {
                window.location.reload();
            }, 1500);
        } else {
            showAlert(data.error || 'Failed to update status.', 'danger');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('An error occurred while updating status.', 'danger');
    })
    .finally(() => {
        if (submitButton) {
            submitButton.innerHTML = 'Update Status';
            submitButton.disabled = false;
        }
    });
}

// Bulk Actions Functions
function updateBulkActionsVisibility() {
    const selectedCheckboxes = document.querySelectorAll('.cheque-checkbox:checked');
    const bulkActionsDiv = document.getElementById('bulkActions');
    const selectedCountSpan = document.getElementById('selectedCount');
    
    if (bulkActionsDiv) {
        if (selectedCheckboxes.length > 0) {
            bulkActionsDiv.classList.add('show');
            if (selectedCountSpan) {
                selectedCountSpan.textContent = `${selectedCheckboxes.length} cheque(s) selected`;
            }
        } else {
            bulkActionsDiv.classList.remove('show');
        }
    }
}

function updateSelectAllState() {
    const selectAllCheckbox = document.getElementById('selectAll');
    const chequeCheckboxes = document.querySelectorAll('.cheque-checkbox');
    const checkedCheckboxes = document.querySelectorAll('.cheque-checkbox:checked');
    
    if (selectAllCheckbox) {
        if (checkedCheckboxes.length === 0) {
            selectAllCheckbox.checked = false;
            selectAllCheckbox.indeterminate = false;
        } else if (checkedCheckboxes.length === chequeCheckboxes.length) {
            selectAllCheckbox.checked = true;
            selectAllCheckbox.indeterminate = false;
        } else {
            selectAllCheckbox.checked = false;
            selectAllCheckbox.indeterminate = true;
        }
    }
}

function clearSelection() {
    const selectAllCheckbox = document.getElementById('selectAll');
    const chequeCheckboxes = document.querySelectorAll('.cheque-checkbox');
    
    if (selectAllCheckbox) {
        selectAllCheckbox.checked = false;
        selectAllCheckbox.indeterminate = false;
    }
    
    chequeCheckboxes.forEach(checkbox => {
        checkbox.checked = false;
    });
    
    updateBulkActionsVisibility();
}

// AJAX Functions
function getPartySuggestions(partyType, searchTerm) {
    return fetch(`/accounting/cheque-register/ajax/party-suggestions/?party_type=${partyType}&q=${encodeURIComponent(searchTerm)}`)
        .then(response => response.json())
        .then(data => data.results)
        .catch(error => {
            console.error('Error fetching party suggestions:', error);
            return [];
        });
}

// Utility Functions
function getCSRFToken() {
    const token = document.querySelector('[name=csrfmiddlewaretoken]');
    return token ? token.value : '';
}

function showAlert(message, type = 'info') {
    const alertContainer = document.getElementById('alertContainer') || createAlertContainer();
    
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    alertContainer.appendChild(alertDiv);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}

function createAlertContainer() {
    const container = document.createElement('div');
    container.id = 'alertContainer';
    container.style.position = 'fixed';
    container.style.top = '20px';
    container.style.right = '20px';
    container.style.zIndex = '9999';
    container.style.maxWidth = '400px';
    
    document.body.appendChild(container);
    return container;
}

// Date Utilities
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

function isOverdue(dateString) {
    const chequeDate = new Date(dateString);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    
    return chequeDate < today;
}

function getDaysOverdue(dateString) {
    const chequeDate = new Date(dateString);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    
    const diffTime = today - chequeDate;
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    return diffDays > 0 ? diffDays : 0;
}

// Export Functions
function exportCheques(format = 'csv') {
    const currentUrl = new URL(window.location);
    currentUrl.searchParams.set('export', format);
    
    window.location.href = currentUrl.toString();
}

// Modal Functions
function showModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('show');
        modal.style.display = 'block';
        
        // Add backdrop
        const backdrop = document.createElement('div');
        backdrop.className = 'modal-backdrop fade show';
        backdrop.id = 'modalBackdrop';
        document.body.appendChild(backdrop);
        
        // Prevent body scroll
        document.body.style.overflow = 'hidden';
    }
}

function hideModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('show');
        modal.style.display = 'none';
        
        // Remove backdrop
        const backdrop = document.getElementById('modalBackdrop');
        if (backdrop) {
            backdrop.remove();
        }
        
        // Restore body scroll
        document.body.style.overflow = '';
    }
}

// Keyboard Shortcuts
document.addEventListener('keydown', function(event) {
    // Ctrl/Cmd + N for new cheque
    if ((event.ctrlKey || event.metaKey) && event.key === 'n') {
        event.preventDefault();
        const newChequeLink = document.querySelector('a[href*="cheque_create"]');
        if (newChequeLink) {
            newChequeLink.click();
        }
    }
    
    // Ctrl/Cmd + F for search
    if ((event.ctrlKey || event.metaKey) && event.key === 'f') {
        event.preventDefault();
        const searchInput = document.querySelector('input[name="search"]');
        if (searchInput) {
            searchInput.focus();
        }
    }
    
    // Escape to close modals
    if (event.key === 'Escape') {
        const openModal = document.querySelector('.modal.show');
        if (openModal) {
            hideModal(openModal.id);
        }
    }
});

// Auto-save functionality for forms
function initializeAutoSave() {
    const forms = document.querySelectorAll('form[data-autosave]');
    
    forms.forEach(form => {
        const inputs = form.querySelectorAll('input, select, textarea');
        let autoSaveTimeout;
        
        inputs.forEach(input => {
            input.addEventListener('input', function() {
                clearTimeout(autoSaveTimeout);
                autoSaveTimeout = setTimeout(() => {
                    saveFormData(form);
                }, 2000); // Save after 2 seconds of inactivity
            });
        });
    });
}

function saveFormData(form) {
    const formData = new FormData(form);
    const formId = form.getAttribute('data-form-id') || 'cheque_form';
    
    // Save to localStorage
    const formObject = {};
    for (let [key, value] of formData.entries()) {
        formObject[key] = value;
    }
    
    localStorage.setItem(`cheque_form_${formId}`, JSON.stringify(formObject));
    
    // Show auto-save indicator
    showAutoSaveIndicator();
}

function loadFormData(form) {
    const formId = form.getAttribute('data-form-id') || 'cheque_form';
    const savedData = localStorage.getItem(`cheque_form_${formId}`);
    
    if (savedData) {
        const formObject = JSON.parse(savedData);
        
        Object.keys(formObject).forEach(key => {
            const field = form.querySelector(`[name="${key}"]`);
            if (field) {
                field.value = formObject[key];
            }
        });
    }
}

function showAutoSaveIndicator() {
    const indicator = document.getElementById('autoSaveIndicator') || createAutoSaveIndicator();
    indicator.textContent = 'Auto-saved';
    indicator.style.opacity = '1';
    
    setTimeout(() => {
        indicator.style.opacity = '0';
    }, 2000);
}

function createAutoSaveIndicator() {
    const indicator = document.createElement('div');
    indicator.id = 'autoSaveIndicator';
    indicator.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        background: #10b981;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 0.5rem;
        font-size: 0.875rem;
        opacity: 0;
        transition: opacity 0.3s ease;
        z-index: 9999;
    `;
    
    document.body.appendChild(indicator);
    return indicator;
}

// Initialize auto-save if enabled
if (document.querySelector('form[data-autosave]')) {
    initializeAutoSave();
} 