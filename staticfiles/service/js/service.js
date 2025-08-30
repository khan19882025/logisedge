// Service Module JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize service module
    initServiceModule();
});

function initServiceModule() {
    // Form validation
    initFormValidation();
    
    // Search functionality
    initSearchFunctionality();
    
    // Price formatting
    initPriceFormatting();
    
    // Auto-save functionality
    initAutoSave();
}

function initFormValidation() {
    const forms = document.querySelectorAll('.service-form');
    
    forms.forEach(form => {
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
        
        // Form submission validation
        form.addEventListener('submit', function(e) {
            if (!validateForm(this)) {
                e.preventDefault();
                showFormErrors(this);
            }
        });
    });
}

function validateField(field) {
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
        case 'service_name':
            if (value && value.length < 3) {
                showFieldError(field, 'Service name must be at least 3 characters long.');
                return false;
            }
            break;
            
        case 'base_price':
            if (value && parseFloat(value) < 0) {
                showFieldError(field, 'Base price cannot be negative.');
                return false;
            }
            break;
            
        case 'currency':
            if (value && value.length !== 3) {
                showFieldError(field, 'Currency code must be exactly 3 characters.');
                return false;
            }
            break;
            
        case 'description':
            if (value && value.length < 10) {
                showFieldError(field, 'Description must be at least 10 characters long.');
                return false;
            }
            break;
    }
    
    return true;
}

function showFieldError(field, message) {
    // Add error class
    field.classList.add('is-invalid');
    
    // Create or update error message
    let errorDiv = field.parentNode.querySelector('.invalid-feedback');
    if (!errorDiv) {
        errorDiv = document.createElement('div');
        errorDiv.className = 'invalid-feedback';
        field.parentNode.appendChild(errorDiv);
    }
    errorDiv.textContent = message;
}

function clearFieldError(field) {
    field.classList.remove('is-invalid');
    field.classList.add('is-valid');
    
    const errorDiv = field.parentNode.querySelector('.invalid-feedback');
    if (errorDiv) {
        errorDiv.remove();
    }
}

function validateForm(form) {
    const inputs = form.querySelectorAll('input, select, textarea');
    let isValid = true;
    
    inputs.forEach(input => {
        if (!validateField(input)) {
            isValid = false;
        }
    });
    
    return isValid;
}

function showFormErrors(form) {
    // Scroll to first error
    const firstError = form.querySelector('.is-invalid');
    if (firstError) {
        firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
        firstError.focus();
    }
    
    // Show toast notification
    showToast('Please correct the errors in the form.', 'error');
}

function initSearchFunctionality() {
    const searchForm = document.querySelector('.service-search-form');
    if (!searchForm) return;
    
    const searchInput = searchForm.querySelector('input[name="search"]');
    const filters = searchForm.querySelectorAll('select');
    
    // Debounced search
    let searchTimeout;
    searchInput.addEventListener('input', function() {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            searchForm.submit();
        }, 500);
    });
    
    // Auto-submit on filter change
    filters.forEach(filter => {
        filter.addEventListener('change', function() {
            searchForm.submit();
        });
    });
}

function initPriceFormatting() {
    const priceInputs = document.querySelectorAll('input[name="base_price"]');
    
    priceInputs.forEach(input => {
        input.addEventListener('blur', function() {
            const value = parseFloat(this.value);
            if (!isNaN(value)) {
                this.value = value.toFixed(2);
            }
        });
        
        input.addEventListener('input', function() {
            // Allow only numbers and decimal point
            this.value = this.value.replace(/[^0-9.]/g, '');
            
            // Ensure only one decimal point
            const parts = this.value.split('.');
            if (parts.length > 2) {
                this.value = parts[0] + '.' + parts.slice(1).join('');
            }
        });
    });
}

function initAutoSave() {
    const forms = document.querySelectorAll('.service-form');
    
    forms.forEach(form => {
        const inputs = form.querySelectorAll('input, select, textarea');
        let autoSaveTimeout;
        
        inputs.forEach(input => {
            input.addEventListener('input', function() {
                clearTimeout(autoSaveTimeout);
                autoSaveTimeout = setTimeout(() => {
                    autoSaveForm(form);
                }, 2000); // Auto-save after 2 seconds of inactivity
            });
        });
    });
}

function autoSaveForm(form) {
    const formData = new FormData(form);
    const serviceId = form.querySelector('input[name="service_id"]')?.value;
    
    // Show saving indicator
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalText = submitBtn.textContent;
    submitBtn.textContent = 'Saving...';
    submitBtn.disabled = true;
    
    // Simulate auto-save (in real implementation, this would be an AJAX call)
    setTimeout(() => {
        submitBtn.textContent = originalText;
        submitBtn.disabled = false;
        showToast('Form auto-saved successfully.', 'success');
    }, 1000);
}

function showToast(message, type = 'info') {
    // Create toast container if it doesn't exist
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
        toastContainer.style.zIndex = '9999';
        document.body.appendChild(toastContainer);
    }
    
    // Create toast
    const toastId = 'toast-' + Date.now();
    const toastHtml = `
        <div id="${toastId}" class="toast" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="toast-header">
                <strong class="me-auto">Service Module</strong>
                <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        </div>
    `;
    
    toastContainer.insertAdjacentHTML('beforeend', toastHtml);
    
    // Show toast
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement);
    toast.show();
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (toastElement.parentNode) {
            toastElement.remove();
        }
    }, 5000);
}

// Service-specific functions
function toggleServiceStatus(serviceId, currentStatus) {
    const newStatus = currentStatus === 'active' ? 'inactive' : 'active';
    
    // Show confirmation dialog
    if (confirm(`Are you sure you want to ${newStatus === 'active' ? 'activate' : 'deactivate'} this service?`)) {
        // In real implementation, this would be an AJAX call
        showToast(`Service status updated to ${newStatus}.`, 'success');
        
        // Update UI
        const statusBadge = document.querySelector(`[data-service-id="${serviceId}"] .status-badge`);
        if (statusBadge) {
            statusBadge.textContent = newStatus.charAt(0).toUpperCase() + newStatus.slice(1);
            statusBadge.className = `badge ${newStatus === 'active' ? 'bg-success' : 'bg-secondary'} status-badge`;
        }
    }
}

function duplicateService(serviceId) {
    if (confirm('Are you sure you want to duplicate this service?')) {
        // In real implementation, this would redirect to create form with pre-filled data
        window.location.href = `/service/create/?duplicate=${serviceId}`;
    }
}

// Export functions for global access
window.ServiceModule = {
    toggleServiceStatus,
    duplicateService,
    showToast,
    validateForm,
    validateField
}; 