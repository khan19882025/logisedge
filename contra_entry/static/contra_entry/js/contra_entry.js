// Contra Entry JavaScript

$(document).ready(function() {
    // Initialize contra entry functionality
    initContraEntry();
});

function initContraEntry() {
    // Initialize form validation
    initFormValidation();
    
    // Initialize autocomplete
    initAutocomplete();
    
    // Initialize dynamic form handling
    initDynamicForms();
    
    // Initialize balance calculation
    initBalanceCalculation();
    
    // Initialize search functionality
    initSearch();
}

// Form Validation
function initFormValidation() {
    $('.contra-entry-form').on('submit', function(e) {
        if (!validateContraEntryForm()) {
            e.preventDefault();
            return false;
        }
    });
    
    // Real-time validation for amount fields
    $('.debit-amount, .credit-amount').on('input', function() {
        validateAmountField($(this));
    });
    
    // Ensure only one amount field is filled per row
    $('.debit-amount, .credit-amount').on('input', function() {
        const row = $(this).closest('tr');
        const debitField = row.find('.debit-amount');
        const creditField = row.find('.credit-amount');
        
        if ($(this).hasClass('debit-amount') && $(this).val()) {
            creditField.val('').prop('readonly', true);
        } else if ($(this).hasClass('credit-amount') && $(this).val()) {
            debitField.val('').prop('readonly', true);
        } else {
            debitField.prop('readonly', false);
            creditField.prop('readonly', false);
        }
    });
}

function validateContraEntryForm() {
    let isValid = true;
    const errors = [];
    
    // Check if we have at least 2 entries
    const validEntries = $('.entries-table tbody tr').filter(function() {
        return !$(this).hasClass('empty-form') && 
               ($(this).find('.debit-amount').val() || $(this).find('.credit-amount').val());
    });
    
    if (validEntries.length < 2) {
        errors.push('At least two entries are required (one debit, one credit).');
        isValid = false;
    }
    
    // Check if each entry has an account selected
    validEntries.each(function() {
        const accountField = $(this).find('.account-select');
        if (!accountField.val()) {
            errors.push('All entries must have an account selected.');
            isValid = false;
            return false;
        }
    });
    
    // Check if debit equals credit
    const totals = calculateTotals();
    if (totals.debit !== totals.credit) {
        errors.push(`Total debit (${totals.debit.toFixed(2)}) must equal total credit (${totals.credit.toFixed(2)}).`);
        isValid = false;
    }
    
    // Check if we have at least one debit and one credit
    const hasDebit = validEntries.filter(function() {
        return $(this).find('.debit-amount').val();
    }).length > 0;
    
    const hasCredit = validEntries.filter(function() {
        return $(this).find('.credit-amount').val();
    }).length > 0;
    
    if (!hasDebit) {
        errors.push('At least one debit entry is required.');
        isValid = false;
    }
    
    if (!hasCredit) {
        errors.push('At least one credit entry is required.');
        isValid = false;
    }
    
    // Display errors
    if (!isValid) {
        showValidationErrors(errors);
    } else {
        clearValidationErrors();
    }
    
    return isValid;
}

function validateAmountField(field) {
    const value = parseFloat(field.val());
    const row = field.closest('tr');
    
    if (field.val() && (isNaN(value) || value <= 0)) {
        field.addClass('is-invalid');
        row.find('.invalid-feedback').remove();
        row.append('<div class="invalid-feedback">Amount must be greater than zero.</div>');
    } else {
        field.removeClass('is-invalid');
        row.find('.invalid-feedback').remove();
    }
}

function showValidationErrors(errors) {
    // Remove existing error display
    $('.validation-errors').remove();
    
    // Create error display
    const errorHtml = `
        <div class="validation-errors alert alert-danger">
            <h6>Please correct the following errors:</h6>
            <ul>
                ${errors.map(error => `<li>${error}</li>`).join('')}
            </ul>
        </div>
    `;
    
    $('.contra-entry-form').prepend(errorHtml);
    
    // Scroll to top
    $('html, body').animate({
        scrollTop: $('.validation-errors').offset().top - 100
    }, 500);
}

