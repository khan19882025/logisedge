/**
 * Balance Sheet Report JavaScript
 * Handles interactivity and functionality for the balance sheet report
 */

console.log('Balance Sheet JavaScript loaded successfully!');

document.addEventListener('DOMContentLoaded', function() {
    // Initialize the balance sheet functionality
    initBalanceSheet();
});

function initBalanceSheet() {
    console.log('Initializing Balance Sheet...');
    
    // Add AJAX form submission
    const form = document.getElementById('balanceSheetForm');
    console.log('Looking for form with ID balanceSheetForm:', form);
    
    // Also check for forms by method
    const formsByMethod = document.querySelectorAll('form[method="post"]');
    console.log('Forms with method="post":', formsByMethod);
    
    if (form) {
        console.log('Form found, adding submit listener');
        form.addEventListener('submit', function(e) {
            console.log('Form submitted, processing with AJAX');
            e.preventDefault(); // Prevent normal form submission
            
            // Submit form via AJAX
            submitFormAjax(this);
        });
    } else {
        console.log('Form not found');
    }

    // Initialize tooltips
    initTooltips();

    // Initialize form validation
    initFormValidation();

    // Initialize export modal functionality
    initExportModal();

    // Initialize print functionality
    initPrintFunctionality();

    // Initialize responsive behavior
    initResponsiveBehavior();

    // Initialize accessibility features
    initAccessibility();
}

/**
 * Get CSRF token from cookie
 */
function getCSRFToken() {
    const name = 'csrftoken';
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

/**
 * Submit form via AJAX
 */
function submitFormAjax(form) {
    console.log('Submitting form via AJAX...');
    
    const formData = new FormData(form);
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    
    // Show loading state
    submitBtn.innerHTML = '<i class="bi bi-hourglass-split me-1"></i> Generating...';
    submitBtn.disabled = true;
    
    // Add AJAX header
    formData.append('ajax', 'true');
    
    console.log('Form data:', Object.fromEntries(formData));
    
    // Get CSRF token
    const csrfToken = getCSRFToken();
    
    // Make AJAX request
    console.log('Making fetch request with headers:', {
        'X-Requested-With': 'XMLHttpRequest',
        'X-CSRFToken': csrfToken
    });
    
    // Try fetch first, fallback to XMLHttpRequest if needed
    try {
        fetch(window.location.href, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': csrfToken
            }
        })
        .then(response => {
            console.log('Response received:', response);
            return response.json();
        })
        .then(data => {
            console.log('Data received:', data);
            if (data.success) {
                // Show success message
                showSuccessMessage(data.message || 'Report generated successfully!');
                
                // Update the page with report data
                updateReportDisplay(data);
                
                // Scroll to report section
                const reportSection = document.querySelector('.balance-sheet-professional');
                if (reportSection) {
                    reportSection.scrollIntoView({ behavior: 'smooth' });
                }
            } else {
                // Show error message
                showErrorMessage(data.error || 'Error generating report');
                
                // Show form errors if any
                if (data.form_errors) {
                    showFormErrors(data.form_errors);
                }
            }
        })
        .catch(error => {
            console.error('Fetch error:', error);
            // Fallback to XMLHttpRequest
            console.log('Falling back to XMLHttpRequest...');
            submitFormWithXHR(formData, csrfToken, submitBtn, originalText);
        });
    } catch (error) {
        console.error('Fetch setup error:', error);
        // Fallback to XMLHttpRequest
        submitFormWithXHR(formData, csrfToken, submitBtn, originalText);
    }
}

/**
 * Submit form via XMLHttpRequest as fallback
 */
