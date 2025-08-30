// Freight Quotation Module JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all components
    initializeFormValidation();
    initializeAutoCalculation();
    initializeSearchFilters();
    initializeModalHandlers();
    initializeTooltips();
    initializeDataTables();
});

// Form Validation
function initializeFormValidation() {
    const forms = document.querySelectorAll('form[data-validate]');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!validateForm(this)) {
                e.preventDefault();
                showAlert('Please correct the errors before submitting.', 'error');
            }
        });
    });
}

function validateForm(form) {
    let isValid = true;
    const requiredFields = form.querySelectorAll('[required]');
    
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            markFieldAsInvalid(field, 'This field is required.');
            isValid = false;
        } else {
            markFieldAsValid(field);
        }
    });
    
    // Validate email fields
    const emailFields = form.querySelectorAll('input[type="email"]');
    emailFields.forEach(field => {
        if (field.value && !isValidEmail(field.value)) {
            markFieldAsInvalid(field, 'Please enter a valid email address.');
            isValid = false;
        }
    });
    
    // Validate numeric fields
    const numericFields = form.querySelectorAll('input[type="number"]');
    numericFields.forEach(field => {
        if (field.value && isNaN(field.value)) {
            markFieldAsInvalid(field, 'Please enter a valid number.');
            isValid = false;
        }
    });
    
    return isValid;
}

function markFieldAsInvalid(field, message) {
    field.classList.add('is-invalid');
    field.classList.remove('is-valid');
    
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

function markFieldAsValid(field) {
    field.classList.remove('is-invalid');
    field.classList.add('is-valid');
    
    // Remove error message
    const existingError = field.parentNode.querySelector('.invalid-feedback');
    if (existingError) {
        existingError.remove();
    }
}

function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

// Auto Calculation for Charges
function initializeAutoCalculation() {
    const chargeForms = document.querySelectorAll('.charge-form');
    
    chargeForms.forEach(form => {
        const rateField = form.querySelector('input[name="rate"]');
        const quantityField = form.querySelector('input[name="quantity"]');
        const totalField = form.querySelector('input[name="total_amount"]');
        
        if (rateField && quantityField && totalField) {
            [rateField, quantityField].forEach(field => {
                field.addEventListener('input', function() {
                    calculateChargeTotal(rateField, quantityField, totalField);
                });
            });
        }
    });
}

function calculateChargeTotal(rateField, quantityField, totalField) {
    const rate = parseFloat(rateField.value) || 0;
    const quantity = parseFloat(quantityField.value) || 0;
    const total = rate * quantity;
    
    totalField.value = total.toFixed(2);
    totalField.dispatchEvent(new Event('change'));
}

// Search and Filter Functionality
function initializeSearchFilters() {
    const searchForm = document.getElementById('search-form');
    if (searchForm) {
        const inputs = searchForm.querySelectorAll('input, select');
        
        inputs.forEach(input => {
            input.addEventListener('change', function() {
                // Add loading state
                addLoadingState(searchForm);
                
                // Submit form after a short delay
                setTimeout(() => {
                    searchForm.submit();
                }, 300);
            });
        });
    }
}

function addLoadingState(element) {
    element.classList.add('loading');
    element.style.pointerEvents = 'none';
}

function removeLoadingState(element) {
    element.classList.remove('loading');
    element.style.pointerEvents = 'auto';
}

// Modal Handlers
function initializeModalHandlers() {
    // Delete confirmation modal
    const deleteButtons = document.querySelectorAll('[data-delete-url]');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const url = this.getAttribute('data-delete-url');
            const itemName = this.getAttribute('data-item-name');
            showDeleteConfirmation(url, itemName);
        });
    });
    
    // Status change modal
    const statusButtons = document.querySelectorAll('[data-status-url]');
    statusButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const url = this.getAttribute('data-status-url');
            const currentStatus = this.getAttribute('data-current-status');
            showStatusChangeModal(url, currentStatus);
        });
    });
}

function showDeleteConfirmation(url, itemName) {
    const modal = new bootstrap.Modal(document.getElementById('deleteModal'));
    document.getElementById('deleteModalLabel').textContent = 'Confirm Delete';
    document.getElementById('deleteModalBody').innerHTML = `
        <p>Are you sure you want to delete <strong>${itemName}</strong>?</p>
        <p class="text-danger">This action cannot be undone.</p>
    `;
    document.getElementById('deleteConfirmBtn').href = url;
    modal.show();
}

