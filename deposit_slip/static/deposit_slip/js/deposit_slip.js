// Deposit Slip JavaScript

$(document).ready(function() {
    // Initialize Select2
    $('.select2').select2({
        theme: 'bootstrap-5',
        width: '100%'
    });

    // Initialize tooltips
    $('[data-bs-toggle="tooltip"]').tooltip();

    // Voucher selection functionality
    initializeVoucherSelection();
    
    // Filter functionality
    initializeFilters();
    
    // Action buttons
    initializeActionButtons();
    
    // Load summary data
    loadSummaryData();
});

// Voucher Selection Functions
function initializeVoucherSelection() {
    // Select all vouchers checkbox
    $('#select-all-vouchers').on('change', function() {
        const isChecked = $(this).is(':checked');
        $('.voucher-checkbox').prop('checked', isChecked);
        updateSummary();
    });

    // Individual voucher checkboxes
    $(document).on('change', '.voucher-checkbox', function() {
        updateSummary();
        updateSelectAllCheckbox();
    });

    // Row click to select checkbox
    $(document).on('click', '.voucher-row', function(e) {
        if (!$(e.target).is('input[type="checkbox"]')) {
            const checkbox = $(this).find('.voucher-checkbox');
            checkbox.prop('checked', !checkbox.is(':checked'));
            checkbox.trigger('change');
        }
    });
}

function updateSummary() {
    let selectedCount = 0;
    let totalAmount = 0;
    let cashAmount = 0;
    let chequeAmount = 0;
    let otherAmount = 0;

    $('.voucher-checkbox:checked').each(function() {
        selectedCount++;
        const amount = parseFloat($(this).data('amount')) || 0;
        totalAmount += amount;
        
        const row = $(this).closest('.voucher-row');
        const paymentMode = row.find('td:nth-child(4) .badge').text().trim();
        
        if (paymentMode.includes('Cash')) {
            cashAmount += amount;
        } else if (paymentMode.includes('Cheque')) {
            chequeAmount += amount;
        } else {
            otherAmount += amount;
        }
    });

    // Update summary display
    $('#selected-count').text(selectedCount);
    $('#total-amount').text(totalAmount.toFixed(2) + ' AED');
    $('#cash-amount').text(cashAmount.toFixed(2) + ' AED');
    $('#cheque-amount').text(chequeAmount.toFixed(2) + ' AED');
}

function updateSelectAllCheckbox() {
    const totalCheckboxes = $('.voucher-checkbox').length;
    const checkedCheckboxes = $('.voucher-checkbox:checked').length;
    
    if (checkedCheckboxes === 0) {
        $('#select-all-vouchers').prop('indeterminate', false).prop('checked', false);
    } else if (checkedCheckboxes === totalCheckboxes) {
        $('#select-all-vouchers').prop('indeterminate', false).prop('checked', true);
    } else {
        $('#select-all-vouchers').prop('indeterminate', true);
    }
}

// Filter Functions
function initializeFilters() {
    // Filter vouchers button
    $('#filter-vouchers').on('click', function() {
        filterVouchers();
    });

    // Clear filters button
    $('#clear-filters').on('click', function() {
        clearFilters();
    });

    // Auto-filter on input change
    $('#id_payer_name, #id_receipt_mode').on('change', function() {
        filterVouchers();
    });

    // Date range filtering
    $('#id_date_from, #id_date_to').on('change', function() {
        filterVouchers();
    });
}

function filterVouchers() {
    const dateFrom = $('#id_date_from').val();
    const dateTo = $('#id_date_to').val();
    const payerName = $('#id_payer_name').val();
    const receiptMode = $('#id_receipt_mode').val();

    // Show loading state
    $('#vouchers-table tbody').addClass('loading');

    // AJAX call to get filtered vouchers
    $.ajax({
        url: '/deposit_slip/ajax/available-vouchers/',
        method: 'GET',
        data: {
            date_from: dateFrom,
            date_to: dateTo,
            payer_name: payerName,
            receipt_mode: receiptMode
        },
        success: function(response) {
            updateVouchersTable(response.vouchers);
        },
        error: function(xhr, status, error) {
            showAlert('Error loading vouchers: ' + error, 'danger');
        },
        complete: function() {
            $('#vouchers-table tbody').removeClass('loading');
        }
    });
}

function updateVouchersTable(vouchers) {
    const tbody = $('#vouchers-table tbody');
    tbody.empty();

    if (vouchers.length === 0) {
        tbody.append(`
            <tr>
                <td colspan="8" class="text-center text-muted py-4">
                    <i class="fas fa-inbox fa-2x mb-2"></i>
                    <p>No vouchers found matching the criteria.</p>
                </td>
            </tr>
        `);
        return;
    }

    vouchers.forEach(function(voucher) {
        const paymentModeClass = voucher.receipt_mode === 'Cash' ? 'bg-success' : 
                                voucher.receipt_mode === 'Cheque' ? 'bg-warning' : 'bg-info';
        const paymentModeIcon = voucher.receipt_mode === 'Cash' ? 'fa-money-bill' : 
                               voucher.receipt_mode === 'Cheque' ? 'fa-university' : 'fa-credit-card';

        const row = `
            <tr class="voucher-row" data-voucher-id="${voucher.id}">
                <td>
                    <input type="checkbox" name="selected_vouchers" value="${voucher.id}" 
                           class="form-check-input voucher-checkbox" 
                           data-amount="${voucher.amount}">
                </td>
                <td>
                    <span class="fw-bold text-primary">${voucher.voucher_number}</span>
                </td>
                <td>${voucher.payer_name}</td>
                <td>
                    <span class="badge ${paymentModeClass}">
                        <i class="fas ${paymentModeIcon}"></i>
                        ${voucher.receipt_mode}
                    </span>
                </td>
                <td class="text-end fw-bold">${parseFloat(voucher.amount).toFixed(2)} AED</td>
                <td>${voucher.reference_number || '-'}</td>
                <td>${formatDate(voucher.voucher_date)}</td>
                <td>
                    <span class="badge bg-success">
                        <i class="fas fa-check"></i> Received
                    </span>
                </td>
            </tr>
        `;
        tbody.append(row);
    });

    // Reinitialize event handlers
    updateSummary();
}