function submitFormWithXHR(formData, csrfToken, submitBtn, originalText) {
    console.log('Using XMLHttpRequest fallback...');
    
    const xhr = new XMLHttpRequest();
    xhr.open('POST', window.location.href, true);
    xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
    xhr.setRequestHeader('X-CSRFToken', csrfToken);
    
    xhr.onreadystatechange = function() {
        if (xhr.readyState === 4) {
            console.log('XHR Response received:', xhr);
            if (xhr.status === 200) {
                try {
                    const data = JSON.parse(xhr.responseText);
                    console.log('XHR Data received:', data);
                    if (data.success) {
                        // Show success message
                        showSuccessMessage(data.message || 'Report generated successfully!');
                        
                        // Update the page with report data
                        updateReportDisplay(data);
                        
                        // Scroll to report section
                        const reportSection = document.querySelector('.balance-sheet-professional');
                        if (reportSection) {
                            reportSection.scrollIntoView({ behavior: 'smooth' });
                        }
                    } else {
                        // Show error message
                        showErrorMessage(data.error || 'Error generating report');
                        
                        // Show form errors if any
                        if (data.form_errors) {
                            showFormErrors(data.form_errors);
                        }
                    }
                } catch (e) {
                    console.error('Error parsing XHR response:', e);
                    showErrorMessage('Error parsing server response');
                }
            } else {
                console.error('XHR Error:', xhr.status, xhr.statusText);
                showErrorMessage('Network error. Please try again.');
            }
            
            // Restore button state
            submitBtn.innerHTML = originalText;
            submitBtn.disabled = false;
        }
    };
    
    xhr.onerror = function() {
        console.error('XHR Network error');
        showErrorMessage('Network error. Please try again.');
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
    };
    
    // Convert FormData to URL-encoded string for XHR
    const formDataObj = {};
    for (let [key, value] of formData.entries()) {
        formDataObj[key] = value;
    }
    
    const postData = new URLSearchParams(formDataObj).toString();
    xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
    xhr.send(postData);
}

/**
 * Show loading state during form submission
 */
function showLoadingState() {
    const container = document.querySelector('.balance-sheet-container');
    if (container) {
        container.classList.add('loading');
    }

    // Show loading spinner
    const submitBtn = document.querySelector('button[type="submit"]');
    if (submitBtn) {
        const originalText = submitBtn.innerHTML;
        submitBtn.innerHTML = '<i class="bi bi-hourglass-split me-1"></i> Generating...';
        submitBtn.disabled = true;

        // Restore button after a delay (in case of errors)
        setTimeout(() => {
            submitBtn.innerHTML = originalText;
            submitBtn.disabled = false;
            if (container) {
                container.classList.remove('loading');
            }
        }, 10000);
    }
}

/**
 * Show success message
 */
function showSuccessMessage(message) {
    // Remove existing messages
    removeExistingMessages();
    
    const messageDiv = document.createElement('div');
    messageDiv.className = 'alert alert-success alert-dismissible fade show';
    messageDiv.innerHTML = `
        <i class="bi bi-check-circle me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    const form = document.getElementById('balanceSheetForm');
    if (form) {
        form.parentNode.insertBefore(messageDiv, form);
    }
}

/**
 * Show error message
 */
function showErrorMessage(message) {
    // Remove existing messages
    removeExistingMessages();
    
    const messageDiv = document.createElement('div');
    messageDiv.className = 'alert alert-danger alert-dismissible fade show';
    messageDiv.innerHTML = `
        <i class="bi bi-exclamation-triangle me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    const form = document.getElementById('balanceSheetForm');
    if (form) {
        form.parentNode.insertBefore(messageDiv, form);
    }
}

/**
 * Remove existing messages
 */
function removeExistingMessages() {
    const existingMessages = document.querySelectorAll('.alert');
    existingMessages.forEach(msg => msg.remove());
}

/**
 * Show form errors
 */
function showFormErrors(errors) {
    // Clear previous errors
    clearFormErrors();
    
    Object.keys(errors).forEach(fieldName => {
        const field = document.querySelector(`[name="${fieldName}"]`);
        if (field) {
            field.classList.add('is-invalid');
            const errorDiv = document.createElement('div');
            errorDiv.className = 'invalid-feedback d-block';
            errorDiv.textContent = errors[fieldName][0];
            field.parentNode.appendChild(errorDiv);
        }
    });
}

