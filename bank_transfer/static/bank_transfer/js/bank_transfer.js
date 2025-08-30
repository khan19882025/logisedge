$(document).ready(function() {
    // Initialize enhanced dropdowns (without Select2 dependency)
    $('.select2').addClass('form-select').removeClass('select2');

    // Load summary data
    loadSummaryData();

    // Account balance updates
    $('#id_from_account, #id_to_account').on('change', function() {
        updateAccountBalances();
        updateCurrencyInfo();
    });

    // Amount and exchange rate calculations
    $('#id_amount, #id_exchange_rate').on('input', function() {
        updateSummaryCalculations();
    });

    // Template loading
    $('.load-template-btn').on('click', function() {
        const templateId = $(this).closest('.template-item').data('template-id');
        loadTemplate(templateId);
    });

    // Form validation
    $('#bankTransferForm').on('submit', function(e) {
        if (!validateForm()) {
            e.preventDefault();
            return false;
        }
    });

    // Complete/Cancel buttons
    $('.complete-btn').on('click', function() {
        const transferId = $(this).data('transfer-id');
        completeTransfer(transferId);
    });

    $('.cancel-btn').on('click', function() {
        const transferId = $(this).data('transfer-id');
        cancelTransfer(transferId);
    });

    // Filter form auto-submit
    $('#filterForm select, #filterForm input[type="date"]').on('change', function() {
        $('#filterForm').submit();
    });

    // Keyboard shortcuts
    $(document).on('keydown', function(e) {
        // Ctrl+S to save
        if (e.ctrlKey && e.key === 's') {
            e.preventDefault();
            $('#bankTransferForm').submit();
        }
        
        // Ctrl+N for new transfer
        if (e.ctrlKey && e.key === 'n') {
            e.preventDefault();
            window.location.href = '/accounting/bank-transfers/create/';
        }
        
        // Ctrl+L for list view
        if (e.ctrlKey && e.key === 'l') {
            e.preventDefault();
            window.location.href = '/accounting/bank-transfers/';
        }
    });

    // Initialize tooltips
    $('[data-toggle="tooltip"]').tooltip();

    // Auto-hide alerts after 5 seconds
    setTimeout(function() {
        $('.alert').fadeOut('slow');
    }, 5000);
});

// Load summary data via AJAX
function loadSummaryData() {
    $.ajax({
        url: '/accounting/bank-transfers/ajax/summary/',
        method: 'GET',
        success: function(data) {
            $('#totalTransfers').text(data.total_transfers);
            $('#pendingTransfers').text(data.pending_transfers);
            $('#completedTransfers').text(data.completed_transfers);
            $('#totalAmount').text(formatCurrency(data.total_amount));
        },
        error: function(xhr, status, error) {
            console.error('Error loading summary data:', error);
        }
    });
}

// Update account balances
function updateAccountBalances() {
    const fromAccountId = $('#id_from_account').val();
    const toAccountId = $('#id_to_account').val();

    if (fromAccountId) {
        $.ajax({
            url: '/accounting/bank-transfers/ajax/account-balance/',
            method: 'GET',
            data: { account_id: fromAccountId },
            success: function(data) {
                $('#fromAccountBalance').text(formatCurrency(data.balance, data.currency_code));
                $('#summaryFromBalance').text(formatCurrency(data.balance, data.currency_code));
            },
            error: function(xhr, status, error) {
                $('#fromAccountBalance').text('Error loading balance');
                $('#summaryFromBalance').text('Error loading balance');
            }
        });
    }

    if (toAccountId) {
        $.ajax({
            url: '/accounting/bank-transfers/ajax/account-balance/',
            method: 'GET',
            data: { account_id: toAccountId },
            success: function(data) {
                $('#toAccountBalance').text(formatCurrency(data.balance, data.currency_code));
                $('#summaryToBalance').text(formatCurrency(data.balance, data.currency_code));
            },
            error: function(xhr, status, error) {
                $('#toAccountBalance').text('Error loading balance');
                $('#summaryToBalance').text('Error loading balance');
            }
        });
    }
}

