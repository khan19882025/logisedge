$(document).ready(function() {
    // Initialize form functionality
    initializeCashTransactionForm();
    
    // Load summary data
    loadSummaryData();
    
    // Account balance updates
    $('#id_from_account, #id_to_account').on('change', function() {
        updateAccountBalances();
    });
    
    // Transaction type change handling
    $('#id_transaction_type').on('change', function() {
        updateFormBasedOnType();
    });
    
    // Amount validation
    $('#id_amount').on('input', function() {
        validateAmount();
        updateSummaryCalculations();
    });
    
    // Location change for cash balance
    $('#id_location').on('input', function() {
        updateCashBalance();
    });
    
    // Form validation
    $('#cashTransactionForm').on('submit', function(e) {
        if (!validateForm()) {
            e.preventDefault();
            return false;
        }
    });
    
    // Post/Cancel buttons
    $('.post-btn').on('click', function() {
        const transactionId = $(this).data('transaction-id');
        postTransaction(transactionId);
    });
    
    $('.cancel-btn').on('click', function() {
        const transactionId = $(this).data('transaction-id');
        cancelTransaction(transactionId);
    });
    
    // Filter form auto-submit
    $('#filterForm select, #filterForm input[type="date"]').on('change', function() {
        $('#filterForm').submit();
    });
    
    // File upload preview
    $('#id_attachment').on('change', function() {
        previewFileUpload(this);
    });
    
    // Keyboard shortcuts
    $(document).on('keydown', function(e) {
        // Ctrl+S to save
        if (e.ctrlKey && e.key === 's') {
            e.preventDefault();
            $('#cashTransactionForm').submit();
        }
        
        // Ctrl+N for new transaction
        if (e.ctrlKey && e.key === 'n') {
            e.preventDefault();
            window.location.href = '/accounting/cash-transactions/create/';
        }
        
        // Ctrl+L for list view
        if (e.ctrlKey && e.key === 'l') {
            e.preventDefault();
            window.location.href = '/accounting/cash-transactions/';
        }
    });
    
    // Initialize tooltips
    $('[data-toggle="tooltip"]').tooltip();
    
    // Auto-hide alerts after 5 seconds
    setTimeout(function() {
        $('.alert').fadeOut('slow');
    }, 5000);
});

// Initialize cash transaction form
function initializeCashTransactionForm() {
    // Set default transaction type if not set
    if (!$('#id_transaction_type').val()) {
        $('#id_transaction_type').val('cash_out').trigger('change');
    }
    
    // Update form based on initial transaction type
    updateFormBasedOnType();
    
    // Add animation classes
    $('.cash-transaction-card').addClass('fade-in');
}

// Update form based on transaction type
function updateFormBasedOnType() {
    const transactionType = $('#id_transaction_type').val();
    
    if (transactionType === 'cash_in') {
        // Show To Account, hide From Account
        $('#fromAccountGroup').hide();
        $('#toAccountGroup').show();
        $('#id_to_account').prop('required', true);
        $('#id_from_account').prop('required', false);
        
        // Update labels and placeholders
        $('.amount-label').text('Amount Received');
        $('#id_amount').attr('placeholder', 'Enter amount received');
        
        // Update summary
        updateSummaryCalculations();
    } else if (transactionType === 'cash_out') {
        // Show From Account, hide To Account
        $('#fromAccountGroup').show();
        $('#toAccountGroup').hide();
        $('#id_from_account').prop('required', true);
        $('#id_to_account').prop('required', false);
        
        // Update labels and placeholders
        $('.amount-label').text('Amount Paid');
        $('#id_amount').attr('placeholder', 'Enter amount paid');
        
        // Update summary
        updateSummaryCalculations();
    }
}

