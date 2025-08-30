/**
 * Profit & Loss Statement JavaScript
 * Handles form interactions, data validation, and export functionality
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize the application
    initProfitLossStatement();
});

function initProfitLossStatement() {
    // Initialize form handlers
    initFormHandlers();
    
    // Initialize export modal
    initExportModal();
    
    // Initialize responsive behavior
    initResponsiveBehavior();
    
    // Initialize print functionality
    initPrintFunctionality();
    
    // Initialize accessibility features
    initAccessibility();
}

function initFormHandlers() {
    console.log('Initializing form handlers...');
    const form = document.getElementById('reportForm');
    const reportPeriodSelect = document.getElementById('report-period');
    const fromDateInput = document.getElementById('id_from_date');
    const toDateInput = document.getElementById('id_to_date');
    const comparisonSelect = document.getElementById('comparison-type');
    
    console.log('Form element:', form);
    console.log('From date input:', fromDateInput);
    console.log('To date input:', toDateInput);
    
    // Form submission handler
    if (form) {
        console.log('Form found, adding submission handler');
        const generateBtn = document.getElementById('generateBtn');
        
        form.addEventListener('submit', function(e) {
            e.preventDefault(); // Prevent default form submission
            console.log('Form submitted via AJAX');
            
            // Show loading state
            if (generateBtn) {
                const btnText = generateBtn.querySelector('.btn-text');
                const btnLoading = generateBtn.querySelector('.btn-loading');
                if (btnText && btnLoading) {
                    btnText.classList.add('d-none');
                    btnLoading.classList.remove('d-none');
                    generateBtn.disabled = true;
                }
            }
            
            // Submit form via AJAX
            submitFormAjax(form);
        });
    } else {
        console.error('Form with ID "reportForm" not found!');
    }
    
    // Check if we should scroll to report after page reload
    if (sessionStorage.getItem('scrollToReport') === 'true') {
        sessionStorage.removeItem('scrollToReport');
        setTimeout(function() {
            const reportSection = document.getElementById('profitLossReport');
            if (reportSection) {
                reportSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
                // Add a subtle highlight effect
                reportSection.style.transition = 'box-shadow 0.3s ease';
                reportSection.style.boxShadow = '0 0 20px rgba(0, 123, 255, 0.3)';
                setTimeout(() => {
                    reportSection.style.boxShadow = '';
                }, 2000);
            }
        }, 100);
    }
    
    // Handle report period changes
    if (reportPeriodSelect) {
        reportPeriodSelect.addEventListener('change', function() {
            updateDateRange(this.value);
        });
    }
    
    // Handle comparison type changes
    if (comparisonSelect) {
        comparisonSelect.addEventListener('change', function() {
            updateComparisonOptions(this.value);
        });
    }
    
    // Add form validation
    addFormValidation();
}

function handleFormSubmit(event) {
    console.log('Form submission handler called');
    
    const fromDate = document.getElementById('id_from_date')?.value;
    const toDate = document.getElementById('id_to_date')?.value;
    
    console.log('From date:', fromDate);
    console.log('To date:', toDate);
    
    // Temporarily disable validation to test form submission
    console.log('Validation temporarily disabled - allowing submission');
    
    const form = event.target;
    const submitButton = form.querySelector('button[type="submit"]');
    
    // Show loading state
    if (submitButton) {
        const originalText = submitButton.innerHTML;
        submitButton.innerHTML = '<i class="bi bi-hourglass-split me-1"></i>Generating Report...';
        submitButton.disabled = true;
        
        // Re-enable after a delay (in case of validation errors)
        setTimeout(() => {
            submitButton.innerHTML = originalText;
            submitButton.disabled = false;
        }, 5000);
    }
    
    // Add loading class to main container
    const container = document.querySelector('.container-fluid');
    if (container) {
        container.classList.add('loading');
    }
    
    return true;
}

function validateForm(form) {
    const fromDateField = form.querySelector('#id_from_date');
    const toDateField = form.querySelector('#id_to_date');
    
    console.log('Validating form...');
    console.log('From date field:', fromDateField);
    console.log('To date field:', toDateField);
    
    if (!fromDateField || !toDateField) {
        console.log('Date fields not found!');
        showAlert('Date fields not found. Please refresh the page.', 'danger');
        return false;
    }
    
    const fromDate = fromDateField.value;
    const toDate = toDateField.value;
    
    console.log('From date value:', fromDate);
    console.log('To date value:', toDate);
    
    if (!fromDate || !toDate) {
        showAlert('Please select both from and to dates.', 'danger');
        return false;
    }
    
    if (new Date(fromDate) > new Date(toDate)) {
        showAlert('From date cannot be after to date.', 'danger');
        return false;
    }
    
    console.log('Form validation passed!');
    return true;
}

function updateDateRange(periodType) {
    const today = new Date();
    const fromDateInput = document.getElementById('id_from_date');
    const toDateInput = document.getElementById('id_to_date');
    
    if (!fromDateInput || !toDateInput) return;
    
    let fromDate, toDate;
    
    switch (periodType) {
        case 'monthly':
            fromDate = new Date(today.getFullYear(), today.getMonth(), 1);
            toDate = new Date(today.getFullYear(), today.getMonth() + 1, 0);
            break;
        case 'quarterly':
            const quarter = Math.floor(today.getMonth() / 3);
            fromDate = new Date(today.getFullYear(), quarter * 3, 1);
            toDate = new Date(today.getFullYear(), (quarter + 1) * 3, 0);
            break;
        case 'yearly':
            fromDate = new Date(today.getFullYear(), 0, 1);
            toDate = new Date(today.getFullYear(), 11, 31);
            break;
        default:
            return; // Keep custom dates
    }
    
    fromDateInput.value = formatDateForInput(fromDate);
    toDateInput.value = formatDateForInput(toDate);
}

function updateComparisonOptions(comparisonType) {
    const comparisonFields = document.querySelectorAll('.comparison-field');
    
    comparisonFields.forEach(field => {
        if (comparisonType === 'none') {
            field.style.display = 'none';
        } else {
            field.style.display = 'block';
        }
    });
}

function formatDateForInput(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

function addFormValidation() {
    const form = document.getElementById('reportForm');
    if (!form) return;
    
    // Add real-time validation
    const inputs = form.querySelectorAll('input, select');
    inputs.forEach(input => {
        input.addEventListener('blur', function() {
            validateField(this);
        });
        
        input.addEventListener('input', function() {
            clearFieldError(this);
        });
    });
}

function validateField(field) {
    const value = field.value.trim();
    
    // Clear previous errors
    clearFieldError(field);
    
    // Required field validation
    if (field.hasAttribute('required') && !value) {
        showFieldError(field, 'This field is required.');
        return false;
    }
    
    // Date validation
    if (field.type === 'date' && value) {
        const date = new Date(value);
        if (isNaN(date.getTime())) {
            showFieldError(field, 'Please enter a valid date.');
            return false;
        }
    }
    
    return true;
}

function showFieldError(field, message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'invalid-feedback d-block';
    errorDiv.textContent = message;
    
    field.classList.add('is-invalid');
    field.parentNode.appendChild(errorDiv);
}

function clearFieldError(field) {
    field.classList.remove('is-invalid');
    const errorDiv = field.parentNode.querySelector('.invalid-feedback');
    if (errorDiv) {
        errorDiv.remove();
    }
}

function initExportModal() {
    const exportModal = document.getElementById('exportModal');
    if (!exportModal) return;
    
    const exportForm = exportModal.querySelector('form');
    const exportButton = exportForm.querySelector('button[type="submit"]');
    
    exportForm.addEventListener('submit', function(event) {
        // Show loading state
        const originalText = exportButton.innerHTML;
        exportButton.innerHTML = '<i class="bi bi-hourglass-split me-1"></i>Exporting...';
        exportButton.disabled = true;
        
        // Let the form submit naturally
        // The form will handle the submission
    });
    
    // Handle format change
    const formatSelect = document.getElementById('export-format');
    if (formatSelect) {
        formatSelect.addEventListener('change', function() {
            updateExportOptions(this.value);
        });
    }
}

function updateExportOptions(format) {
    const percentageCheckbox = document.getElementById('include-percentages');
    const comparisonCheckbox = document.getElementById('include-comparison');
    
    // Show/hide options based on format
    if (format === 'csv') {
        if (percentageCheckbox) percentageCheckbox.checked = false;
        if (comparisonCheckbox) comparisonCheckbox.checked = false;
    }
}

function initResponsiveBehavior() {
    // Handle table responsiveness
    const table = document.getElementById('profitLossTable');
    if (table) {
        makeTableResponsive(table);
    }
    
    // Handle mobile menu
    const mobileMenuToggle = document.querySelector('.navbar-toggler');
    if (mobileMenuToggle) {
        mobileMenuToggle.addEventListener('click', function() {
            document.body.classList.toggle('mobile-menu-open');
        });
    }
}

function makeTableResponsive(table) {
    // Add horizontal scroll for small screens
    const wrapper = document.createElement('div');
    wrapper.className = 'table-responsive';
    table.parentNode.insertBefore(wrapper, table);
    wrapper.appendChild(table);
    
    // Add sticky header for better mobile experience
    if (window.innerWidth <= 768) {
        table.classList.add('table-sticky-header');
    }
}

function initPrintFunctionality() {
    // Handle print button
    const printButton = document.querySelector('button[onclick="window.print()"]');
    if (printButton) {
        printButton.addEventListener('click', function(event) {
            event.preventDefault();
            prepareForPrint();
            window.print();
        });
    }
    
    // Handle print media query
    window.addEventListener('beforeprint', prepareForPrint);
    window.addEventListener('afterprint', restoreAfterPrint);
}

function prepareForPrint() {
    // Hide unnecessary elements
    const elementsToHide = document.querySelectorAll('.btn, .modal, .card-header, .navbar, .footer');
    elementsToHide.forEach(el => {
        el.style.display = 'none';
    });
    
    // Add print-specific styles
    document.body.classList.add('printing');
}

function restoreAfterPrint() {
    // Show elements back
    const elementsToHide = document.querySelectorAll('.btn, .modal, .card-header, .navbar, .footer');
    elementsToHide.forEach(el => {
        el.style.display = '';
    });
    
    // Remove print-specific styles
    document.body.classList.remove('printing');
}

function initAccessibility() {
    // Add keyboard navigation
    addKeyboardNavigation();
    
    // Add ARIA labels
    addAriaLabels();
    
    // Add focus management
    addFocusManagement();
}

function addKeyboardNavigation() {
    // Handle table navigation
    const table = document.getElementById('profitLossTable');
    if (table) {
        const rows = table.querySelectorAll('tbody tr');
        
        rows.forEach((row, index) => {
            row.setAttribute('tabindex', '0');
            row.addEventListener('keydown', function(event) {
                if (event.key === 'Enter' || event.key === ' ') {
                    event.preventDefault();
                    this.click();
                }
            });
        });
    }
}

function addAriaLabels() {
    // Add ARIA labels to form elements
    const form = document.getElementById('reportForm');
    if (form) {
        const inputs = form.querySelectorAll('input, select');
        inputs.forEach(input => {
            if (!input.getAttribute('aria-label')) {
                const label = form.querySelector(`label[for="${input.id}"]`);
                if (label) {
                    input.setAttribute('aria-label', label.textContent);
                }
            }
        });
    }
}

function addFocusManagement() {
    // Manage focus for modals
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        modal.addEventListener('shown.bs.modal', function() {
            const firstInput = this.querySelector('input, select, button');
            if (firstInput) {
                firstInput.focus();
            }
        });
    });
}

// Utility functions
function showAlert(message, type = 'info') {
    // Create alert element
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Insert at top of container
    const container = document.querySelector('.container-fluid');
    if (container) {
        container.insertBefore(alertDiv, container.firstChild);
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    }
}

function resetForm() {
    const form = document.getElementById('reportForm');
    if (form) {
        form.reset();
        
        // Reset to current month
        const today = new Date();
        const firstDay = new Date(today.getFullYear(), today.getMonth(), 1);
        
        const fromDateInput = document.getElementById('id_from_date');
        const toDateInput = document.getElementById('id_to_date');
        
        if (fromDateInput) {
            fromDateInput.value = formatDateForInput(firstDay);
        }
        if (toDateInput) {
            toDateInput.value = formatDateForInput(today);
        }
        
        // Clear any validation errors
        const errorFields = form.querySelectorAll('.is-invalid');
        errorFields.forEach(field => {
            clearFieldError(field);
        });
        
        showAlert('Form has been reset to default values.', 'info');
    }
}

function formatCurrency(amount) {
    return new Intl.NumberFormat('en-AE', {
        style: 'currency',
        currency: 'AED',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(amount);
}

function formatPercentage(value) {
    return `${parseFloat(value).toFixed(2)}%`;
}

// Direct export function
function directExport(format) {
    const form = document.getElementById('reportForm');
    if (!form) {
        showAlert('Report form not found.', 'error');
        return;
    }
    
    // Validate form first
    if (!validateForm()) {
        showAlert('Please fill in all required fields before exporting.', 'error');
        return;
    }
    
    // Show loading state
    const button = document.getElementById(`direct${format.charAt(0).toUpperCase() + format.slice(1)}Export`);
    const originalText = button.innerHTML;
    button.disabled = true;
    button.innerHTML = '<i class="bi bi-hourglass-split me-1"></i>Exporting...';
    
    // Create a temporary form for export
    const exportForm = document.createElement('form');
    exportForm.method = 'POST';
    exportForm.action = '/profit-loss-statement/export/';
    exportForm.style.display = 'none';
    
    // Add CSRF token
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    const csrfInput = document.createElement('input');
    csrfInput.type = 'hidden';
    csrfInput.name = 'csrfmiddlewaretoken';
    csrfInput.value = csrfToken;
    exportForm.appendChild(csrfInput);
    
    // Add export format
    const formatInput = document.createElement('input');
    formatInput.type = 'hidden';
    formatInput.name = 'export_format';
    formatInput.value = format;
    exportForm.appendChild(formatInput);
    
    // Add form data
    const formData = new FormData(form);
    for (let [key, value] of formData.entries()) {
        if (key !== 'csrfmiddlewaretoken') {
            const input = document.createElement('input');
            input.type = 'hidden';
            input.name = key;
            input.value = value;
            exportForm.appendChild(input);
        }
    }
    
    // Add default export options
    const defaultOptions = {
        'include_headers': 'on',
        'include_totals': 'on',
        'include_percentages': 'on'
    };
    
    for (let [key, value] of Object.entries(defaultOptions)) {
        const input = document.createElement('input');
        input.type = 'hidden';
        input.name = key;
        input.value = value;
        exportForm.appendChild(input);
    }
    
    // Submit form
    document.body.appendChild(exportForm);
    exportForm.submit();
    document.body.removeChild(exportForm);
    
    // Reset button state after a delay
    setTimeout(() => {
        button.disabled = false;
        button.innerHTML = originalText;
        showAlert(`${format.toUpperCase()} export initiated successfully.`, 'success');
    }, 2000);
}

// Export functions for global access
window.profitLossStatement = {
    resetForm,
    formatCurrency,
    formatPercentage,
    showAlert
};

// Make directExport globally accessible
window.directExport = directExport;

// Handle window resize
window.addEventListener('resize', function() {
    // Reinitialize responsive behavior
    initResponsiveBehavior();
});

// Handle page visibility changes
document.addEventListener('visibilitychange', function() {
    if (document.visibilityState === 'visible') {
        // Refresh data if needed
        const reportData = document.querySelector('#profitLossTable');
        if (reportData && reportData.dataset.autoRefresh === 'true') {
            // Auto-refresh logic here
        }
    }
});

// AJAX form submission function
function submitFormAjax(form) {
    const formData = new FormData(form);
    const url = form.action || window.location.href;
    
    fetch(url, {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': getCsrfToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        handleAjaxResponse(data);
    })
    .catch(error => {
        console.error('Error:', error);
        handleAjaxError('An error occurred while generating the report. Please try again.');
    });
}

// Handle AJAX response
function handleAjaxResponse(data) {
    const generateBtn = document.getElementById('generateBtn');
    
    // Reset button state
    resetButtonState(generateBtn);
    
    if (data.success) {
        // Display the report data
        displayReportData(data);
        
        // Scroll to report section
        setTimeout(() => {
            const reportSection = document.getElementById('profitLossReport');
            if (reportSection) {
                reportSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
                // Add highlight effect
                reportSection.style.transition = 'box-shadow 0.3s ease';
                reportSection.style.boxShadow = '0 0 20px rgba(0, 123, 255, 0.3)';
                setTimeout(() => {
                    reportSection.style.boxShadow = '';
                }, 2000);
            }
        }, 100);
        
        // Show success message
        showMessage('Report generated successfully!', 'success');
    } else {
        // Handle error
        handleAjaxError(data.error || 'Failed to generate report');
    }
}

// Handle AJAX errors
function handleAjaxError(errorMessage) {
    const generateBtn = document.getElementById('generateBtn');
    resetButtonState(generateBtn);
    showMessage(errorMessage, 'error');
}

// Reset button state
function resetButtonState(button) {
    if (button) {
        const btnText = button.querySelector('.btn-text');
        const btnLoading = button.querySelector('.btn-loading');
        if (btnText && btnLoading) {
            btnText.classList.remove('d-none');
            btnLoading.classList.add('d-none');
            button.disabled = false;
        }
    }
}

// Display report data
function displayReportData(data) {
    const reportSection = document.getElementById('profitLossReport');
    if (!reportSection) return;
    
    // Update report header information
    updateReportHeader(data);
    
    // Update report table
    updateReportTable(data.report_data);
    
    // Show the report section
    reportSection.style.display = 'block';
}

// Update report header
function updateReportHeader(data) {
    const companyElement = document.querySelector('.report-company');
    const periodElement = document.querySelector('.report-period');
    
    if (companyElement) {
        companyElement.textContent = data.company;
    }
    
    if (periodElement) {
        periodElement.textContent = `${data.from_date} to ${data.to_date}`;
    }
}

// Update report table
function updateReportTable(reportData) {
    const tableBody = document.querySelector('#profitLossTable tbody');
    if (!tableBody || !reportData) return;
    
    // Clear existing table content
    tableBody.innerHTML = '';
    
    // Add revenue section
    if (reportData.revenue) {
        addTableSection(tableBody, 'REVENUE', reportData.revenue);
    }
    
    // Add cost of goods sold section
    if (reportData.cost_of_goods_sold) {
        addTableSection(tableBody, 'COST OF GOODS SOLD', reportData.cost_of_goods_sold);
    }
    
    // Add operating expenses section
    if (reportData.operating_expenses) {
        addTableSection(tableBody, 'OPERATING EXPENSES', reportData.operating_expenses);
    }
    
    // Add other income section
    if (reportData.other_income) {
        addTableSection(tableBody, 'OTHER INCOME', reportData.other_income);
    }
    
    // Add other expenses section
    if (reportData.other_expenses) {
        addTableSection(tableBody, 'OTHER EXPENSES', reportData.other_expenses);
    }
    
    // Add totals
    addTableTotals(tableBody, reportData);
}

// Add table section
function addTableSection(tableBody, sectionTitle, sectionData) {
    // Add section header
    const headerRow = document.createElement('tr');
    headerRow.className = 'table-section-header';
    headerRow.innerHTML = `
        <td colspan="3" class="fw-bold text-primary">${sectionTitle}</td>
    `;
    tableBody.appendChild(headerRow);
    
    // Add section items
    Object.entries(sectionData).forEach(([key, value]) => {
        if (key !== 'total') {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td class="ps-4">${key}</td>
                <td class="text-end">${formatCurrency(value)}</td>
                <td class="text-end">-</td>
            `;
            tableBody.appendChild(row);
        }
    });
    
    // Add section total
    if (sectionData.total !== undefined) {
        const totalRow = document.createElement('tr');
        totalRow.className = 'table-section-total';
        totalRow.innerHTML = `
            <td class="fw-bold ps-4">Total ${sectionTitle}</td>
            <td class="text-end fw-bold">${formatCurrency(sectionData.total)}</td>
            <td class="text-end">-</td>
        `;
        tableBody.appendChild(totalRow);
    }
}

// Add table totals
function addTableTotals(tableBody, reportData) {
    // Add gross profit
    if (reportData.gross_profit !== undefined) {
        const grossProfitRow = document.createElement('tr');
        grossProfitRow.className = 'table-total-row';
        grossProfitRow.innerHTML = `
            <td class="fw-bold">GROSS PROFIT</td>
            <td class="text-end fw-bold">${formatCurrency(reportData.gross_profit)}</td>
            <td class="text-end">-</td>
        `;
        tableBody.appendChild(grossProfitRow);
    }
    
    // Add net profit
    if (reportData.net_profit !== undefined) {
        const netProfitRow = document.createElement('tr');
        netProfitRow.className = 'table-final-total';
        netProfitRow.innerHTML = `
            <td class="fw-bold">NET PROFIT</td>
            <td class="text-end fw-bold">${formatCurrency(reportData.net_profit)}</td>
            <td class="text-end">-</td>
        `;
        tableBody.appendChild(netProfitRow);
    }
}

// Format currency
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 2
    }).format(amount || 0);
}

// Get CSRF token
function getCsrfToken() {
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
    return csrfToken ? csrfToken.value : '';
}

// Show message
function showMessage(message, type) {
    // Create or update message container
    let messageContainer = document.getElementById('ajax-messages');
    if (!messageContainer) {
        messageContainer = document.createElement('div');
        messageContainer.id = 'ajax-messages';
        messageContainer.className = 'position-fixed top-0 end-0 p-3';
        messageContainer.style.zIndex = '9999';
        document.body.appendChild(messageContainer);
    }
    
    // Create message element
    const messageElement = document.createElement('div');
    messageElement.className = `alert alert-${type === 'error' ? 'danger' : 'success'} alert-dismissible fade show`;
    messageElement.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    messageContainer.appendChild(messageElement);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (messageElement.parentNode) {
            messageElement.remove();
        }
    }, 5000);
}