/**
 * Clear form errors
 */
function clearFormErrors() {
    const invalidFields = document.querySelectorAll('.is-invalid');
    invalidFields.forEach(field => {
        field.classList.remove('is-invalid');
    });
    
    const errorDivs = document.querySelectorAll('.invalid-feedback');
    errorDivs.forEach(div => div.remove());
}

/**
 * Update report display with new data
 */
function updateReportDisplay(data) {
    // This function will be implemented based on the report structure
    // For now, we'll reload the page to show the new report
    if (data.report_id) {
        window.location.href = `/reports/balance-sheet/reports/${data.report_id}/`;
    } else {
        // Reload the page to show the new report
        window.location.reload();
    }
}

/**
 * Initialize Bootstrap tooltips
 */
function initTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Initialize form validation
 */
function initFormValidation() {
    const form = document.getElementById('balanceSheetForm');
    if (!form) return;

    // Custom validation for date fields
    const dateField = form.querySelector('input[type="date"]');
    if (dateField) {
        dateField.addEventListener('change', function() {
            const selectedDate = new Date(this.value);
            const today = new Date();
            
            if (selectedDate > today) {
                this.setCustomValidity('Date cannot be in the future');
                showFieldError(this, 'Date cannot be in the future');
            } else {
                this.setCustomValidity('');
                clearFieldError(this);
            }
        });
    }

    // Real-time validation feedback
    form.addEventListener('input', function(e) {
        if (e.target.matches('input, select, textarea')) {
            validateField(e.target);
        }
    });
}

/**
 * Validate individual form field
 */
function validateField(field) {
    const value = field.value.trim();
    
    // Clear previous error states
    clearFieldError(field);
    
    // Required field validation
    if (field.hasAttribute('required') && !value) {
        showFieldError(field, 'This field is required');
        return false;
    }
    
    // Date validation
    if (field.type === 'date' && value) {
        const selectedDate = new Date(value);
        const today = new Date();
        
        if (selectedDate > today) {
            showFieldError(field, 'Date cannot be in the future');
            return false;
        }
    }
    
    return true;
}

/**
 * Show field error
 */