// Update currency information and exchange rate visibility
function updateCurrencyInfo() {
    const fromAccountId = $('#id_from_account').val();
    const toAccountId = $('#id_to_account').val();

    if (fromAccountId && toAccountId) {
        $.ajax({
            url: '/accounting/bank-transfers/ajax/account-currencies/',
            method: 'GET',
            data: { 
                from_account_id: fromAccountId,
                to_account_id: toAccountId
            },
            success: function(data) {
                if (data.is_multi_currency) {
                    $('#exchangeRateGroup').show();
                    $('#id_exchange_rate').prop('required', true);
                    $('#id_exchange_rate').attr('placeholder', 'Enter exchange rate');
                    
                    // Update currency dropdowns
                    $('#id_currency').val(data.from_currency.id).trigger('change');
                    
                    // Show multi-currency indicators
                    $('.currency-info').html(`
                        <small class="text-info">
                            <i class="fas fa-exchange-alt"></i>
                            Multi-currency transfer: ${data.from_currency.code} → ${data.to_currency.code}
                        </small>
                    `);
                } else {
                    $('#exchangeRateGroup').hide();
                    $('#id_exchange_rate').prop('required', false);
                    $('#id_exchange_rate').val('1.000000');
                    
                    // Update currency dropdown
                    $('#id_currency').val(data.from_currency.id).trigger('change');
                    
                    // Hide multi-currency indicators
                    $('.currency-info').html('');
                }
                
                updateSummaryCalculations();
            },
            error: function(xhr, status, error) {
                console.error('Error loading currency info:', error);
            }
        });
    }
}

// Update summary calculations
function updateSummaryCalculations() {
    const amount = parseFloat($('#id_amount').val()) || 0;
    const exchangeRate = parseFloat($('#id_exchange_rate').val()) || 1;
    
    $('#summaryTransferAmount').text(formatCurrency(amount));
    
    if (exchangeRate !== 1) {
        const convertedAmount = amount * exchangeRate;
        const fxGainLoss = convertedAmount - amount;
        
        $('#summaryConvertedAmount').show();
        $('#summaryConvertedValue').text(formatCurrency(convertedAmount));
        
        $('#summaryFXGainLoss').show();
        $('#summaryFXValue').text(formatCurrency(fxGainLoss));
        $('#summaryFXValue').removeClass('text-success text-danger').addClass(
            fxGainLoss >= 0 ? 'text-success' : 'text-danger'
        );
    } else {
        $('#summaryConvertedAmount').hide();
        $('#summaryFXGainLoss').hide();
    }
}