// Update account balances
function updateAccountBalances() {
    const fromAccountId = $('#id_from_account').val();
    const toAccountId = $('#id_to_account').val();
    
    if (fromAccountId) {
        $.ajax({
            url: '/accounting/cash-transactions/ajax/account-balance/',
            method: 'GET',
            data: { account_id: fromAccountId },
            success: function(data) {
                const balanceClass = data.balance >= 0 ? 'positive' : 'negative';
                const balanceSign = data.balance >= 0 ? '+' : '';
                $('#fromAccountBalance').html(`
                    <small class="account-balance ${balanceClass}">
                        <i class="bi bi-wallet2"></i>
                        Balance: ${balanceSign}${formatCurrency(data.balance, data.currency_code)}
                    </small>
                `);
            },
            error: function(xhr, status, error) {
                $('#fromAccountBalance').html('<small class="text-danger">Error loading balance</small>');
            }
        });
    } else {
        $('#fromAccountBalance').html('');
    }
    
    if (toAccountId) {
        $.ajax({
            url: '/accounting/cash-transactions/ajax/account-balance/',
            method: 'GET',
            data: { account_id: toAccountId },
            success: function(data) {
                const balanceClass = data.balance >= 0 ? 'positive' : 'negative';
                const balanceSign = data.balance >= 0 ? '+' : '';
                $('#toAccountBalance').html(`
                    <small class="account-balance ${balanceClass}">
                        <i class="bi bi-wallet2"></i>
                        Balance: ${balanceSign}${formatCurrency(data.balance, data.currency_code)}
                    </small>
                `);
            },
            error: function(xhr, status, error) {
                $('#toAccountBalance').html('<small class="text-danger">Error loading balance</small>');
            }
        });
    } else {
        $('#toAccountBalance').html('');
    }
}

// Update cash balance at location
function updateCashBalance() {
    const location = $('#id_location').val();
    const currencyId = $('#id_currency').val() || 3;
    
    if (location) {
        $.ajax({
            url: '/accounting/cash-transactions/ajax/cash-balance/',
            method: 'GET',
            data: { 
                location: location,
                currency_id: currencyId
            },
            success: function(data) {
                const balanceClass = data.balance >= 0 ? 'positive' : 'negative';
                const balanceSign = data.balance >= 0 ? '+' : '';
                $('#cashBalanceInfo').html(`
                    <div class="alert alert-info">
                        <i class="bi bi-info-circle"></i>
                        Available cash at ${location}: ${balanceSign}${formatCurrency(data.balance, data.currency_code)}
                    </div>
                `);
            },
            error: function(xhr, status, error) {
                $('#cashBalanceInfo').html(`
                    <div class="alert alert-warning">
                        <i class="bi bi-exclamation-triangle"></i>
                        No cash balance record found for this location
                    </div>
                `);
            }
        });
    } else {
        $('#cashBalanceInfo').html('');
    }
}

// Validate amount
function validateAmount() {
    const amount = parseFloat($('#id_amount').val()) || 0;
    const amountField = $('#id_amount');
    
    // Remove previous validation classes
    amountField.removeClass('is-valid is-invalid');
    $('.amount-feedback').remove();
    
    if (amount <= 0) {
        amountField.addClass('is-invalid');
        amountField.after('<div class="invalid-feedback amount-feedback">Amount must be greater than zero.</div>');
        return false;
    } else {
        amountField.addClass('is-valid');
        return true;
    }
}

// Update summary calculations
function updateSummaryCalculations() {
    const amount = parseFloat($('#id_amount').val()) || 0;
    const transactionType = $('#id_transaction_type').val();
    
    $('#summaryAmount').text(formatCurrency(amount));
    $('#summaryType').text(transactionType === 'cash_in' ? 'Cash In' : 'Cash Out');
    
    // Update summary styling
    if (transactionType === 'cash_in') {
        $('#summaryAmount').removeClass('text-danger').addClass('text-success');
    } else {
        $('#summaryAmount').removeClass('text-success').addClass('text-danger');
    }
}

// Load summary data
function loadSummaryData() {
    $.ajax({
        url: '/accounting/cash-transactions/ajax/summary/',
        method: 'GET',
        success: function(data) {
            $('#totalTransactions').text(data.total_transactions);
            $('#totalCashIn').text(formatCurrency(data.total_cash_in));
            $('#totalCashOut').text(formatCurrency(data.total_cash_out));
            $('#netCashFlow').text(formatCurrency(data.net_cash_flow));
            
            // Update net cash flow color
            if (data.net_cash_flow >= 0) {
                $('#netCashFlow').removeClass('text-danger').addClass('text-success');
            } else {
                $('#netCashFlow').removeClass('text-success').addClass('text-danger');
            }
        },
        error: function(xhr, status, error) {
            console.error('Error loading summary data:', error);
        }
    });
}

