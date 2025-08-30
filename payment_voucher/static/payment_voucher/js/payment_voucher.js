/**
 * Payment Voucher JavaScript
 * Handles form validation, autocomplete, and interactive features
 */

// Global variables
let payeeSearchTimeout;
let accountSearchTimeout;

/**
 * Initialize payment voucher form functionality
 */
function initializePaymentVoucherForm() {
    // Initialize payee search
    initializePayeeSearch();
    
    // Initialize account search
    initializeAccountSearch();
    
    // Initialize form validation
    initializeFormValidation();
    
    // Initialize amount formatting
    initializeAmountFormatting();
    
    // Initialize date picker
    initializeDatePicker();
    
    // Initialize file upload
    initializeFileUpload();
}

/**
 * Initialize payee search functionality
 */
function initializePayeeSearch() {
    const payeeSearchInput = document.getElementById('id_payee_search');
    const payeeNameInput = document.getElementById('id_payee_name');
    const payeeIdInput = document.getElementById('id_payee_id');
    const payeeTypeSelect = document.getElementById('id_payee_type');
    
    if (!payeeSearchInput) return;
    
    // Create search results container
    const searchResultsContainer = document.createElement('div');
    searchResultsContainer.className = 'payee-search-results';
    searchResultsContainer.style.cssText = `
        position: absolute;
        top: 100%;
        left: 0;
        right: 0;
        background: white;
        border: 1px solid #ddd;
        border-top: none;
        border-radius: 0 0 8px 8px;
        max-height: 200px;
        overflow-y: auto;
        z-index: 1000;
        display: none;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    `;
    
    payeeSearchInput.parentNode.style.position = 'relative';
    payeeSearchInput.parentNode.appendChild(searchResultsContainer);
    
    // Handle search input
    payeeSearchInput.addEventListener('input', function() {
        const query = this.value.trim();
        const payeeType = payeeTypeSelect ? payeeTypeSelect.value : '';
        
        if (query.length < 2) {
            searchResultsContainer.style.display = 'none';
            return;
        }
        
        // Clear previous timeout
        clearTimeout(payeeSearchTimeout);
        
        // Set new timeout for search
        payeeSearchTimeout = setTimeout(() => {
            searchPayees(query, payeeType, searchResultsContainer, payeeNameInput, payeeIdInput);
        }, 300);
    });
    
    // Handle payee type change
    if (payeeTypeSelect) {
        payeeTypeSelect.addEventListener('change', function() {
            payeeSearchInput.value = '';
            payeeNameInput.value = '';
            payeeIdInput.value = '';
            searchResultsContainer.style.display = 'none';
        });
    }
    
    // Hide results when clicking outside
    document.addEventListener('click', function(e) {
        if (!payeeSearchInput.contains(e.target) && !searchResultsContainer.contains(e.target)) {
            searchResultsContainer.style.display = 'none';
        }
    });
}

/**
 * Search payees via AJAX
 */
function searchPayees(query, payeeType, container, nameInput, idInput) {
    const url = new URL('/accounting/payment-vouchers/ajax/payee-search/', window.location.origin);
    url.searchParams.append('q', query);
    url.searchParams.append('payee_type', payeeType);
    
    fetch(url)
        .then(response => response.json())
        .then(data => {
            displayPayeeResults(data.results, container, nameInput, idInput);
        })
        .catch(error => {
            console.error('Error searching payees:', error);
            showNotification('Error searching payees', 'error');
        });
}

/**
 * Display payee search results
 */
function displayPayeeResults(results, container, nameInput, idInput) {
    container.innerHTML = '';
    
    if (results.length === 0) {
        container.innerHTML = '<div class="p-3 text-muted">No results found</div>';
        container.style.display = 'block';
        return;
    }
    
    results.forEach(result => {
        const resultItem = document.createElement('div');
        resultItem.className = 'payee-result-item';
        resultItem.style.cssText = `
            padding: 0.75rem 1rem;
            border-bottom: 1px solid #eee;
            cursor: pointer;
            transition: background-color 0.2s;
        `;
        
        resultItem.innerHTML = `
            <div class="fw-bold">${result.text}</div>
            <small class="text-muted">${result.type}</small>
        `;
        
        resultItem.addEventListener('click', function() {
            nameInput.value = result.name;
            idInput.value = result.code || '';
            container.style.display = 'none';
        });
        
        resultItem.addEventListener('mouseenter', function() {
            this.style.backgroundColor = '#f8f9fa';
        });
        
        resultItem.addEventListener('mouseleave', function() {
            this.style.backgroundColor = 'white';
        });
        
        container.appendChild(resultItem);
    });
    
    container.style.display = 'block';
}