function clearFilters() {
    $('#id_date_from, #id_date_to, #id_payer_name').val('');
    $('#id_receipt_mode').val('');
    filterVouchers();
}

// Action Buttons
function initializeActionButtons() {
    // Submit deposit slip
    $(document).on('click', '.submit-slip, #submit-slip', function() {
        const pk = $(this).data('pk');
        submitDepositSlip(pk);
    });

    // Confirm deposit slip
    $(document).on('click', '.confirm-slip, #confirm-slip', function() {
        const pk = $(this).data('pk');
        confirmDepositSlip(pk);
    });

    // Save draft button
    $('#save-draft').on('click', function() {
        // Add a hidden field to indicate draft save
        if (!$('#save-as-draft').length) {
            $('<input>').attr({
                type: 'hidden',
                id: 'save-as-draft',
                name: 'save_as_draft',
                value: 'true'
            }).appendTo('#deposit-slip-form');
        }
        $('#deposit-slip-form').submit();
    });
}

function submitDepositSlip(pk) {
    if (!confirm('Are you sure you want to submit this deposit slip?')) {
        return;
    }

    $.ajax({
        url: `/deposit_slip/${pk}/submit/`,
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        },
        success: function(response) {
            if (response.success) {
                showAlert(response.message, 'success');
                setTimeout(function() {
                    location.reload();
                }, 1500);
            } else {
                showAlert(response.message, 'danger');
            }
        },
        error: function(xhr, status, error) {
            showAlert('Error submitting deposit slip: ' + error, 'danger');
        }
    });
}

function confirmDepositSlip(pk) {
    if (!confirm('Are you sure you want to confirm this deposit slip?')) {
        return;
    }

    $.ajax({
        url: `/deposit_slip/${pk}/confirm/`,
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        },
        success: function(response) {
            if (response.success) {
                showAlert(response.message, 'success');
                setTimeout(function() {
                    location.reload();
                }, 1500);
            } else {
                showAlert(response.message, 'danger');
            }
        },
        error: function(xhr, status, error) {
            showAlert('Error confirming deposit slip: ' + error, 'danger');
        }
    });
}

// Summary Data Loading
function loadSummaryData() {
    $.ajax({
        url: '/deposit_slip/ajax/summary/',
        method: 'GET',
        success: function(data) {
            $('#draft-count').text(data.draft_slips);
            $('#available-amount').text(data.available_amount.toFixed(2) + ' AED');
        },
        error: function(xhr, status, error) {
            console.error('Error loading summary data:', error);
        }
    });
}

// Utility Functions
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-GB');
}

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

function showAlert(message, type) {
    const alertHtml = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    // Remove existing alerts
    $('.alert').remove();
    
    // Add new alert at the top of the page
    $('.container-fluid').prepend(alertHtml);
    
    // Auto-dismiss after 5 seconds
    setTimeout(function() {
        $('.alert').fadeOut();
    }, 5000);
}

// Form Validation
function validateForm() {
    let isValid = true;
    const errors = [];

    // Check if deposit date is selected
    if (!$('#id_deposit_date').val()) {
        errors.push('Deposit date is required');
        isValid = false;
    }

    // Check if bank account is selected
    if (!$('#id_deposit_to').val()) {
        errors.push('Bank account is required');
        isValid = false;
    }

    // Check if at least one voucher is selected
    if ($('.voucher-checkbox:checked').length === 0) {
        errors.push('At least one receipt voucher must be selected');
        isValid = false;
    }

    if (!isValid) {
        showAlert('Please fix the following errors:<br>' + errors.join('<br>'), 'danger');
    }

    return isValid;
}

// Form submission
$('#deposit-slip-form').on('submit', function(e) {
    if (!validateForm()) {
        e.preventDefault();
        return false;
    }
    
    // Show loading state
    $(this).find('button[type="submit"]').prop('disabled', true).html('<i class="fas fa-spinner fa-spin"></i> Creating...');
});

// Keyboard shortcuts
$(document).on('keydown', function(e) {
    // Ctrl/Cmd + Enter to submit form
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        if ($('#deposit-slip-form').length) {
            $('#deposit-slip-form').submit();
        }
    }
    
    // Escape to clear filters
    if (e.key === 'Escape') {
        clearFilters();
    }
});

// Auto-save functionality (optional)
let autoSaveTimer;
function setupAutoSave() {
    $('input, select, textarea').on('change', function() {
        clearTimeout(autoSaveTimer);
        autoSaveTimer = setTimeout(function() {
            // Auto-save logic here if needed
            console.log('Auto-saving...');
        }, 2000);
    });
}

// Initialize auto-save if on create/edit page
if ($('#deposit-slip-form').length) {
    setupAutoSave();
} 