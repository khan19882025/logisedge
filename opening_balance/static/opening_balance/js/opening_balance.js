$(document).ready(function() {
    // Initialize variables
    let totalDebit = 0;
    let totalCredit = 0;
    
    // Initialize Select2 for account dropdowns
    function initializeSelect2() {
        $('.account-select').select2({
            placeholder: 'Search for an account...',
            allowClear: true,
            ajax: {
                url: '/opening-balance/ajax/account-search/',
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
    
    // Initialize Select2 on page load
    initializeSelect2();
    
    // Calculate totals
    function calculateTotals() {
        totalDebit = 0;
        totalCredit = 0;
        
        $('.entry-row').each(function() {
            const amount = parseFloat($(this).find('.amount-input').val()) || 0;
            const balanceType = $(this).find('.balance-type-select').val();
            
            if (balanceType === 'debit') {
                totalDebit += amount;
            } else if (balanceType === 'credit') {
                totalCredit += amount;
            }
        });
        
        // Update display
        $('#total-debit').text(totalDebit.toFixed(2));
        $('#total-credit').text(totalCredit.toFixed(2));
        
        // Update balance status
        const difference = totalDebit - totalCredit;
        const balanceElement = $('#balance-difference');
        
        if (Math.abs(difference) < 0.01) {
            balanceElement.text('Balanced').removeClass('unbalanced').addClass('balanced');
            $('#opening-balance-form button[type="submit"]').prop('disabled', false);
        } else {
            balanceElement.text(`Unbalanced (${difference > 0 ? '+' : ''}${difference.toFixed(2)})`)
                          .removeClass('balanced').addClass('unbalanced');
            $('#opening-balance-form button[type="submit"]').prop('disabled', true);
        }
        
        // Highlight unbalanced rows
        highlightUnbalancedRows();
    }
    
    // Highlight rows with validation errors
    function highlightUnbalancedRows() {
        $('.entry-row').each(function() {
            const row = $(this);
            const account = row.find('.account-select').val();
            const amount = parseFloat(row.find('.amount-input').val()) || 0;
            const balanceType = row.find('.balance-type-select').val();
            
            let hasError = false;
            
            // Check for required fields
            if (!account) {
                row.addClass('error-row');
                hasError = true;
            }
            
            if (amount <= 0) {
                row.addClass('error-row');
                hasError = true;
            }
            
            if (!balanceType) {
                row.addClass('error-row');
                hasError = true;
            }
            
            // Remove error class if no errors
            if (!hasError) {
                row.removeClass('error-row');
            }
        });
    }
    
    // Add new entry row
    $('.add-entry-row').on('click', function() {
        const formset = $('#id_entries-TOTAL_FORMS');
        const currentForms = parseInt(formset.val());
        const newFormNum = currentForms;
        
        // Clone the first row
        const newRow = $('.entry-row').first().clone();
        
        // Update form indices
        newRow.find('input, select, textarea').each(function() {
            const name = $(this).attr('name');
            if (name) {
                $(this).attr('name', name.replace(/-\d+-/, `-${newFormNum}-`));
                $(this).attr('id', $(this).attr('id').replace(/-\d+-/, `-${newFormNum}-`));
            }
        });
        
        // Clear values
        newRow.find('input, select, textarea').val('');
        newRow.find('.select2').remove();
        
        // Add remove button
        newRow.find('.col-actions').html(`
            <button type="button" class="btn btn-sm btn-danger remove-entry-row">
                <i class="fas fa-trash"></i>
            </button>
        `);
        
        // Add to table
        $('.entry-rows').append(newRow);
        
        // Initialize Select2 for new row
        newRow.find('.account-select').select2({
            placeholder: 'Search for an account...',
            allowClear: true,
            ajax: {
                url: '/opening-balance/ajax/account-search/',
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
        
        // Update form count
        formset.val(newFormNum + 1);
        
        // Recalculate totals
        calculateTotals();
    });
    
    // Remove entry row
    $(document).on('click', '.remove-entry-row', function() {
        const row = $(this).closest('.entry-row');
        const formset = $('#id_entries-TOTAL_FORMS');
        const currentForms = parseInt(formset.val());
        
        // Don't remove if only one row left
        if ($('.entry-row').length <= 1) {
            alert('At least one entry is required.');
            return;
        }
        
        // Remove the row
        row.remove();
        
        // Update form count
        formset.val(currentForms - 1);
        
        // Recalculate totals
        calculateTotals();
    });
    
    // Handle amount input changes
    $(document).on('input', '.amount-input', function() {
        const value = parseFloat($(this).val()) || 0;
        $(this).val(value.toFixed(2));
        calculateTotals();
    });
    
    // Handle balance type changes
    $(document).on('change', '.balance-type-select', function() {
        calculateTotals();
    });
    
    // Handle account selection changes
    $(document).on('change', '.account-select', function() {
        calculateTotals();
    });
    
    // Form submission validation
    $('#opening-balance-form').on('submit', function(e) {
        const totalDebit = parseFloat($('#total-debit').text()) || 0;
        const totalCredit = parseFloat($('#total-credit').text()) || 0;
        
        if (Math.abs(totalDebit - totalCredit) > 0.01) {
            e.preventDefault();
            alert('Opening balance must be balanced. Total Debit and Total Credit must be equal.');
            return false;
        }
        
        // Check for empty required fields
        let hasErrors = false;
        $('.entry-row').each(function() {
            const account = $(this).find('.account-select').val();
            const amount = parseFloat($(this).find('.amount-input').val()) || 0;
            const balanceType = $(this).find('.balance-type-select').val();
            
            if (!account || amount <= 0 || !balanceType) {
                hasErrors = true;
                return false; // break loop
            }
        });
        
        if (hasErrors) {
            e.preventDefault();
            alert('Please fill in all required fields for each entry.');
            return false;
        }
        
        // Show loading state
        $(this).addClass('loading');
        $(this).find('button[type="submit"]').prop('disabled', true).html('<i class="fas fa-spinner fa-spin"></i> Saving...');
    });
    
    // Financial year change handler
    $('#financial_year_select').on('change', function() {
        const selectedYear = $(this).val();
        if (selectedYear) {
            // Check if opening balance already exists for this year
            $.get(`/opening-balance/check-year/${selectedYear}/`, function(data) {
                if (data.exists) {
                    if (confirm('An opening balance already exists for this financial year. Do you want to edit it instead?')) {
                        window.location.href = data.edit_url;
                    } else {
                        $('#financial_year_select').val('').trigger('change');
                    }
                }
            });
        }
    });
    
    // Auto-format amount inputs
    $(document).on('blur', '.amount-input', function() {
        const value = parseFloat($(this).val()) || 0;
        $(this).val(value.toFixed(2));
    });
    
    // Initialize totals on page load
    calculateTotals();
    
    // Set up existing account values for edit mode
    var existingEntries = $('#opening-balance-form').data('existing-entries');
    if (existingEntries) {
        existingEntries.forEach(function(entry) {
            $(`#id_entries-${entry.index}-account`).val(entry.accountId).trigger('change');
        });
    }
    
    // Tooltip initialization
    $('[data-toggle="tooltip"]').tooltip();
    
    // Auto-save draft functionality
    let autoSaveTimer;
    $(document).on('input change', '#opening-balance-form input, #opening-balance-form select, #opening-balance-form textarea', function() {
        clearTimeout(autoSaveTimer);
        autoSaveTimer = setTimeout(function() {
            // Auto-save draft logic can be implemented here
            console.log('Auto-saving draft...');
        }, 3000); // Save after 3 seconds of inactivity
    });
    
    // Keyboard shortcuts
    $(document).on('keydown', function(e) {
        // Ctrl/Cmd + Enter to submit form
        if ((e.ctrlKey || e.metaKey) && e.keyCode === 13) {
            e.preventDefault();
            $('#opening-balance-form').submit();
        }
        
        // Ctrl/Cmd + N to add new row
        if ((e.ctrlKey || e.metaKey) && e.keyCode === 78) {
            e.preventDefault();
            $('.add-entry-row').click();
        }
    });
    
    // Responsive table handling
    function handleResponsiveTable() {
        if ($(window).width() < 768) {
            $('.entry-details-table').addClass('table-responsive');
        } else {
            $('.entry-details-table').removeClass('table-responsive');
        }
    }
    
    $(window).on('resize', handleResponsiveTable);
    handleResponsiveTable();
}); 