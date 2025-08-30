/**
 * Adjustment Entry System JavaScript
 * Handles form validation, dynamic form rows, and AJAX functionality
 */

class AdjustmentEntryManager {
    constructor() {
        this.init();
    }

    init() {
        this.bindEvents();
        this.initializeFormValidation();
        this.initializeAccountSearch();
        this.initializeBalanceCalculation();
    }

    bindEvents() {
        // Form submission
        $(document).on('submit', '#adjustment-entry-form', this.handleFormSubmit.bind(this));
        
        // Dynamic form rows
        $(document).on('click', '.add-entry-row', this.addEntryRow.bind(this));
        $(document).on('click', '.remove-entry-row', this.removeEntryRow.bind(this));
        
        // Amount input changes
        $(document).on('input', '.debit-amount, .credit-amount', this.handleAmountChange.bind(this));
        
        // Account selection
        $(document).on('change', '.account-select', this.handleAccountChange.bind(this));
        
        // Action buttons
        $(document).on('click', '.btn-post', this.handlePostAction.bind(this));
        $(document).on('click', '.btn-cancel', this.handleCancelAction.bind(this));
        $(document).on('click', '.btn-delete', this.handleDeleteAction.bind(this));
        
        // Search and filter
        $(document).on('submit', '#search-form', this.handleSearch.bind(this));
        $(document).on('change', '#id_status, #id_adjustment_type', this.handleFilterChange.bind(this));
        
        // Print functionality
        $(document).on('click', '.btn-print', this.handlePrint.bind(this));
    }

    initializeFormValidation() {
        // Real-time validation
        $('.debit-amount, .credit-amount').on('input', function() {
            this.validateAmountField($(this));
        }.bind(this));

        // Form validation before submit
        $('#adjustment-entry-form').on('submit', function(e) {
            if (!this.validateForm()) {
                e.preventDefault();
                this.showError('Please correct the errors before submitting.');
            }
        }.bind(this));
    }