// Form validation
function validateForm() {
    let isValid = true;
    
    // Clear previous errors
    $('.is-invalid').removeClass('is-invalid');
    $('.invalid-feedback').remove();
    
    // Required fields validation
    const requiredFields = [
        'id_transaction_date',
        'id_transaction_type',
        'id_category',
        'id_amount',
        'id_currency'
    ];
    
    requiredFields.forEach(function(fieldId) {
        const field = $(`#${fieldId}`);
        if (!field.val()) {
            field.addClass('is-invalid');
            field.after('<div class="invalid-feedback">This field is required.</div>');
            isValid = false;
        }
    });
    
    // Transaction type specific validation
    const transactionType = $('#id_transaction_type').val();
    if (transactionType === 'cash_in') {
        if (!$('#id_to_account').val()) {
            $('#id_to_account').addClass('is-invalid');
            $('#id_to_account').after('<div class="invalid-feedback">To Account is required for Cash In transactions.</div>');
            isValid = false;
        }
    } else if (transactionType === 'cash_out') {
        if (!$('#id_from_account').val()) {
            $('#id_from_account').addClass('is-invalid');
            $('#id_from_account').after('<div class="invalid-feedback">From Account is required for Cash Out transactions.</div>');
            isValid = false;
        }
    }
    
    // Amount validation
    if (!validateAmount()) {
        isValid = false;
    }
    
    return isValid;
}

// Post transaction
function postTransaction(transactionId) {
    if (confirm('Are you sure you want to post this transaction?')) {
        $.ajax({
            url: `/accounting/cash-transactions/${transactionId}/post/`,
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            },
            success: function(data) {
                if (data.success) {
                    showAlert(data.message, 'success');
                    setTimeout(function() {
                        location.reload();
                    }, 1500);
                } else {
                    showAlert(data.message, 'danger');
                }
            },
            error: function(xhr, status, error) {
                showAlert('Error posting transaction: ' + error, 'danger');
            }
        });
    }
}

// Cancel transaction
function cancelTransaction(transactionId) {
    if (confirm('Are you sure you want to cancel this transaction?')) {
        $.ajax({
            url: `/accounting/cash-transactions/${transactionId}/cancel/`,
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            },
            success: function(data) {
                if (data.success) {
                    showAlert(data.message, 'success');
                    setTimeout(function() {
                        location.reload();
                    }, 1500);
                } else {
                    showAlert(data.message, 'danger');
                }
            },
            error: function(xhr, status, error) {
                showAlert('Error cancelling transaction: ' + error, 'danger');
            }
        });
    }
}

// File upload preview
function previewFileUpload(input) {
    if (input.files && input.files[0]) {
        const file = input.files[0];
        const fileSize = (file.size / 1024 / 1024).toFixed(2); // MB
        
        // Validate file size (max 5MB)
        if (file.size > 5 * 1024 * 1024) {
            showAlert('File size must be less than 5MB', 'danger');
            input.value = '';
            return;
        }
        
        // Show file info
        $('#filePreview').html(`
            <div class="alert alert-info">
                <i class="bi bi-file-earmark"></i>
                <strong>${file.name}</strong> (${fileSize} MB)
            </div>
        `);
    } else {
        $('#filePreview').html('');
    }
}

// Show alert message
function showAlert(message, type) {
    const alertHtml = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    `;
    
    // Remove existing alerts
    $('.alert').remove();
    
    // Add new alert
    $('.cash-transaction-container').prepend(alertHtml);
    
    // Auto-hide after 5 seconds
    setTimeout(function() {
        $('.alert').fadeOut('slow');
    }, 5000);
}

// Format currency
function formatCurrency(amount, currencyCode = 'AED') {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: currencyCode,
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(amount);
}

// Get CSRF token from cookies
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

// Set loading state
function setLoadingState(button, isLoading) {
    if (isLoading) {
        button.prop('disabled', true);
        button.addClass('loading');
        button.html('<i class="bi bi-hourglass-split"></i> Processing...');
    } else {
        button.prop('disabled', false);
        button.removeClass('loading');
        button.html(button.data('original-text'));
    }
}

// Print transaction
function printTransaction(transactionId) {
    window.open(`/accounting/cash-transactions/${transactionId}/print/`, '_blank');
}

// Export transactions
function exportTransactions(format) {
    const currentUrl = new URL(window.location);
    currentUrl.searchParams.set('export', format);
    window.location.href = currentUrl.toString();
} 