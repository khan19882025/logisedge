/**
 * Bank Accounts Management JavaScript
 * Handles all interactive functionality for the bank accounts module
 */

$(document).ready(function() {
    // Initialize all bank accounts functionality
    initializeBankAccounts();
});

function initializeBankAccounts() {
    // Initialize tooltips
    initializeTooltips();
    
    // Initialize form validation
    initializeFormValidation();
    
    // Initialize search and filters
    initializeSearchFilters();
    
    // Initialize table interactions
    initializeTableInteractions();
    
    // Initialize real-time updates
    initializeRealTimeUpdates();
}

/**
 * Initialize Bootstrap tooltips
 */
function initializeTooltips() {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Initialize form validation
 */
function initializeFormValidation() {
    // Bank account form validation
    $('#bank-account-form').on('submit', function(e) {
        if (!validateBankAccountForm()) {
            e.preventDefault();
            showAlert('Please correct the errors in the form.', 'danger');
            scrollToFirstError();
        }
    });

    // Real-time validation
    $('.form-control, .form-select').on('blur', function() {
        validateField($(this));
    });

    // Account number formatting
    $('#id_account_number').on('input', function() {
        formatAccountNumber($(this));
    });

    // IFSC code formatting
    $('#id_ifsc_code').on('input', function() {
        formatIFSCCode($(this));
    });

    // Opening balance validation
    $('#id_opening_balance').on('input', function() {
        validateAmount($(this));
    });
}

/**
 * Validate bank account form
 */
function validateBankAccountForm() {
    var isValid = true;
    
    // Required fields validation
    $('.form-control[required], .form-select[required]').each(function() {
        if (!validateField($(this))) {
            isValid = false;
        }
    });
    
    // Account number uniqueness check
    if (!validateAccountNumberUniqueness()) {
        isValid = false;
    }
    
    // Default account validation
    if (!validateDefaultAccountSettings()) {
        isValid = false;
    }
    
    return isValid;
}

/**
 * Validate individual field
 */
function validateField(field) {
    var value = field.val().trim();
    var isValid = true;
    
    // Remove existing error states
    field.removeClass('is-invalid');
    field.siblings('.invalid-feedback').remove();
    
    // Required field validation
    if (field.prop('required') && !value) {
        showFieldError(field, 'This field is required.');
        isValid = false;
    }
    
    // Specific field validations
    if (field.attr('id') === 'id_account_number' && value) {
        if (!validateAccountNumberFormat(value)) {
            showFieldError(field, 'Please enter a valid account number.');
            isValid = false;
        }
    }
    
    if (field.attr('id') === 'id_ifsc_code' && value) {
        if (!validateIFSCFormat(value)) {
            showFieldError(field, 'Please enter a valid IFSC/SWIFT code.');
            isValid = false;
        }
    }
    
    if (field.attr('id') === 'id_opening_balance' && value) {
        if (!validateAmountFormat(value)) {
            showFieldError(field, 'Please enter a valid amount.');
            isValid = false;
        }
    }
    
    return isValid;
}

/**
 * Show field error
 */
function showFieldError(field, message) {
    field.addClass('is-invalid');
    field.after('<div class="invalid-feedback">' + message + '</div>');
}

/**
 * Validate account number format
 */
function validateAccountNumberFormat(accountNumber) {
    // Basic validation - can be customized based on requirements
    return /^[0-9]{8,20}$/.test(accountNumber);
}

/**
 * Validate IFSC code format
 */
function validateIFSCFormat(ifscCode) {
    // IFSC code format: 4 letters + 7 alphanumeric
    return /^[A-Z]{4}0[A-Z0-9]{6}$/.test(ifscCode.toUpperCase());
}

/**
 * Validate amount format
 */
function validateAmountFormat(amount) {
    return /^\d+(\.\d{1,2})?$/.test(amount) && parseFloat(amount) >= 0;
}

/**
 * Format account number input
 */
function formatAccountNumber(field) {
    var value = field.val().replace(/[^0-9]/g, '');
    field.val(value);
}

/**
 * Format IFSC code input
 */
function formatIFSCCode(field) {
    var value = field.val().toUpperCase().replace(/[^A-Z0-9]/g, '');
    field.val(value);
}

/**
 * Validate amount input
 */
function validateAmount(field) {
    var value = field.val();
    if (value && !validateAmountFormat(value)) {
        showFieldError(field, 'Please enter a valid amount (e.g., 1000.50)');
    }
}

/**
 * Validate account number uniqueness via AJAX
 */
function validateAccountNumberUniqueness() {
    var accountNumber = $('#id_account_number').val();
    var accountId = $('#bank-account-form').data('account-id');
    
    if (!accountNumber) return true;
    
    // This would typically make an AJAX call to check uniqueness
    // For now, we'll assume it's valid
    return true;
}

/**
 * Validate default account settings
 */
function validateDefaultAccountSettings() {
    var isDefaultPayments = $('#id_is_default_for_payments').is(':checked');
    var isDefaultReceipts = $('#id_is_default_for_receipts').is(':checked');
    
    // Add any specific validation logic here
    return true;
}

/**
 * Initialize search and filters
 */
function initializeSearchFilters() {
    // Auto-submit form on filter change
    $('.search-filters-form select').on('change', function() {
        $('.search-filters-form').submit();
    });
    
    // Search with debounce
    var searchTimeout;
    $('.search-filters-form input[type="text"]').on('input', function() {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(function() {
            $('.search-filters-form').submit();
        }, 500);
    });
    
    // Clear filters
    $('.clear-filters').on('click', function(e) {
        e.preventDefault();
        window.location.href = window.location.pathname;
    });
}

/**
 * Initialize table interactions
 */
function initializeTableInteractions() {
    // Row selection
    $('.bank-accounts-table tbody tr').on('click', function(e) {
        if (!$(e.target).closest('.action-buttons').length) {
            var accountId = $(this).data('account-id');
            if (accountId) {
                window.location.href = '/bank-accounts/' + accountId + '/';
            }
        }
    });
    
    // Bulk actions
    $('.bulk-action-select').on('change', function() {
        var action = $(this).val();
        if (action) {
            performBulkAction(action);
        }
    });
    
    // Select all checkbox
    $('.select-all-accounts').on('change', function() {
        var isChecked = $(this).is(':checked');
        $('.account-checkbox').prop('checked', isChecked);
        updateBulkActionButton();
    });
    
    // Individual checkboxes
    $('.account-checkbox').on('change', function() {
        updateBulkActionButton();
    });
}

/**
 * Perform bulk action
 */
function performBulkAction(action) {
    var selectedAccounts = $('.account-checkbox:checked').map(function() {
        return $(this).val();
    }).get();
    
    if (selectedAccounts.length === 0) {
        showAlert('Please select at least one account.', 'warning');
        return;
    }
    
    if (confirm('Are you sure you want to perform this action on ' + selectedAccounts.length + ' account(s)?')) {
        // Submit bulk action form
        $('#bulk-action-form input[name="account_ids"]').val(selectedAccounts.join(','));
        $('#bulk-action-form input[name="action"]').val(action);
        $('#bulk-action-form').submit();
    }
}

/**
 * Update bulk action button state
 */
function updateBulkActionButton() {
    var selectedCount = $('.account-checkbox:checked').length;
    var bulkActionBtn = $('.bulk-action-btn');
    
    if (selectedCount > 0) {
        bulkActionBtn.prop('disabled', false).text('Apply to ' + selectedCount + ' account(s)');
    } else {
        bulkActionBtn.prop('disabled', true).text('Apply Action');
    }
}

/**
 * Initialize real-time updates
 */
function initializeRealTimeUpdates() {
    // Auto-refresh balance information every 30 seconds
    setInterval(function() {
        refreshAccountBalances();
    }, 30000);
    
    // Real-time balance updates on transaction form
    $('#id_amount, #id_transaction_type').on('input change', function() {
        updateBalancePreview();
    });
}

/**
 * Refresh account balances
 */
function refreshAccountBalances() {
    $('.balance-amount').each(function() {
        var balanceElement = $(this);
        var accountId = balanceElement.data('account-id');
        
        if (accountId) {
            $.ajax({
                url: '/bank-accounts/ajax/balance/' + accountId + '/',
                method: 'GET',
                success: function(data) {
                    balanceElement.text(data.balance_formatted);
                },
                error: function() {
                    console.log('Failed to refresh balance for account ' + accountId);
                }
            });
        }
    });
}

/**
 * Update balance preview in transaction form
 */
function updateBalancePreview() {
    var amount = parseFloat($('#id_amount').val()) || 0;
    var transactionType = $('#id_transaction_type').val();
    var currentBalance = parseFloat($('#current-balance').data('balance')) || 0;
    
    var newBalance;
    if (transactionType === 'credit') {
        newBalance = currentBalance + amount;
    } else {
        newBalance = currentBalance - amount;
    }
    
    $('#balance-preview').text('New Balance: ' + formatCurrency(newBalance));
}

/**
 * Format currency
 */
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'AED'
    }).format(amount);
}