    initializeAccountSearch() {
        // Initialize select2 for account search
        $('.account-select').select2({
            placeholder: 'Search for an account...',
            allowClear: true,
            ajax: {
                url: '/accounting/adjustment-entry/ajax/account-search/',
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
            templateResult: this.formatAccountOption,
            templateSelection: this.formatAccountSelection
        });
    }

    initializeBalanceCalculation() {
        // Calculate initial balance
        this.calculateBalance();
        
        // Set up periodic balance calculation
        setInterval(() => {
            this.calculateBalance();
        }, 1000);
    }

    formatAccountOption(account) {
        if (account.loading) return account.text;
        if (!account.id) return account.text;
        
        return $(`
            <div class="account-option">
                <strong>${account.account_code}</strong> - ${account.account_name}
            </div>
        `);
    }

    formatAccountSelection(account) {
        if (!account.id) return account.text;
        return `${account.account_code} - ${account.account_name}`;
    }

    handleFormSubmit(e) {
        const form = $(e.target);
        const submitBtn = form.find('button[type="submit"]');
        
        // Show loading state
        submitBtn.prop('disabled', true);
        submitBtn.html('<span class="loading-spinner"></span> Saving...');
        
        // Validate form
        if (!this.validateForm()) {
            e.preventDefault();
            submitBtn.prop('disabled', false);
            submitBtn.html(submitBtn.data('original-text') || 'Save');
            this.showError('Please correct the errors before submitting.');
            return false;
        }
    }

    validateForm() {
        let isValid = true;
        
        // Clear previous errors
        $('.is-invalid').removeClass('is-invalid');
        $('.invalid-feedback').remove();
        
        // Validate required fields
        $('#adjustment-entry-form .form-control[required]').each(function() {
            if (!$(this).val().trim()) {
                $(this).addClass('is-invalid');
                $(this).after('<div class="invalid-feedback">This field is required.</div>');
                isValid = false;
            }
        });
        
        // Validate date
        const dateField = $('#id_date');
        if (dateField.val()) {
            const selectedDate = new Date(dateField.val());
            const today = new Date();
            if (selectedDate > today) {
                dateField.addClass('is-invalid');
                dateField.after('<div class="invalid-feedback">Date cannot be in the future.</div>');
                isValid = false;
            }
        }
        
        // Validate entries
        if (!this.validateEntries()) {
            isValid = false;
        }
        
        return isValid;
    }

    validateEntries() {
        let isValid = true;
        let totalDebit = 0;
        let totalCredit = 0;
        let validEntries = 0;
        let hasDebit = false;
        let hasCredit = false;
        
        $('.entry-row').each(function() {
            const row = $(this);
            const debit = parseFloat(row.find('.debit-amount').val()) || 0;
            const credit = parseFloat(row.find('.credit-amount').val()) || 0;
            const account = row.find('.account-select').val();
            
            // Clear previous errors
            row.find('.is-invalid').removeClass('is-invalid');
            row.find('.invalid-feedback').remove();
            
            // Validate account selection
            if (!account) {
                row.find('.account-select').addClass('is-invalid');
                row.find('.account-select').after('<div class="invalid-feedback">Account is required.</div>');
                isValid = false;
            }
            
            // Validate amount
            if (debit === 0 && credit === 0) {
                row.find('.debit-amount, .credit-amount').addClass('is-invalid');
                row.find('.debit-amount').after('<div class="invalid-feedback">Either debit or credit amount is required.</div>');
                isValid = false;
            } else if (debit > 0 && credit > 0) {
                row.find('.debit-amount, .credit-amount').addClass('is-invalid');
                row.find('.debit-amount').after('<div class="invalid-feedback">Cannot have both debit and credit amounts.</div>');
                isValid = false;
            } else {
                totalDebit += debit;
                totalCredit += credit;
                validEntries++;
                if (debit > 0) hasDebit = true;
                if (credit > 0) hasCredit = true;
            }
        });
        
        // Validate minimum entries
        if (validEntries < 2) {
            this.showError('At least two entries are required (one debit, one credit).');
            isValid = false;
        }
        
        // Validate debit and credit presence
        if (!hasDebit) {
            this.showError('At least one debit entry is required.');
            isValid = false;
        }
        
        if (!hasCredit) {
            this.showError('At least one credit entry is required.');
            isValid = false;
        }
        
        // Validate balance
        if (Math.abs(totalDebit - totalCredit) > 0.01) {
            this.showError(`Total debit (${totalDebit.toFixed(2)}) must equal total credit (${totalCredit.toFixed(2)}).`);
            isValid = false;
        }
        
        return isValid;
    }

    validateAmountField(field) {
        const value = parseFloat(field.val());
        const row = field.closest('.entry-row');
        const otherField = field.hasClass('debit-amount') ? 
            row.find('.credit-amount') : row.find('.debit-amount');
        
        // Clear previous errors
        field.removeClass('is-invalid');
        otherField.removeClass('is-invalid');
        row.find('.invalid-feedback').remove();
        
        // Validate amount
        if (value < 0) {
            field.addClass('is-invalid');
            field.after('<div class="invalid-feedback">Amount must be positive.</div>');
            return false;
        }
        
        // Check for both debit and credit
        const otherValue = parseFloat(otherField.val()) || 0;
        if (value > 0 && otherValue > 0) {
            field.addClass('is-invalid');
            otherField.addClass('is-invalid');
            field.after('<div class="invalid-feedback">Cannot have both debit and credit amounts.</div>');
            return false;
        }
        
        return true;
    }

    addEntryRow() {
        const formset = $('#id_entries-TOTAL_FORMS');
        const currentCount = parseInt(formset.val());
        const newCount = currentCount + 1;
        
        // Update form count
        formset.val(newCount);
        
        // Clone the first row and update indices
        const firstRow = $('.entry-row').first();
        const newRow = firstRow.clone();
        
        // Clear values
        newRow.find('input, select').val('');
        newRow.find('.select2-container').remove();
        
        // Update form indices
        newRow.find('input, select').each(function() {
            const name = $(this).attr('name');
            if (name) {
                $(this).attr('name', name.replace(/-\d+-/, `-${newCount - 1}-`));
            }
            
            const id = $(this).attr('id');
            if (id) {
                $(this).attr('id', id.replace(/-\d+-/, `-${newCount - 1}-`));
            }
        });
        
        // Add remove button if not present
        if (!newRow.find('.remove-entry-row').length) {
            newRow.find('.col-actions').html(`
                <button type="button" class="btn btn-sm btn-danger remove-entry-row">
                    <i class="fas fa-trash"></i>
                </button>
            `);
        }
        
        // Add to form
        $('.entry-rows').append(newRow);
        
        // Reinitialize select2
        this.initializeAccountSearch();
        
        // Update balance
        this.calculateBalance();
    }

    removeEntryRow() {
        const row = $(this).closest('.entry-row');
        const totalRows = $('.entry-row').length;
        
        if (totalRows > 2) {
            row.remove();
            this.updateFormIndices();
            this.calculateBalance();
        } else {
            this.showError('At least two entries are required.');
        }
    }

    updateFormIndices() {
        $('.entry-row').each(function(index) {
            $(this).find('input, select').each(function() {
                const name = $(this).attr('name');
                if (name) {
                    $(this).attr('name', name.replace(/-\d+-/, `-${index}-`));
                }
                
                const id = $(this).attr('id');
                if (id) {
                    $(this).attr('id', id.replace(/-\d+-/, `-${index}-`));
                }
            });
        });
        
        // Update total forms count
        $('#id_entries-TOTAL_FORMS').val($('.entry-row').length);
    }

    handleAmountChange() {
        this.calculateBalance();
        this.validateAmountField($(this));
    }

    handleAccountChange() {
        // Additional account validation if needed
        this.calculateBalance();
    }

    calculateBalance() {
        let totalDebit = 0;
        let totalCredit = 0;
        
        $('.entry-row').each(function() {
            const debit = parseFloat($(this).find('.debit-amount').val()) || 0;
            const credit = parseFloat($(this).find('.credit-amount').val()) || 0;
            
            totalDebit += debit;
            totalCredit += credit;
        });
        
        // Update display
        $('#total-debit').text(totalDebit.toFixed(2));
        $('#total-credit').text(totalCredit.toFixed(2));
        
        const difference = Math.abs(totalDebit - totalCredit);
        const balanceElement = $('#balance-difference');
        
        if (difference < 0.01) {
            balanceElement.text('Balanced').removeClass('text-danger').addClass('text-success');
        } else {
            balanceElement.text(`Difference: ${difference.toFixed(2)}`).removeClass('text-success').addClass('text-danger');
        }
    }

    handlePostAction(e) {
        e.preventDefault();
        
        if (confirm('Are you sure you want to post this adjustment entry? This action cannot be undone.')) {
            const url = $(this).data('url');
            this.performAction(url, 'posting');
        }
    }

    handleCancelAction(e) {
        e.preventDefault();
        
        if (confirm('Are you sure you want to cancel this adjustment entry? This action cannot be undone.')) {
            const url = $(this).data('url');
            this.performAction(url, 'cancelling');
        }
    }

    handleDeleteAction(e) {
        e.preventDefault();
        
        if (confirm('Are you sure you want to delete this adjustment entry? This action cannot be undone.')) {
            const url = $(this).data('url');
            this.performAction(url, 'deleting');
        }
    }

    performAction(url, action) {
        const button = $(`[data-url="${url}"]`);
        const originalText = button.text();
        
        // Show loading state
        button.prop('disabled', true);
        button.html(`<span class="loading-spinner"></span> ${action}...`);
        
        $.post(url)
            .done(function(response) {
                // Reload page to show updated status
                window.location.reload();
            })
            .fail(function(xhr) {
                button.prop('disabled', false);
                button.text(originalText);
                
                let errorMessage = 'An error occurred while ' + action + ' the entry.';
                if (xhr.responseJSON && xhr.responseJSON.error) {
                    errorMessage = xhr.responseJSON.error;
                }
                
                this.showError(errorMessage);
            }.bind(this));
    }

    handleSearch(e) {
        // Add loading indicator
        const form = $(e.target);
        const submitBtn = form.find('button[type="submit"]');
        const originalText = submitBtn.text();
        
        submitBtn.prop('disabled', true);
        submitBtn.html('<span class="loading-spinner"></span> Searching...');
        
        // Form will submit normally, reset button on page load
        setTimeout(() => {
            submitBtn.prop('disabled', false);
            submitBtn.text(originalText);
        }, 2000);
    }

    handleFilterChange() {
        // Auto-submit form when filters change
        $('#search-form').submit();
    }

    handlePrint() {
        const url = $(this).data('url');
        window.open(url, '_blank');
    }

    showError(message) {
        // Remove existing alerts
        $('.alert').remove();
        
        // Add new error alert
        const alert = $(`
            <div class="alert alert-danger alert-dismissible fade show" role="alert">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `);
        
        $('.adjustment-entry-content').prepend(alert);
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            alert.alert('close');
        }, 5000);
    }

    showSuccess(message) {
        // Remove existing alerts
        $('.alert').remove();
        
        // Add new success alert
        const alert = $(`
            <div class="alert alert-success alert-dismissible fade show" role="alert">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `);
        
        $('.adjustment-entry-content').prepend(alert);
        
        // Auto-dismiss after 3 seconds
        setTimeout(() => {
            alert.alert('close');
        }, 3000);
    }
}

// Initialize when document is ready
$(document).ready(function() {
    new AdjustmentEntryManager();
});

// Export for use in other scripts
window.AdjustmentEntryManager = AdjustmentEntryManager; 