function clearValidationErrors() {
    $('.validation-errors').remove();
    $('.is-invalid').removeClass('is-invalid');
    $('.invalid-feedback').remove();
}

// Autocomplete
function initAutocomplete() {
    $('.account-select').autocomplete({
        source: function(request, response) {
            $.ajax({
                url: '/accounting/contra-entry/ajax/account-search/',
                dataType: 'json',
                data: {
                    q: request.term
                },
                success: function(data) {
                    response(data.results);
                }
            });
        },
        minLength: 2,
        select: function(event, ui) {
            $(this).val(ui.item.text);
            return false;
        }
    }).autocomplete('instance')._renderItem = function(ul, item) {
        return $('<li>')
            .append('<div><strong>' + item.account_code + '</strong> - ' + item.account_name + '</div>')
            .appendTo(ul);
    };
}

// Dynamic Forms
function initDynamicForms() {
    // Add new entry row
    $('.add-entry-row').on('click', function() {
        addEntryRow();
    });
    
    // Remove entry row
    $(document).on('click', '.remove-entry-row', function() {
        if ($('.entries-table tbody tr').length > 2) {
            $(this).closest('tr').remove();
            updateBalanceSummary();
        } else {
            alert('At least two entries are required.');
        }
    });
    
    // Handle formset management
    if (typeof django !== 'undefined' && django.jQuery) {
        django.jQuery(document).on('formset:added', function(event, $row, formsetName) {
            if (formsetName === 'entries') {
                initRow($row);
            }
        });
    }
}

function addEntryRow() {
    const tbody = $('.entries-table tbody');
    const newRow = `
        <tr class="entry-row">
            <td>
                <select class="form-control account-select" name="entries-__prefix__-account" required>
                    <option value="">Select Account</option>
                </select>
            </td>
            <td>
                <div class="amount-input debit">
                    <input type="number" class="form-control debit-amount" name="entries-__prefix__-debit" 
                           step="0.01" min="0.01" placeholder="0.00">
                </div>
            </td>
            <td>
                <div class="amount-input credit">
                    <input type="number" class="form-control credit-amount" name="entries-__prefix__-credit" 
                           step="0.01" min="0.01" placeholder="0.00">
                </div>
            </td>
            <td>
                <button type="button" class="btn btn-sm btn-danger remove-entry-row">
                    <i class="fas fa-trash"></i>
                </button>
            </td>
        </tr>
    `;
    
    tbody.append(newRow);
    initRow(tbody.find('tr:last'));
    updateBalanceSummary();
}

function initRow(row) {
    // Initialize autocomplete for new row
    row.find('.account-select').autocomplete({
        source: function(request, response) {
            $.ajax({
                url: '/accounting/contra-entry/ajax/account-search/',
                dataType: 'json',
                data: { q: request.term },
                success: function(data) {
                    response(data.results);
                }
            });
        },
        minLength: 2,
        select: function(event, ui) {
            $(this).val(ui.item.text);
            return false;
        }
    });
    
    // Initialize amount validation
    row.find('.debit-amount, .credit-amount').on('input', function() {
        validateAmountField($(this));
        updateBalanceSummary();
    });
}

// Balance Calculation
function initBalanceCalculation() {
    // Calculate balance on page load
    updateBalanceSummary();
    
    // Recalculate on amount changes
    $(document).on('input', '.debit-amount, .credit-amount', function() {
        updateBalanceSummary();
    });
}

function calculateTotals() {
    let totalDebit = 0;
    let totalCredit = 0;
    
    $('.entries-table tbody tr').each(function() {
        const debitVal = parseFloat($(this).find('.debit-amount').val()) || 0;
        const creditVal = parseFloat($(this).find('.credit-amount').val()) || 0;
        
        totalDebit += debitVal;
        totalCredit += creditVal;
    });
    
    return { debit: totalDebit, credit: totalCredit };
}

