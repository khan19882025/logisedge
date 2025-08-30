// Recurring Journal Entry JavaScript

$(document).ready(function() {
    // Initialize form functionality
    initializeForm();
    
    // Initialize line items functionality
    initializeLineItems();
    
    // Initialize scheduled dates preview
    initializeScheduledDates();
});

function initializeForm() {
    // Handle posting day change
    $('#id_posting_day').on('change', function() {
        toggleCustomDay();
    });
    
    // Handle form validation
    $('#recurring-entry-form').on('submit', function(e) {
        if (!validateForm()) {
            e.preventDefault();
            return false;
        }
    });
    
    // Handle auto-post toggle
    $('#id_auto_post').on('change', function() {
        if (this.checked) {
            showAutoPostWarning();
        }
    });
}

function initializeLineItems() {
    // Add new line item row
    $('.add-line-item-row').on('click', function() {
        addLineItemRow();
    });
    
    // Remove line item row
    $(document).on('click', '.remove-line-item-row', function() {
        removeLineItemRow($(this));
    });
    
    // Handle amount changes
    $(document).on('input', '.debit-amount, .credit-amount', function() {
        validateLineAmount($(this));
        calculateTotals();
    });
    
    // Handle account selection
    $(document).on('change', '.account-select', function() {
        validateLineItem($(this).closest('tr'));
    });
    
    // Initialize existing rows
    $('.line-item-row').each(function() {
        initializeLineItemRow($(this));
    });
}

function initializeScheduledDates() {
    // Update scheduled dates when form changes
    $('#id_frequency, #id_posting_day, #id_start_date, #id_end_date, #id_number_of_occurrences').on('change', function() {
        updateScheduledDates();
    });
    
    // Initial update
    updateScheduledDates();
}

// Form validation
function validateForm() {
    let isValid = true;
    
    // Check required fields
    $('.form-control[required]').each(function() {
        if (!$(this).val()) {
            $(this).addClass('is-invalid');
            isValid = false;
        } else {
            $(this).removeClass('is-invalid');
        }
    });
    
    // Check if at least 2 line items have data
    let linesWithData = 0;
    $('.line-item-row').each(function() {
        if (hasLineItemData($(this))) {
            linesWithData++;
        }
    });
    
    if (linesWithData < 2) {
        showAlert('At least 2 line items are required.', 'danger');
        isValid = false;
    }
    
    // Check if entry is balanced
    if (!isEntryBalanced()) {
        showAlert('Total debit must equal total credit.', 'danger');
        isValid = false;
    }
    
    // Check custom day validation
    if ($('#id_posting_day').val() === 'CUSTOM' && !$('#id_custom_day').val()) {
        $('#id_custom_day').addClass('is-invalid');
        showAlert('Custom day is required when posting day is set to "Custom".', 'danger');
        isValid = false;
    }
    
    return isValid;
}

// Line items functionality
function addLineItemRow() {
    const formset = $('.line-items-rows');
    const totalForms = parseInt($('#id_lines-TOTAL_FORMS').val());
    const maxForms = parseInt($('#id_lines-MAX_NUM_FORMS').val());
    
    if (totalForms >= maxForms) {
        showAlert('Maximum number of line items reached.', 'warning');
        return;
    }
    
    // Clone the last row
    const lastRow = $('.line-item-row').last();
    const newRow = lastRow.clone();
    
    // Clear values
    newRow.find('input, select').val('');
    newRow.find('.select2').remove();
    
    // Update form index
    newRow.find('input, select').each(function() {
        const name = $(this).attr('name');
        if (name) {
            $(this).attr('name', name.replace(/-\d+-/, '-' + totalForms + '-'));
            $(this).attr('id', $(this).attr('id').replace(/-\d+-/, '-' + totalForms + '-'));
        }
    });
    
    // Add remove button
    newRow.find('.col-actions').html(`
        <button type="button" class="btn btn-sm btn-danger remove-line-item-row">
            <i class="fas fa-trash"></i>
        </button>
    `);
    
    // Add to table
    formset.append(newRow);
    
    // Initialize the new row
    initializeLineItemRow(newRow);
    
    // Update form count
    $('#id_lines-TOTAL_FORMS').val(totalForms + 1);
    
    // Recalculate totals
    calculateTotals();
}