/**
 * Initialize account search functionality
 */
function initializeAccountSearch() {
    const accountSelect = document.getElementById('id_account_to_debit');
    const paymentModeSelect = document.getElementById('id_payment_mode');
    
    if (!accountSelect) return;
    
    // Convert to Select2 with search
    $(accountSelect).select2({
        theme: 'bootstrap-5',
        width: '100%',
        placeholder: 'Search for account...',
        allowClear: true,
        ajax: {
            url: '/accounting/payment-vouchers/ajax/account-search/',
            dataType: 'json',
            delay: 250,
            data: function(params) {
                const paymentMode = paymentModeSelect ? paymentModeSelect.value : '';
                return {
                    q: params.term,
                    payment_mode: paymentMode,
                    page: params.page || 1
                };
            },
            processResults: function(data, params) {
                params.page = params.page || 1;
                
                return {
                    results: data.results,
                    pagination: {
                        more: false
                    }
                };
            },
            cache: false // Disable cache to ensure fresh results when payment mode changes
        },
        templateResult: formatAccountOption,
        templateSelection: formatAccountSelection
    });
    
    // Add payment mode change handler
    if (paymentModeSelect) {
        paymentModeSelect.addEventListener('change', function() {
            // Clear current selection and refresh options
            $(accountSelect).val(null).trigger('change');
            
            // Update placeholder based on payment mode
            const paymentMode = this.value;
            let placeholder = 'Search for account...';
            
            if (paymentMode === 'cash') {
                placeholder = 'Search for cash accounts...';
            } else if (paymentMode === 'bank_transfer' || paymentMode === 'cheque') {
                placeholder = 'Search for bank accounts...';
            } else if (paymentMode === 'credit_card') {
                placeholder = 'Search for credit card accounts...';
            }
            
            // Update Select2 placeholder
            $(accountSelect).data('select2').$selection.find('.select2-selection__placeholder').text(placeholder);
        });
    }
}

/**
 * Format account option for Select2
 */
function formatAccountOption(account) {
    if (account.loading) return account.text;
    
    return $(`
        <div class="account-option">
            <div class="fw-bold">${account.code} - ${account.name}</div>
            <small class="text-muted">${account.category}</small>
        </div>
    `);
}

/**
 * Format account selection for Select2
 */
function formatAccountSelection(account) {
    return account.code ? `${account.code} - ${account.name}` : account.text;
}

/**
 * Initialize form validation
 */
function initializeFormValidation() {
    const form = document.getElementById('payment-voucher-form');
    
    if (!form) return;
    
    // Real-time validation
    const requiredFields = form.querySelectorAll('[required]');
    requiredFields.forEach(field => {
        field.addEventListener('blur', function() {
            validateField(this);
        });
        
        field.addEventListener('input', function() {
            clearFieldError(this);
        });
    });
    
    // Amount validation
    const amountField = document.getElementById('id_amount');
    if (amountField) {
        amountField.addEventListener('input', function() {
            validateAmount(this);
        });
    }
    
    // Date validation
    const dateField = document.getElementById('id_voucher_date');
    if (dateField) {
        dateField.addEventListener('change', function() {
            validateDate(this);
        });
    }
    
    // Form submission validation
    form.addEventListener('submit', function(e) {
        if (!validateForm()) {
            e.preventDefault();
            showNotification('Please fix the errors before submitting', 'error');
        }
    });
}

/**
 * Validate individual field
 */
function validateField(field) {
    const value = field.value.trim();
    const isRequired = field.hasAttribute('required');
    
    if (isRequired && !value) {
        showFieldError(field, 'This field is required');
        return false;
    }
    
    clearFieldError(field);
    return true;
}

/**
 * Validate amount field
 */
function validateAmount(field) {
    const value = parseFloat(field.value);
    
    if (isNaN(value) || value <= 0) {
        showFieldError(field, 'Amount must be greater than zero');
        return false;
    }
    
    clearFieldError(field);
    return true;
}

/**
 * Validate date field
 */
function validateDate(field) {
    const selectedDate = new Date(field.value);
    const today = new Date();
    today.setHours(23, 59, 59, 999);
    
    if (selectedDate > today) {
        showFieldError(field, 'Date cannot be in the future');
        return false;
    }
    
    clearFieldError(field);
    return true;
}

/**
 * Validate entire form
 */
function validateForm() {
    const form = document.getElementById('payment-voucher-form');
    const requiredFields = form.querySelectorAll('[required]');
    let isValid = true;
    
    requiredFields.forEach(field => {
        if (!validateField(field)) {
            isValid = false;
        }
    });
    
    const amountField = document.getElementById('id_amount');
    if (amountField && !validateAmount(amountField)) {
        isValid = false;
    }
    
    const dateField = document.getElementById('id_voucher_date');
    if (dateField && !validateDate(dateField)) {
        isValid = false;
    }
    
    return isValid;
}