/**
 * Show alert message
 */
function showAlert(message, type) {
    var alertHtml = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    `;
    
    $('.alert-container').html(alertHtml);
    
    // Auto-dismiss after 5 seconds
    setTimeout(function() {
        $('.alert').alert('close');
    }, 5000);
}

/**
 * Scroll to first error
 */
function scrollToFirstError() {
    var firstError = $('.is-invalid').first();
    if (firstError.length) {
        $('html, body').animate({
            scrollTop: firstError.offset().top - 100
        }, 500);
        firstError.focus();
    }
}

/**
 * Confirm delete action
 */
function confirmDelete(accountId, accountName) {
    if (confirm('Are you sure you want to delete the bank account "' + accountName + '"?\n\nThis action cannot be undone.')) {
        window.location.href = '/bank-accounts/' + accountId + '/delete/';
    }
}

/**
 * Toggle account status
 */
function toggleAccountStatus(accountId, currentStatus) {
    var newStatus = currentStatus === 'active' ? 'inactive' : 'active';
    var actionText = currentStatus === 'active' ? 'deactivate' : 'activate';
    
    if (confirm('Are you sure you want to ' + actionText + ' this account?')) {
        window.location.href = '/bank-accounts/' + accountId + '/toggle-status/';
    }
}

/**
 * Export accounts
 */
function exportAccounts(format) {
    var currentUrl = new URL(window.location);
    currentUrl.searchParams.set('export', format);
    window.location.href = currentUrl.toString();
}

/**
 * Initialize Select2 for enhanced dropdowns
 */
function initializeSelect2() {
    // Chart account selection
    $('#id_chart_account').select2({
        placeholder: 'Search for a bank account in Chart of Accounts...',
        allowClear: true,
        ajax: {
            url: '/bank-accounts/ajax/account-search/',
            dataType: 'json',
            delay: 250,
            data: function(params) {
                return {
                    q: params.term,
                    page: params.page
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
            cache: true
        },
        minimumInputLength: 2,
        templateResult: function(account) {
            if (account.loading) return account.text;
            if (!account.id) return account.text;
            
            return $(`
                <div class="account-option">
                    <strong>${account.account_code}</strong> - ${account.account_name}
                </div>
            `);
        },
        templateSelection: function(account) {
            if (!account.id) return account.text;
            return `${account.account_code} - ${account.account_name}`;
        }
    });

    // Currency selection
    $('#id_currency').select2({
        placeholder: 'Select currency...',
        allowClear: true
    });
}

/**
 * Initialize data tables for better table functionality
 */
function initializeDataTables() {
    if ($.fn.DataTable) {
        $('.bank-accounts-table').DataTable({
            pageLength: 25,
            order: [[0, 'asc']],
            responsive: true,
            language: {
                search: "Search accounts:",
                lengthMenu: "Show _MENU_ accounts per page",
                info: "Showing _START_ to _END_ of _TOTAL_ accounts",
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

/**
 * Initialize chart visualizations
 */
function initializeCharts() {
    // Balance distribution chart
    if (typeof Chart !== 'undefined' && $('#balanceChart').length) {
        var ctx = document.getElementById('balanceChart').getContext('2d');
        new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Current Accounts', 'Savings Accounts', 'Loan Accounts'],
                datasets: [{
                    data: [60, 25, 15],
                    backgroundColor: ['#667eea', '#4ade80', '#f59e0b']
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false
            }
        });
    }
}

// Export functions for global access
window.BankAccounts = {
    confirmDelete: confirmDelete,
    toggleAccountStatus: toggleAccountStatus,
    exportAccounts: exportAccounts,
    showAlert: showAlert
}; 