function updateBalanceSummary() {
    const totals = calculateTotals();
    const difference = Math.abs(totals.debit - totals.credit);
    const isBalanced = totals.debit === totals.credit;
    
    // Update summary display
    $('.total-debit').text(totals.debit.toFixed(2));
    $('.total-credit').text(totals.credit.toFixed(2));
    $('.difference').text(difference.toFixed(2));
    
    // Update balance status
    const balanceStatus = $('.balance-status');
    if (isBalanced) {
        balanceStatus.removeClass('unbalanced').addClass('balanced')
            .html('<i class="fas fa-check-circle"></i> Balanced');
    } else {
        balanceStatus.removeClass('balanced').addClass('unbalanced')
            .html('<i class="fas fa-exclamation-triangle"></i> Not Balanced');
    }
    
    // Update row styling
    $('.entries-table tbody tr').each(function() {
        const debitVal = $(this).find('.debit-amount').val();
        const creditVal = $(this).find('.credit-amount').val();
        
        $(this).removeClass('debit credit');
        if (debitVal) {
            $(this).addClass('debit');
        } else if (creditVal) {
            $(this).addClass('credit');
        }
    });
}

// Search Functionality
function initSearch() {
    // Auto-submit search form on change
    $('.search-form select, .search-form input[type="date"]').on('change', function() {
        $('.search-form').submit();
    });
    
    // Clear search
    $('.clear-search').on('click', function() {
        $('.search-form input[type="text"]').val('');
        $('.search-form select').val('');
        $('.search-form input[type="date"]').val('');
        $('.search-form').submit();
    });
}

// AJAX Functions
function loadSummaryStats() {
    $.ajax({
        url: '/accounting/contra-entry/ajax/summary/',
        dataType: 'json',
        success: function(data) {
            if (data.success) {
                updateSummaryDisplay(data.summary);
            }
        }
    });
}

function updateSummaryDisplay(summary) {
    $('.total-entries-count').text(summary.total_entries);
    $('.draft-entries-count').text(summary.draft_entries);
    $('.posted-entries-count').text(summary.posted_entries);
    $('.cancelled-entries-count').text(summary.cancelled_entries);
    $('.total-debit-summary').text(summary.total_debit.toFixed(2));
    $('.total-credit-summary').text(summary.total_credit.toFixed(2));
}

// Action Functions
function postContraEntry(pk) {
    if (confirm('Are you sure you want to post this contra entry?')) {
        $.post(`/accounting/contra-entry/${pk}/post/`, {
            'csrfmiddlewaretoken': $('[name=csrfmiddlewaretoken]').val()
        })
        .done(function() {
            location.reload();
        })
        .fail(function() {
            alert('Error posting contra entry.');
        });
    }
}

function cancelContraEntry(pk) {
    if (confirm('Are you sure you want to cancel this contra entry?')) {
        $.post(`/accounting/contra-entry/${pk}/cancel/`, {
            'csrfmiddlewaretoken': $('[name=csrfmiddlewaretoken]').val()
        })
        .done(function() {
            location.reload();
        })
        .fail(function() {
            alert('Error cancelling contra entry.');
        });
    }
}

function deleteContraEntry(pk) {
    if (confirm('Are you sure you want to delete this contra entry? This action cannot be undone.')) {
        window.location.href = `/accounting/contra-entry/${pk}/delete/`;
    }
}

// Print Function
function printContraEntry(pk) {
    window.open(`/accounting/contra-entry/${pk}/print/`, '_blank');
}

// Utility Functions
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-AE', {
        style: 'currency',
        currency: 'AED'
    }).format(amount);
}

function showLoading(element) {
    element.addClass('loading');
}

function hideLoading(element) {
    element.removeClass('loading');
}

// Export functions for global access
window.ContraEntry = {
    init: initContraEntry,
    validateForm: validateContraEntryForm,
    calculateTotals: calculateTotals,
    updateBalanceSummary: updateBalanceSummary,
    postEntry: postContraEntry,
    cancelEntry: cancelContraEntry,
    deleteEntry: deleteContraEntry,
    printEntry: printContraEntry,
    formatCurrency: formatCurrency
}; 