/**
 * Show field error
 */
function showFieldError(field, message) {
    clearFieldError(field);
    
    field.classList.add('is-invalid');
    
    const errorDiv = document.createElement('div');
    errorDiv.className = 'invalid-feedback d-block';
    errorDiv.textContent = message;
    
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
 * Initialize amount formatting
 */
function initializeAmountFormatting() {
    const amountField = document.getElementById('id_amount');
    
    if (!amountField) return;
    
    amountField.addEventListener('blur', function() {
        const value = parseFloat(this.value);
        if (!isNaN(value)) {
            this.value = value.toFixed(2);
        }
    });
    
    amountField.addEventListener('input', function() {
        // Allow only numbers and decimal point
        this.value = this.value.replace(/[^0-9.]/g, '');
        
        // Ensure only one decimal point
        const parts = this.value.split('.');
        if (parts.length > 2) {
            this.value = parts[0] + '.' + parts.slice(1).join('');
        }
    });
}

/**
 * Initialize date picker
 */
function initializeDatePicker() {
    const dateField = document.getElementById('id_voucher_date');
    
    if (!dateField) return;
    
    // Set max date to today
    const today = new Date().toISOString().split('T')[0];
    dateField.setAttribute('max', today);
    
    // Set default value to today if empty
    if (!dateField.value) {
        dateField.value = today;
    }
}

/**
 * Initialize file upload
 */
function initializeFileUpload() {
    const fileInputs = document.querySelectorAll('input[type="file"]');
    
    fileInputs.forEach(input => {
        input.addEventListener('change', function() {
            validateFileUpload(this);
        });
    });
}

/**
 * Validate file upload
 */
function validateFileUpload(input) {
    const file = input.files[0];
    if (!file) return;
    
    // Check file size (10MB limit)
    const maxSize = 10 * 1024 * 1024; // 10MB
    if (file.size > maxSize) {
        showNotification('File size must be less than 10MB', 'error');
        input.value = '';
        return false;
    }
    
    // Check file type
    const allowedTypes = [
        'application/pdf',
        'image/jpeg',
        'image/jpg',
        'image/png',
        'image/gif',
        'image/bmp',
        'image/webp',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    ];
    
    if (!allowedTypes.includes(file.type)) {
        showNotification('File type not allowed. Please upload PDF, image, or document files.', 'error');
        input.value = '';
        return false;
    }
    
    return true;
}

/**
 * Show notification
 */
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    notification.style.cssText = `
        top: 20px;
        right: 20px;
        z-index: 9999;
        min-width: 300px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    `;
    
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(notification);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 5000);
}

/**
 * Initialize dashboard functionality
 */
function initializeDashboard() {
    // Load summary statistics
    loadVoucherSummary();
    
    // Initialize charts if Chart.js is available
    if (typeof Chart !== 'undefined') {
        initializeCharts();
    }
}

/**
 * Load voucher summary statistics
 */
function loadVoucherSummary() {
    fetch('/accounting/payment-vouchers/ajax/voucher-summary/')
        .then(response => response.json())
        .then(data => {
            updateSummaryCards(data);
        })
        .catch(error => {
            console.error('Error loading voucher summary:', error);
        });
}

/**
 * Update summary cards with data
 */
function updateSummaryCards(data) {
    // Update total vouchers
    const totalVouchersElement = document.getElementById('total-vouchers');
    if (totalVouchersElement) {
        totalVouchersElement.textContent = data.total_vouchers;
    }
    
    // Update total amount
    const totalAmountElement = document.getElementById('total-amount');
    if (totalAmountElement) {
        totalAmountElement.textContent = `AED ${parseFloat(data.total_amount).toFixed(2)}`;
    }
    
    // Update status counts
    Object.keys(data.status_counts).forEach(status => {
        const element = document.getElementById(`${status}-count`);
        if (element) {
            element.textContent = data.status_counts[status];
        }
    });
}

/**
 * Initialize charts
 */