function showFieldError(field, message) {
    // Remove existing error
    clearFieldError(field);
    
    // Add error class
    field.classList.add('is-invalid');
    
    // Create error message
    const errorDiv = document.createElement('div');
    errorDiv.className = 'invalid-feedback';
    errorDiv.textContent = message;
    
    // Insert error message after field
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
 * Initialize export modal functionality
 */
function initExportModal() {
    const exportModal = document.getElementById('exportModal');
    if (!exportModal) return;

    // Handle export dropdown buttons
    const exportButtons = document.querySelectorAll('[data-format]');
    exportButtons.forEach(button => {
        button.addEventListener('click', function() {
            const format = this.getAttribute('data-format');
            const formatSelect = exportModal.querySelector('select[name="export_format"]');
            if (formatSelect && format) {
                // Set the format in the select dropdown
                formatSelect.value = format.toUpperCase();
                updateExportOptions(format.toUpperCase());
            }
        });
    });

    const exportForm = exportModal.querySelector('form');
    if (exportForm) {
        exportForm.addEventListener('submit', function(e) {
            // Validate export options
            const format = this.querySelector('select[name="export_format"]').value;
            if (!format) {
                e.preventDefault();
                showModalError('Please select an export format');
                return;
            }
            
            // Show loading state
            const submitBtn = this.querySelector('button[type="submit"]');
            if (submitBtn) {
                const originalText = submitBtn.innerHTML;
                submitBtn.innerHTML = '<i class="bi bi-hourglass-split me-1"></i> Exporting...';
                submitBtn.disabled = true;
                
                // Reset button after timeout (in case of errors)
                setTimeout(() => {
                    submitBtn.innerHTML = originalText;
                    submitBtn.disabled = false;
                }, 15000);
            }
        });
    }

    // Format change handler
    const formatSelect = exportModal.querySelector('select[name="export_format"]');
    if (formatSelect) {
        formatSelect.addEventListener('change', function() {
            updateExportOptions(this.value);
        });
    }

    // Reset modal when closed
    exportModal.addEventListener('hidden.bs.modal', function() {
        resetExportModal();
    });
}

/**
 * Update export options based on selected format
 */
function updateExportOptions(format) {
    const percentageCheckbox = document.querySelector('input[name="include_percentages"]');
    const comparisonCheckbox = document.querySelector('input[name="include_comparison"]');
    
    if (format === 'csv') {
        // CSV doesn't support complex formatting
        if (percentageCheckbox) percentageCheckbox.disabled = true;
        if (comparisonCheckbox) comparisonCheckbox.disabled = true;
    } else {
        if (percentageCheckbox) percentageCheckbox.disabled = false;
        if (comparisonCheckbox) comparisonCheckbox.disabled = false;
    }
}

/**
 * Show modal error
 */
function showModalError(message) {
    const modal = document.getElementById('exportModal');
    if (!modal) return;

    // Remove existing alerts
    const existingAlert = modal.querySelector('.alert');
    if (existingAlert) {
        existingAlert.remove();
    }

    // Create error alert
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-danger alert-dismissible fade show';
    alertDiv.innerHTML = `
        <i class="bi bi-exclamation-triangle me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    // Insert at top of modal body
    const modalBody = modal.querySelector('.modal-body');
    modalBody.insertBefore(alertDiv, modalBody.firstChild);
}

/**
 * Show modal success message
 */
function showModalSuccess(message) {
    const modal = document.getElementById('exportModal');
    if (!modal) return;

    // Remove existing alerts
    const existingAlert = modal.querySelector('.alert');
    if (existingAlert) {
        existingAlert.remove();
    }

    // Create success alert
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-success alert-dismissible fade show';
    alertDiv.innerHTML = `
        <i class="bi bi-check-circle me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    // Insert at top of modal body
    const modalBody = modal.querySelector('.modal-body');
    modalBody.insertBefore(alertDiv, modalBody.firstChild);
}

/**
 * Reset export modal to default state
 */
function resetExportModal() {
    const modal = document.getElementById('exportModal');
    if (!modal) return;

    // Remove any alerts
    const alerts = modal.querySelectorAll('.alert');
    alerts.forEach(alert => alert.remove());

    // Reset form
    const form = modal.querySelector('form');
    if (form) {
        // Reset format selection
        const formatSelect = form.querySelector('select[name="export_format"]');
        if (formatSelect) {
            formatSelect.selectedIndex = 0;
        }

        // Reset checkboxes to default state
        const checkboxes = form.querySelectorAll('input[type="checkbox"]');
        checkboxes.forEach(checkbox => {
            checkbox.checked = checkbox.hasAttribute('checked');
            checkbox.disabled = false;
        });

        // Reset submit button
        const submitBtn = form.querySelector('button[type="submit"]');
        if (submitBtn) {
            submitBtn.innerHTML = '<i class="bi bi-download me-1"></i> Export';
            submitBtn.disabled = false;
        }
    }
}

/**
 * Initialize print functionality
 */
function initPrintFunctionality() {
    // Add print button event listeners
    const printButtons = document.querySelectorAll('button[onclick="window.print()"]');
    printButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            prepareForPrint();
            window.print();
        });
    });
}

/**
 * Prepare page for printing
 */
function prepareForPrint() {
    // Add print-specific classes
    document.body.classList.add('printing');
    
    // Remove print class after printing
    window.addEventListener('afterprint', function() {
        document.body.classList.remove('printing');
    });
}

/**
 * Initialize responsive behavior
 */
function initResponsiveBehavior() {
    // Handle window resize
    let resizeTimer;
    window.addEventListener('resize', function() {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(function() {
            adjustLayout();
        }, 250);
    });

    // Initial layout adjustment
    adjustLayout();
}