function removeLineItemRow(button) {
    const row = button.closest('tr');
    const totalForms = parseInt($('#id_lines-TOTAL_FORMS').val());
    
    if (totalForms <= 2) {
        showAlert('At least 2 line items are required.', 'warning');
        return;
    }
    
    row.remove();
    $('#id_lines-TOTAL_FORMS').val(totalForms - 1);
    
    // Recalculate totals
    calculateTotals();
}

function initializeLineItemRow(row) {
    // Initialize select2 for account field
    const accountSelect = row.find('.account-select');
    if (accountSelect.length && !accountSelect.hasClass('select2-hidden-accessible')) {
        accountSelect.select2({
            placeholder: 'Search for an account...',
            allowClear: true,
            ajax: {
                url: '/accounting/recurring-journal-entry/ajax/account-search/',
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
    }
}

function validateLineAmount(input) {
    const row = input.closest('tr');
    const debitInput = row.find('.debit-amount');
    const creditInput = row.find('.credit-input');
    
    const debitValue = parseFloat(debitInput.val()) || 0;
    const creditValue = parseFloat(creditInput.val()) || 0;
    
    // Ensure only one amount is entered
    if (debitValue > 0 && creditValue > 0) {
        showAlert('A line item cannot have both debit and credit amounts.', 'warning');
        if (input.hasClass('debit-amount')) {
            creditInput.val('');
        } else {
            debitInput.val('');
        }
    }
    
    // Ensure at least one amount is entered
    if (debitValue === 0 && creditValue === 0) {
        input.addClass('is-invalid');
    } else {
        input.removeClass('is-invalid');
    }
}

function validateLineItem(row) {
    const account = row.find('.account-select').val();
    const debit = parseFloat(row.find('.debit-amount').val()) || 0;
    const credit = parseFloat(row.find('.credit-amount').val()) || 0;
    
    let isValid = true;
    
    if (!account) {
        row.find('.account-select').addClass('is-invalid');
        isValid = false;
    } else {
        row.find('.account-select').removeClass('is-invalid');
    }
    
    if (debit === 0 && credit === 0) {
        row.find('.debit-amount, .credit-amount').addClass('is-invalid');
        isValid = false;
    } else {
        row.find('.debit-amount, .credit-amount').removeClass('is-invalid');
    }
    
    return isValid;
}

function hasLineItemData(row) {
    const account = row.find('.account-select').val();
    const debit = parseFloat(row.find('.debit-amount').val()) || 0;
    const credit = parseFloat(row.find('.credit-amount').val()) || 0;
    
    return account && (debit > 0 || credit > 0);
}

// Calculate totals
function calculateTotals() {
    let totalDebit = 0;
    let totalCredit = 0;
    
    $('.line-item-row').each(function() {
        const debit = parseFloat($(this).find('.debit-amount').val()) || 0;
        const credit = parseFloat($(this).find('.credit-amount').val()) || 0;
        
        totalDebit += debit;
        totalCredit += credit;
    });
    
    // Update display
    $('#total-debit').text(totalDebit.toFixed(2));
    $('#total-credit').text(totalCredit.toFixed(2));
    
    // Update balance
    const difference = totalDebit - totalCredit;
    const balanceElement = $('#balance-difference');
    
    if (Math.abs(difference) < 0.01) {
        balanceElement.text('Balanced').removeClass('unbalanced').addClass('balanced');
    } else {
        balanceElement.text('Unbalanced: ' + difference.toFixed(2)).removeClass('balanced').addClass('unbalanced');
    }
    
    return Math.abs(difference) < 0.01;
}

function isEntryBalanced() {
    return calculateTotals();
}

// Scheduled dates functionality
function updateScheduledDates() {
    const frequency = $('#id_frequency').val();
    const postingDay = $('#id_posting_day').val();
    const startDate = $('#id_start_date').val();
    const endDate = $('#id_end_date').val();
    const occurrences = $('#id_number_of_occurrences').val();
    
    if (!frequency || !postingDay || !startDate) {
        $('#scheduled-dates').html('<p class="text-muted">Complete the form above to see scheduled dates</p>');
        return;
    }
    
    // Show loading
    $('#scheduled-dates').html('<p class="text-muted">Calculating scheduled dates...</p>');
    
    // Calculate next few dates
    const dates = calculateScheduledDates(frequency, postingDay, startDate, endDate, occurrences);
    
    if (dates.length === 0) {
        $('#scheduled-dates').html('<p class="text-muted">No scheduled dates found</p>');
        return;
    }
    
    // Display dates
    let html = '';
    dates.slice(0, 5).forEach(function(date, index) {
        const isToday = date === new Date().toISOString().split('T')[0];
        const isPast = date < new Date().toISOString().split('T')[0];
        
        let badgeClass = 'bg-info';
        let badgeText = 'Upcoming';
        
        if (isToday) {
            badgeClass = 'bg-danger';
            badgeText = 'Today';
        } else if (isPast) {
            badgeClass = 'bg-warning';
            badgeText = 'Overdue';
        }
        
        html += `
            <div class="scheduled-date-item">
                <div class="date-info">
                    <div class="date">${formatDate(date)}</div>
                    <small class="text-muted">${getDayName(date)}</small>
                </div>
                <span class="badge ${badgeClass}">${badgeText}</span>
            </div>
        `;
    });
    
    $('#scheduled-dates').html(html);
}

function calculateScheduledDates(frequency, postingDay, startDate, endDate, occurrences) {
    const dates = [];
    let currentDate = new Date(startDate);
    let count = 0;
    const maxCount = occurrences ? parseInt(occurrences) : 12; // Show max 12 dates if no limit
    
    while (count < maxCount) {
        if (endDate && currentDate > new Date(endDate)) {
            break;
        }
        
        dates.push(currentDate.toISOString().split('T')[0]);
        
        // Calculate next date based on frequency
        switch (frequency) {
            case 'DAILY':
                currentDate.setDate(currentDate.getDate() + 1);
                break;
            case 'WEEKLY':
                currentDate.setDate(currentDate.getDate() + 7);
                break;
            case 'MONTHLY':
                currentDate.setMonth(currentDate.getMonth() + 1);
                break;
            case 'QUARTERLY':
                currentDate.setMonth(currentDate.getMonth() + 3);
                break;
            case 'ANNUALLY':
                currentDate.setFullYear(currentDate.getFullYear() + 1);
                break;
        }
        
        count++;
    }
    
    return dates;
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric', 
        year: 'numeric' 
    });
}

function getDayName(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { weekday: 'long' });
}