function showStatusChangeModal(url, currentStatus) {
    const modal = new bootstrap.Modal(document.getElementById('statusModal'));
    document.getElementById('statusModalLabel').textContent = 'Change Status';
    document.getElementById('currentStatus').textContent = currentStatus;
    document.getElementById('statusForm').action = url;
    modal.show();
}

// Tooltips
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Data Tables (if using Bootstrap tables)
function initializeDataTables() {
    const tables = document.querySelectorAll('.table-sortable');
    
    tables.forEach(table => {
        const headers = table.querySelectorAll('th[data-sort]');
        
        headers.forEach(header => {
            header.addEventListener('click', function() {
                const column = this.getAttribute('data-sort');
                const direction = this.getAttribute('data-direction') === 'asc' ? 'desc' : 'asc';
                
                // Update all headers
                headers.forEach(h => h.setAttribute('data-direction', ''));
                this.setAttribute('data-direction', direction);
                
                // Sort table
                sortTable(table, column, direction);
            });
        });
    });
}

function sortTable(table, column, direction) {
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    
    rows.sort((a, b) => {
        const aValue = a.querySelector(`td[data-${column}]`).getAttribute(`data-${column}`);
        const bValue = b.querySelector(`td[data-${column}]`).getAttribute(`data-${column}`);
        
        if (direction === 'asc') {
            return aValue.localeCompare(bValue);
        } else {
            return bValue.localeCompare(aValue);
        }
    });
    
    // Reorder rows
    rows.forEach(row => tbody.appendChild(row));
}

// Alert System
function showAlert(message, type = 'info', duration = 5000) {
    const alertContainer = document.getElementById('alert-container') || createAlertContainer();
    
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    alertContainer.appendChild(alertDiv);
    
    // Auto dismiss after duration
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, duration);
}

function createAlertContainer() {
    const container = document.createElement('div');
    container.id = 'alert-container';
    container.style.position = 'fixed';
    container.style.top = '20px';
    container.style.right = '20px';
    container.style.zIndex = '9999';
    container.style.maxWidth = '400px';
    document.body.appendChild(container);
    return container;
}

// AJAX Functions
function fetchCustomerDetails(customerId) {
    return fetch(`/freight-quotation/ajax/customer/${customerId}/`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .catch(error => {
            console.error('Error fetching customer details:', error);
            showAlert('Error loading customer details', 'error');
        });
}

function updateCustomerFields(customerData) {
    const fields = ['email', 'phone', 'address', 'country'];
    
    fields.forEach(field => {
        const element = document.getElementById(`customer_${field}`);
        if (element && customerData[field]) {
            element.value = customerData[field];
        }
    });
}

// PDF Generation (placeholder)
function generatePDF(quotationId) {
    showAlert('Generating PDF...', 'info');
    
    // This would typically make an AJAX call to generate PDF
    fetch(`/freight-quotation/${quotationId}/pdf/`)
        .then(response => response.blob())
        .then(blob => {
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `quotation-${quotationId}.pdf`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            showAlert('PDF downloaded successfully!', 'success');
        })
        .catch(error => {
            console.error('Error generating PDF:', error);
            showAlert('Error generating PDF', 'error');
        });
}

// Email Functionality (placeholder)
function sendQuotationEmail(quotationId) {
    showAlert('Sending email...', 'info');
    
    // This would typically make an AJAX call to send email
    fetch(`/freight-quotation/${quotationId}/send-email/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json',
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('Email sent successfully!', 'success');
        } else {
            showAlert(data.error || 'Error sending email', 'error');
        }
    })
    .catch(error => {
        console.error('Error sending email:', error);
        showAlert('Error sending email', 'error');
    });
}

// Utility Functions
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

function formatCurrency(amount, currency = 'AED') {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: currency
    }).format(amount);
}

function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

// Export functions for global use
window.FreightQuotation = {
    showAlert,
    generatePDF,
    sendQuotationEmail,
    fetchCustomerDetails,
    updateCustomerFields,
    formatCurrency,
    formatDate
}; 