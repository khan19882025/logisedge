// Tax Settings App JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize form validation
    initializeFormValidation();
    
    // Initialize search functionality
    initializeSearch();
    
    // Initialize tooltips
    initializeTooltips();
    
    // Initialize date pickers
    initializeDatePickers();
    
    // Initialize AJAX functionality
    initializeAjax();
});

// Form validation
function initializeFormValidation() {
    const forms = document.querySelectorAll('.needs-validation');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });
}

// Search functionality
function initializeSearch() {
    const searchInput = document.querySelector('input[name="search"]');
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

// Tooltips
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Date pickers
function initializeDatePickers() {
    const dateInputs = document.querySelectorAll('input[type="date"]');
    dateInputs.forEach(input => {
        if (!input.value) {
            input.value = new Date().toISOString().split('T')[0];
        }
    });
}

// AJAX functionality
function initializeAjax() {
    // Tax rate calculation
    const taxCalculationForm = document.getElementById('tax-calculation-form');
    if (taxCalculationForm) {
        taxCalculationForm.addEventListener('submit', handleTaxCalculation);
    }
    
    // Dynamic tax rate loading
    const jurisdictionSelect = document.getElementById('id_jurisdiction');
    if (jurisdictionSelect) {
        jurisdictionSelect.addEventListener('change', loadTaxRatesByJurisdiction);
    }
}

// Handle tax calculation
function handleTaxCalculation(event) {
    event.preventDefault();
    
    const form = event.target;
    const formData = new FormData(form);
    const submitButton = form.querySelector('button[type="submit"]');
    const resultDiv = document.getElementById('tax-calculation-result');
    
    // Show loading state
    submitButton.disabled = true;
    submitButton.innerHTML = '<i class="bi bi-hourglass-split me-2"></i>Calculating...';
    
    fetch(form.action, {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            displayTaxCalculationResult(data);
        } else {
            displayTaxCalculationError(data.error);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        displayTaxCalculationError('An error occurred while calculating tax.');
    })
    .finally(() => {
        // Reset button state
        submitButton.disabled = false;
        submitButton.innerHTML = '<i class="bi bi-calculator me-2"></i>Calculate Tax';
    });
}

// Display tax calculation result
function displayTaxCalculationResult(data) {
    const resultDiv = document.getElementById('tax-calculation-result');
    if (resultDiv) {
        resultDiv.innerHTML = `
            <div class="alert alert-success">
                <h5 class="alert-heading">Tax Calculation Result</h5>
                <div class="row">
                    <div class="col-md-6">
                        <p><strong>Taxable Amount:</strong> ${data.taxable_amount}</p>
                        <p><strong>Tax Rate:</strong> ${data.tax_rate}%</p>
                    </div>
                    <div class="col-md-6">
                        <p><strong>Tax Amount:</strong> ${data.tax_amount}</p>
                        <p><strong>Total Amount:</strong> ${data.total_amount}</p>
                    </div>
                </div>
            </div>
        `;
        resultDiv.scrollIntoView({ behavior: 'smooth' });
    }
}

// Display tax calculation error
function displayTaxCalculationError(error) {
    const resultDiv = document.getElementById('tax-calculation-result');
    if (resultDiv) {
        resultDiv.innerHTML = `
            <div class="alert alert-danger">
                <h5 class="alert-heading">Calculation Error</h5>
                <p>${error}</p>
            </div>
        `;
        resultDiv.scrollIntoView({ behavior: 'smooth' });
    }
}

// Load tax rates by jurisdiction
function loadTaxRatesByJurisdiction(event) {
    const jurisdictionId = event.target.value;
    const taxRateSelect = document.getElementById('id_default_tax_rate');
    
    if (!jurisdictionId || !taxRateSelect) return;
    
    // Show loading state
    taxRateSelect.disabled = true;
    taxRateSelect.innerHTML = '<option>Loading...</option>';
    
    fetch(`/tax-settings/api/tax-rates-by-jurisdiction/?jurisdiction_id=${jurisdictionId}`)
        .then(response => response.json())
        .then(data => {
            taxRateSelect.innerHTML = '<option value="">Select Tax Rate</option>';
            data.tax_rates.forEach(rate => {
                const option = document.createElement('option');
                option.value = rate.id;
                option.textContent = `${rate.name} (${rate.rate}%)`;
                taxRateSelect.appendChild(option);
            });
        })
        .catch(error => {
            console.error('Error loading tax rates:', error);
            taxRateSelect.innerHTML = '<option value="">Error loading tax rates</option>';
        })
        .finally(() => {
            taxRateSelect.disabled = false;
        });
}

// Confirm delete
function confirmDelete(message = 'Are you sure you want to delete this item?') {
    return confirm(message);
}

// Show notification
function showNotification(message, type = 'info') {
    const notificationDiv = document.createElement('div');
    notificationDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    notificationDiv.style.cssText = 'top: 20px; right: 20px; z-index: 1050; min-width: 300px;';
    notificationDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(notificationDiv);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (notificationDiv.parentNode) {
            notificationDiv.remove();
        }
    }, 5000);
}

// Export functionality
function exportTaxData(format = 'csv') {
    const currentUrl = new URL(window.location);
    currentUrl.searchParams.set('export', format);
    
    window.location.href = currentUrl.toString();
}

// Print functionality
function printTaxReport() {
    window.print();
}

// Keyboard shortcuts
document.addEventListener('keydown', function(event) {
    // Ctrl/Cmd + N for new tax rate
    if ((event.ctrlKey || event.metaKey) && event.key === 'n') {
        event.preventDefault();
        const newButton = document.querySelector('a[href*="create"]');
        if (newButton) {
            newButton.click();
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
    
    // Escape key to close modals
    if (event.key === 'Escape') {
        const modals = document.querySelectorAll('.modal.show');
        modals.forEach(modal => {
            const modalInstance = bootstrap.Modal.getInstance(modal);
            if (modalInstance) {
                modalInstance.hide();
            }
        });
    }
});

// Utility functions
function formatCurrency(amount, currency = 'AED') {
    return new Intl.NumberFormat('en-AE', {
        style: 'currency',
        currency: currency
    }).format(amount);
}

function formatPercentage(value) {
    return `${value}%`;
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-AE', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

// Initialize when DOM is loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeTaxSettings);
} else {
    initializeTaxSettings();
}

function initializeTaxSettings() {
    // Additional initialization code can be added here
    console.log('Tax Settings app initialized');
}