// Utility functions
function toggleCustomDay() {
    const postingDay = $('#id_posting_day').val();
    const customDayField = $('#id_custom_day').closest('.col-md-4');
    
    if (postingDay === 'CUSTOM') {
        customDayField.show();
        $('#id_custom_day').prop('required', true);
    } else {
        customDayField.hide();
        $('#id_custom_day').prop('required', false);
    }
}

function showAutoPostWarning() {
    showAlert('Auto-post will automatically create and post journal entries when they are due. Make sure your template is correct before enabling this feature.', 'warning');
}

function showAlert(message, type) {
    const alertHtml = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    `;
    
    // Remove existing alerts
    $('.alert').remove();
    
    // Add new alert at the top of the form
    $('#recurring-entry-form').prepend(alertHtml);
    
    // Auto-dismiss after 5 seconds
    setTimeout(function() {
        $('.alert').fadeOut();
    }, 5000);
}

// Keyboard navigation
$(document).on('keydown', '.line-item-row input', function(e) {
    if (e.key === 'Enter') {
        e.preventDefault();
        const currentRow = $(this).closest('tr');
        const nextRow = currentRow.next('.line-item-row');
        
        if (nextRow.length) {
            nextRow.find('input:first').focus();
        } else {
            // Add new row if at the end
            addLineItemRow();
            $('.line-item-row').last().find('input:first').focus();
        }
    }
    
    if (e.key === 'Tab' && e.shiftKey === false) {
        const currentRow = $(this).closest('tr');
        const nextRow = currentRow.next('.line-item-row');
        
        if (!nextRow.length && $(this).is(':last-child')) {
            e.preventDefault();
            addLineItemRow();
            $('.line-item-row').last().find('input:first').focus();
        }
    }
});

// Form submission handling
$('#recurring-entry-form').on('submit', function() {
    const submitBtn = $(this).find('button[type="submit"]');
    const originalText = submitBtn.data('original-text');
    
    // Show loading state
    submitBtn.prop('disabled', true);
    submitBtn.html('<i class="fas fa-spinner fa-spin"></i> Saving...');
    
    // Re-enable after 10 seconds (in case of error)
    setTimeout(function() {
        submitBtn.prop('disabled', false);
        submitBtn.html('<i class="fas fa-save"></i> ' + originalText);
    }, 10000);
}); 