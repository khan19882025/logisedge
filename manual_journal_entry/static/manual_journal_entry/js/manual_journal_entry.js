/**
 * Manual Journal Entry JavaScript
 * Handles the interactive functionality for the journal entry form
 */

$(document).ready(function() {
    // Initialize the form
    initJournalEntryForm();
    
    // Set up event listeners
    setupEventListeners();
    
    // Calculate initial totals
    calculateTotals();
});

function initJournalEntryForm() {
    console.log('Initializing Manual Journal Entry form...');
    
    // Initialize Select2 for account fields
    initializeSelect2();
    
    // Set up form validation
    setupFormValidation();
    
    // Enable keyboard navigation
    setupKeyboardNavigation();
}

function setupEventListeners() {
    // Add row button
    $(document).on('click', '.add-line-item-row', function() {
        addNewRow();
    });
    
    // Remove row button
    $(document).on('click', '.remove-line-item-row', function() {
        removeRow($(this));
    });
    
    // Amount field changes
    $(document).on('input', '.debit-amount, .credit-amount', function() {
        validateLineAmount(this);
        calculateTotals();
    });
    
    // Account selection changes
    $(document).on('change', '.account-select', function() {
        validateAccountSelection(this);
    });
    
    // Form submission
    $('#journal-entry-form').on('submit', function(e) {
        if (!validateForm()) {
            e.preventDefault();
            showValidationErrors();
        }
    });
    
    // Tab navigation for speed entry
    setupTabNavigation();
}