// Load template data
function loadTemplate(templateId) {
    $.ajax({
        url: `/accounting/bank-transfers/ajax/load-template/${templateId}/`,
        method: 'GET',
        success: function(data) {
            $('#id_from_account').val(data.from_account).trigger('change');
            $('#id_to_account').val(data.to_account).trigger('change');
            $('#id_amount').val(data.amount);
            $('#id_currency').val(data.currency).trigger('change');
            $('#id_narration').val(data.narration);
            
            // Show success message
            showAlert('Template loaded successfully!', 'success');
            
            // Update calculations
            updateAccountBalances();
            updateCurrencyInfo();
            updateSummaryCalculations();
        },
        error: function(xhr, status, error) {
            showAlert('Error loading template: ' + error, 'danger');
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
        'id_transfer_date',
        'id_transfer_type',
        'id_from_account',
        'id_to_account',
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
    
    // Amount validation
    const amount = parseFloat($('#id_amount').val());
    if (amount <= 0) {
        $('#id_amount').addClass('is-invalid');
        $('#id_amount').after('<div class="invalid-feedback">Amount must be greater than zero.</div>');
        isValid = false;
    }
    
    // Account validation
    const fromAccount = $('#id_from_account').val();
    const toAccount = $('#id_to_account').val();
    if (fromAccount && toAccount && fromAccount === toAccount) {
        $('#id_from_account, #id_to_account').addClass('is-invalid');
        $('#id_from_account').after('<div class="invalid-feedback">From and To accounts must be different.</div>');
        isValid = false;
    }
    
    // Exchange rate validation for multi-currency
    const exchangeRate = parseFloat($('#id_exchange_rate').val());
    if ($('#exchangeRateGroup').is(':visible') && (exchangeRate <= 0 || isNaN(exchangeRate))) {
        $('#id_exchange_rate').addClass('is-invalid');
        $('#id_exchange_rate').after('<div class="invalid-feedback">Exchange rate must be greater than zero.</div>');
        isValid = false;
    }
    
    return isValid;
}

// Complete transfer
function completeTransfer(transferId) {
    if (confirm('Are you sure you want to complete this transfer?')) {
        $.ajax({
            url: `/accounting/bank-transfers/${transferId}/complete/`,
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
                showAlert('Error completing transfer: ' + error, 'danger');
            }
        });
    }
}

// Cancel transfer
function cancelTransfer(transferId) {
    if (confirm('Are you sure you want to cancel this transfer?')) {
        $.ajax({
            url: `/accounting/bank-transfers/${transferId}/cancel/`,
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
                showAlert('Error cancelling transfer: ' + error, 'danger');
            }
        });
    }
}

// Show alert message
function showAlert(message, type) {
    const alertHtml = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="close" data-dismiss="alert" aria-label="Close">
                <span aria-hidden="true">&times;</span>
            </button>
        </div>
    `;
    
    // Remove existing alerts
    $('.alert').remove();
    
    // Add new alert at the top of the page
    $('.container-fluid').prepend(alertHtml);
    
    // Auto-hide after 5 seconds
    setTimeout(function() {
        $('.alert').fadeOut('slow');
    }, 5000);
}

// Format currency
function formatCurrency(amount, currencyCode = 'AED') {
    if (isNaN(amount)) return '-';
    
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

// Add loading state to buttons
function setLoadingState(button, isLoading) {
    if (isLoading) {
        button.prop('disabled', true);
        button.addClass('loading');
        button.html('<i class="fas fa-spinner fa-spin"></i> Processing...');
    } else {
        button.prop('disabled', false);
        button.removeClass('loading');
        button.html(button.data('original-text'));
    }
}

// Initialize loading states
$(document).on('click', 'button[type="submit"], .complete-btn, .cancel-btn', function() {
    const button = $(this);
    button.data('original-text', button.html());
    setLoadingState(button, true);
    
    // Reset loading state after 5 seconds (fallback)
    setTimeout(function() {
        setLoadingState(button, false);
    }, 5000);
});

// Auto-save draft functionality
let autoSaveTimer;
$('#bankTransferForm input, #bankTransferForm select, #bankTransferForm textarea').on('input change', function() {
    clearTimeout(autoSaveTimer);
    autoSaveTimer = setTimeout(function() {
        // Auto-save logic can be implemented here
        console.log('Auto-saving draft...');
    }, 3000);
});

// Print functionality
function printTransfer(transferId) {
    window.open(`/accounting/bank-transfers/${transferId}/print/`, '_blank');
}

// Export functionality
function exportTransfers(format) {
    const currentUrl = new URL(window.location);
    currentUrl.searchParams.set('export', format);
    window.location.href = currentUrl.toString();
}

// Keyboard navigation for table rows
$('.table tbody tr').on('click', function(e) {
    if (!$(e.target).closest('.action-buttons').length) {
        const transferId = $(this).find('.transfer-link').attr('href').split('/').slice(-2)[0];
        window.location.href = `/accounting/bank-transfers/${transferId}/`;
    }
});

// Add hover effect to table rows
$('.table tbody tr').hover(
    function() {
        $(this).addClass('table-hover');
    },
    function() {
        $(this).removeClass('table-hover');
    }
); 