/**
 * Adjust layout based on screen size
 */
function adjustLayout() {
    const container = document.querySelector('.balance-sheet-container');
    if (!container) return;

    const isMobile = window.innerWidth <= 768;
    
    if (isMobile) {
        container.classList.add('mobile-layout');
    } else {
        container.classList.remove('mobile-layout');
    }
}

/**
 * Initialize accessibility features
 */
function initAccessibility() {
    // Add keyboard navigation
    addKeyboardNavigation();
    
    // Add ARIA labels
    addAriaLabels();
    
    // Add focus management
    addFocusManagement();
}

/**
 * Add keyboard navigation
 */
function addKeyboardNavigation() {
    // Navigate through account rows with arrow keys
    const accountRows = document.querySelectorAll('.account-row');
    accountRows.forEach((row, index) => {
        row.setAttribute('tabindex', '0');
        row.setAttribute('role', 'button');
        
        row.addEventListener('keydown', function(e) {
            switch(e.key) {
                case 'ArrowDown':
                    e.preventDefault();
                    if (index < accountRows.length - 1) {
                        accountRows[index + 1].focus();
                    }
                    break;
                case 'ArrowUp':
                    e.preventDefault();
                    if (index > 0) {
                        accountRows[index - 1].focus();
                    }
                    break;
                case 'Enter':
                case ' ':
                    e.preventDefault();
                    this.click();
                    break;
            }
        });
    });
}

/**
 * Add ARIA labels
 */
function addAriaLabels() {
    // Add labels to account rows
    const accountRows = document.querySelectorAll('.account-row');
    accountRows.forEach(row => {
        const accountName = row.querySelector('.account-name');
        const accountAmount = row.querySelector('.account-amount');
        
        if (accountName && accountAmount) {
            row.setAttribute('aria-label', `${accountName.textContent}: ${accountAmount.textContent}`);
        }
    });

    // Add labels to totals
    const totals = document.querySelectorAll('.account-total, .grand-total');
    totals.forEach(total => {
        const label = total.querySelector('.total-label');
        const amount = total.querySelector('.total-amount');
        
        if (label && amount) {
            total.setAttribute('aria-label', `${label.textContent}: ${amount.textContent}`);
        }
    });
}

/**
 * Add focus management
 */
function addFocusManagement() {
    // Trap focus in modals
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        const focusableElements = modal.querySelectorAll(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        
        const firstElement = focusableElements[0];
        const lastElement = focusableElements[focusableElements.length - 1];
        
        modal.addEventListener('keydown', function(e) {
            if (e.key === 'Tab') {
                if (e.shiftKey) {
                    if (document.activeElement === firstElement) {
                        e.preventDefault();
                        lastElement.focus();
                    }
                } else {
                    if (document.activeElement === lastElement) {
                        e.preventDefault();
                        firstElement.focus();
                    }
                }
            }
        });
    });
}

/**
 * Format currency values
 */
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(amount);
}

/**
 * Format percentage values
 */
function formatPercentage(value) {
    return new Intl.NumberFormat('en-US', {
        style: 'percent',
        minimumFractionDigits: 1,
        maximumFractionDigits: 1
    }).format(value / 100);
}

/**
 * Add negative/zero amount styling
 */
function addAmountStyling() {
    const amounts = document.querySelectorAll('.account-amount, .total-amount');
    amounts.forEach(amount => {
        const value = parseFloat(amount.textContent.replace(/[$,]/g, ''));
        
        if (value < 0) {
            amount.classList.add('negative');
        } else if (value === 0) {
            amount.classList.add('zero');
        }
    });
}

/**
 * Initialize amount styling
 */
document.addEventListener('DOMContentLoaded', function() {
    addAmountStyling();
});

/**
 * Export functions for external use
 */
window.BalanceSheet = {
    formatCurrency,
    formatPercentage,
    showLoadingState,
    prepareForPrint
};