function initializeSelect2() {
    // Initialize Select2 for existing account fields
    $('.account-select').select2({
        placeholder: 'Search for an account...',
        allowClear: true,
        ajax: {
            url: '/accounting/manual-journal-entry/ajax/account-search/',
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

function addNewRow() {
    console.log('Adding new row...');
    
    // Get the current number of forms
    var totalForms = parseInt($('#id_entries-TOTAL_FORMS').val());
    var maxForms = parseInt($('#id_entries-MAX_NUM_FORMS').val());
    
    if (totalForms >= maxForms) {
        showAlert('Maximum number of line items reached (' + maxForms + ')', 'warning');
        return;
    }
    
    // Clone the last row
    var lastRow = $('.line-item-row:last');
    var newRow = lastRow.clone();
    
    // Clear the values
    newRow.find('input, select').val('');
    newRow.find('.select2').remove();
    
    // Update the form index
    newRow.find('input, select').each(function() {
        var name = $(this).attr('name');
        if (name) {
            var newName = name.replace(/entries-\d+/, 'entries-' + totalForms);
            $(this).attr('name', newName);
        }
        
        var id = $(this).attr('id');
        if (id) {
            var newId = id.replace(/entries-\d+/, 'entries-' + totalForms);
            $(this).attr('id', newId);
        }
    });
    
    // Add remove button if not present
    if (newRow.find('.remove-line-item-row').length === 0) {
        newRow.find('.col-actions').html(`
            <button type="button" class="btn btn-sm btn-danger remove-line-item-row">
                <i class="fas fa-trash"></i>
            </button>
        `);
    }
    
    // Add the new row with animation
    newRow.addClass('new-row');
    $('.line-items-rows').append(newRow);
    
    // Initialize Select2 for the new row
    newRow.find('.account-select').select2({
        placeholder: 'Search for an account...',
        allowClear: true,
        ajax: {
            url: '/manual-journal-entry/ajax/account-search/',
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
    
    // Update the total forms count
    $('#id_entries-TOTAL_FORMS').val(totalForms + 1);
    
    // Remove animation class after animation completes
    setTimeout(function() {
        newRow.removeClass('new-row');
    }, 300);
    
    // Focus on the first field of the new row
    newRow.find('.account-select').select2('open');
    
    console.log('New row added successfully');
}

function removeRow(button) {
    console.log('Removing row...');
    
    var row = button.closest('.line-item-row');
    var totalForms = parseInt($('#id_entries-TOTAL_FORMS').val());
    
    if (totalForms <= 2) {
        showAlert('At least 2 line items are required', 'warning');
        return;
    }
    
    // Add removal animation
    row.addClass('removing');
    
    setTimeout(function() {
        row.remove();
        
        // Update form indices
        updateFormIndices();
        
        // Update total forms count
        $('#id_entries-TOTAL_FORMS').val(totalForms - 1);
        
        // Recalculate totals
        calculateTotals();
        
        console.log('Row removed successfully');
    }, 300);
}

function updateFormIndices() {
    $('.line-item-row').each(function(index) {
        $(this).find('input, select').each(function() {
            var name = $(this).attr('name');
            if (name) {
                var newName = name.replace(/entries-\d+/, 'entries-' + index);
                $(this).attr('name', newName);
            }
            
            var id = $(this).attr('id');
            if (id) {
                var newId = id.replace(/entries-\d+/, 'entries-' + index);
                $(this).attr('id', newId);
            }
        });
    });
}

function validateLineAmount(field) {
    var row = $(field).closest('.line-item-row');
    var debitField = row.find('.debit-amount');
    var creditField = row.find('.credit-field');
    
    var debitValue = parseFloat(debitField.val()) || 0;
    var creditValue = parseFloat(creditField.val()) || 0;
    
    // Clear previous validation
    debitField.removeClass('is-invalid is-valid');
    creditField.removeClass('is-invalid is-valid');
    
    // Validate that at least one amount is provided
    if (debitValue === 0 && creditValue === 0) {
        debitField.addClass('is-invalid');
        creditField.addClass('is-invalid');
        return false;
    }
    
    // Validate that not both amounts are provided
    if (debitValue > 0 && creditValue > 0) {
        debitField.addClass('is-invalid');
        creditField.addClass('is-invalid');
        return false;
    }
    
    // Mark as valid
    if (debitValue > 0) {
        debitField.addClass('is-valid');
    } else if (creditValue > 0) {
        creditField.addClass('is-valid');
    }
    
    return true;
}

function calculateTotals() {
    console.log('Calculating totals...');
    
    var totalDebit = 0;
    var totalCredit = 0;
    
    $('.line-item-row').each(function() {
        var debitValue = parseFloat($(this).find('.debit-amount').val()) || 0;
        var creditValue = parseFloat($(this).find('.credit-amount').val()) || 0;
        
        totalDebit += debitValue;
        totalCredit += creditValue;
    });
    
    // Update display
    $('#total-debit').text(formatCurrency(totalDebit));
    $('#total-credit').text(formatCurrency(totalCredit));
    
    // Check balance
    var difference = totalDebit - totalCredit;
    var balanceElement = $('#balance-difference');
    
    if (Math.abs(difference) < 0.01) {
        balanceElement.text('Balanced').removeClass('unbalanced').addClass('balanced');
    } else {
        balanceElement.text(formatCurrency(difference)).removeClass('balanced').addClass('unbalanced');
    }
    
    console.log('Totals calculated: Debit =', totalDebit, 'Credit =', totalCredit, 'Difference =', difference);
}

function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(amount);
}

function validateAccountSelection(field) {
    var row = $(field).closest('.line-item-row');
    var accountField = $(field);
    
    // Clear previous validation
    accountField.removeClass('is-invalid is-valid');
    
    if (accountField.val()) {
        accountField.addClass('is-valid');
        return true;
    } else {
        accountField.addClass('is-invalid');
        return false;
    }
}

function validateForm() {
    console.log('Validating form...');
    
    var isValid = true;
    var hasData = false;
    
    // Check each row
    $('.line-item-row').each(function() {
        var accountField = $(this).find('.account-select');
        var debitField = $(this).find('.debit-amount');
        var creditField = $(this).find('.credit-amount');
        
        var accountValue = accountField.val();
        var debitValue = parseFloat(debitField.val()) || 0;
        var creditValue = parseFloat(creditField.val()) || 0;
        
        // Check if row has data
        if (accountValue || debitValue > 0 || creditValue > 0) {
            hasData = true;
            
            // Validate account
            if (!accountValue) {
                accountField.addClass('is-invalid');
                isValid = false;
            }
            
            // Validate amounts
            if (!validateLineAmount(debitField[0])) {
                isValid = false;
            }
        }
    });
    
    // Check if at least 2 rows have data
    if (!hasData) {
        showAlert('At least one line item must be filled', 'warning');
        isValid = false;
    }
    
    // Check balance
    var totalDebit = parseFloat($('#total-debit').text().replace(/[^\d.-]/g, '')) || 0;
    var totalCredit = parseFloat($('#total-credit').text().replace(/[^\d.-]/g, '')) || 0;
    
    if (Math.abs(totalDebit - totalCredit) >= 0.01) {
        showAlert('Total debit must equal total credit', 'warning');
        isValid = false;
    }
    
    console.log('Form validation result:', isValid);
    return isValid;
}

function setupFormValidation() {
    // Real-time validation
    $(document).on('blur', '.account-select', function() {
        validateAccountSelection(this);
    });
    
    $(document).on('blur', '.debit-amount, .credit-amount', function() {
        validateLineAmount(this);
    });
}

function setupKeyboardNavigation() {
    // Tab navigation for speed entry
    $(document).on('keydown', '.line-item-row input, .line-item-row select', function(e) {
        if (e.key === 'Tab' && !e.shiftKey) {
            var currentRow = $(this).closest('.line-item-row');
            var nextRow = currentRow.next('.line-item-row');
            
            if (nextRow.length === 0) {
                // Add new row if we're at the last row
                addNewRow();
                setTimeout(function() {
                    $('.line-item-row:last .account-select').select2('open');
                }, 100);
                e.preventDefault();
            }
        }
    });
}

function setupTabNavigation() {
    // Enhanced tab navigation
    var tabOrder = [
        '.account-select',
        'input[name*="description"]',
        'input[name*="debit"]',
        'input[name*="credit"]'
    ];
    
    $(document).on('keydown', '.line-item-row input, .line-item-row select', function(e) {
        if (e.key === 'Tab') {
            var currentField = $(this);
            var currentRow = currentField.closest('.line-item-row');
            var currentIndex = tabOrder.indexOf(currentField.attr('class') || currentField.attr('name'));
            
            if (e.shiftKey) {
                // Shift+Tab - go to previous field
                if (currentIndex > 0) {
                    currentRow.find(tabOrder[currentIndex - 1]).focus();
                } else {
                    var prevRow = currentRow.prev('.line-item-row');
                    if (prevRow.length > 0) {
                        prevRow.find(tabOrder[tabOrder.length - 1]).focus();
                    }
                }
            } else {
                // Tab - go to next field
                if (currentIndex < tabOrder.length - 1) {
                    currentRow.find(tabOrder[currentIndex + 1]).focus();
                } else {
                    var nextRow = currentRow.next('.line-item-row');
                    if (nextRow.length > 0) {
                        nextRow.find(tabOrder[0]).focus();
                    } else {
                        // Add new row and focus on first field
                        addNewRow();
                        setTimeout(function() {
                            $('.line-item-row:last').find(tabOrder[0]).focus();
                        }, 100);
                    }
                }
            }
            e.preventDefault();
        }
    });
}

function showValidationErrors() {
    // Scroll to first error
    var firstError = $('.is-invalid').first();
    if (firstError.length > 0) {
        $('html, body').animate({
            scrollTop: firstError.offset().top - 100
        }, 500);
    }
}

function showAlert(message, type) {
    // Create alert element
    var alertHtml = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    // Insert at the top of the form
    $('#journal-entry-form').prepend(alertHtml);
    
    // Auto-dismiss after 5 seconds
    setTimeout(function() {
        $('.alert').fadeOut();
    }, 5000);
}

// Global functions for template use
window.validateLineAmount = validateLineAmount;
window.calculateTotals = calculateTotals;
window.addNewRow = addNewRow;
window.removeRow = removeRow;