function initializeCharts() {
    // Monthly totals chart
    const monthlyChartCtx = document.getElementById('monthlyChart');
    if (monthlyChartCtx) {
        new Chart(monthlyChartCtx, {
            type: 'line',
            data: {
                labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
                datasets: [{
                    label: 'Monthly Totals',
                    data: window.monthlyTotals || [],
                    borderColor: '#667eea',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'top',
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }
    
    // Payment mode chart
    const paymentModeChartCtx = document.getElementById('paymentModeChart');
    if (paymentModeChartCtx) {
        new Chart(paymentModeChartCtx, {
            type: 'doughnut',
            data: {
                labels: ['Cash', 'Bank Transfer', 'Cheque', 'Credit Card', 'Other'],
                datasets: [{
                    data: [
                        window.paymentModeCounts?.cash || 0,
                        window.paymentModeCounts?.bank_transfer || 0,
                        window.paymentModeCounts?.cheque || 0,
                        window.paymentModeCounts?.credit_card || 0,
                        window.paymentModeCounts?.other || 0
                    ],
                    backgroundColor: [
                        '#FF6384',
                        '#36A2EB',
                        '#FFCE56',
                        '#4BC0C0',
                        '#9966FF'
                    ]
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'bottom',
                    }
                }
            }
        });
    }
}

/**
 * Export functionality
 */
function exportVouchers(format = 'excel') {
    const currentUrl = new URL(window.location.href);
    currentUrl.searchParams.set('export', format);
    
    window.location.href = currentUrl.toString();
}

/**
 * Print voucher
 */
function printVoucher(voucherId) {
    const printWindow = window.open(`/accounting/payment-vouchers/${voucherId}/print/`, '_blank');
    printWindow.focus();
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Initialize form if on form page
    if (document.getElementById('payment-voucher-form')) {
        initializePaymentVoucherForm();
    }
    
    // Initialize dashboard if on dashboard page
    if (document.getElementById('voucher-dashboard')) {
        initializeDashboard();
    }
    
    // Initialize list functionality if on list page
    if (document.getElementById('voucher-list')) {
        initializeListFunctionality();
    }
});

/**
 * Initialize list functionality
 */
function initializeListFunctionality() {
    // Initialize bulk actions
    initializeBulkActions();
    
    // Initialize quick actions
    initializeQuickActions();
}

/**
 * Initialize bulk actions
 */
function initializeBulkActions() {
    const selectAllCheckbox = document.getElementById('select-all');
    const voucherCheckboxes = document.querySelectorAll('.voucher-checkbox');
    const bulkActionsContainer = document.getElementById('bulk-actions');
    
    if (!selectAllCheckbox) return;
    
    // Select all functionality
    selectAllCheckbox.addEventListener('change', function() {
        voucherCheckboxes.forEach(checkbox => {
            checkbox.checked = this.checked;
        });
        updateBulkActionsVisibility();
    });
    
    // Individual checkbox functionality
    voucherCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            updateSelectAllState();
            updateBulkActionsVisibility();
        });
    });
    
    function updateSelectAllState() {
        const checkedCount = document.querySelectorAll('.voucher-checkbox:checked').length;
        const totalCount = voucherCheckboxes.length;
        
        selectAllCheckbox.checked = checkedCount === totalCount;
        selectAllCheckbox.indeterminate = checkedCount > 0 && checkedCount < totalCount;
    }
    
    function updateBulkActionsVisibility() {
        const checkedCount = document.querySelectorAll('.voucher-checkbox:checked').length;
        
        if (bulkActionsContainer) {
            bulkActionsContainer.style.display = checkedCount > 0 ? 'block' : 'none';
        }
    }
}

/**
 * Initialize quick actions
 */
function initializeQuickActions() {
    // Quick approve buttons
    document.querySelectorAll('.quick-approve').forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const voucherId = this.dataset.voucherId;
            quickApproveVoucher(voucherId);
        });
    });
    
    // Quick pay buttons
    document.querySelectorAll('.quick-pay').forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const voucherId = this.dataset.voucherId;
            quickPayVoucher(voucherId);
        });
    });
}

/**
 * Quick approve voucher
 */
function quickApproveVoucher(voucherId) {
    if (!confirm('Are you sure you want to approve this voucher?')) {
        return;
    }
    
    fetch(`/accounting/payment-vouchers/${voucherId}/approve/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({})
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Voucher approved successfully', 'success');
            setTimeout(() => window.location.reload(), 1000);
        } else {
            showNotification(data.error || 'Error approving voucher', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Error approving voucher', 'error');
    });
}

/**
 * Quick pay voucher
 */
function quickPayVoucher(voucherId) {
    if (!confirm('Are you sure you want to mark this voucher as paid?')) {
        return;
    }
    
    fetch(`/accounting/payment-vouchers/${voucherId}/mark-paid/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({})
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Voucher marked as paid successfully', 'success');
            setTimeout(() => window.location.reload(), 1000);
        } else {
            showNotification(data.error || 'Error marking voucher as paid', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Error marking voucher as paid', 'error');
    });
}

/**
 * Get CSRF token from cookies
 */
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