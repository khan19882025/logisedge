/**
 * Chart of Accounts JavaScript functionality
 */

$(document).ready(function() {
    // Initialize tooltips
    $('[data-toggle="tooltip"]').tooltip();
    
    // Initialize popovers
    $('[data-toggle="popover"]').popover();
    
    // Account code generation functionality
    initializeAccountCodeGeneration();
    
    // Parent account autocomplete
    initializeParentAccountAutocomplete();
    
    // Account status toggle
    initializeAccountStatusToggle();
    
    // Search functionality
    initializeSearchFunctionality();
    
    // Export functionality
    initializeExportFunctionality();
});

/**
 * Initialize account code generation
 */
function initializeAccountCodeGeneration() {
    const accountTypeSelect = $('#account_type');
    const accountCodeInput = $('#account_code');
    const autoGenerateCheckbox = $('#auto_generate_code');
    const accountNatureSelect = $('#account_nature');
    
    if (accountTypeSelect.length && accountCodeInput.length && autoGenerateCheckbox.length) {
        // Function to generate account code
        function generateAccountCode() {
            const accountTypeId = accountTypeSelect.val();
            const isAutoGenerate = autoGenerateCheckbox.is(':checked');
            
            if (accountTypeId && isAutoGenerate) {
                $.ajax({
                    url: '/chart-of-accounts/ajax/generate-account-code/',
                    method: 'POST',
                    data: {
                        account_type_id: accountTypeId,
                        csrfmiddlewaretoken: $('[name=csrfmiddlewaretoken]').val()
                    },
                    success: function(response) {
                        if (response.success) {
                            accountCodeInput.val(response.account_code);
                            showNotification('Account code generated successfully!', 'success');
                        } else {
                            showNotification('Error generating account code: ' + response.error, 'error');
                        }
                    },
                    error: function(xhr, status, error) {
                        showNotification('Error generating account code. Please try again.', 'error');
                        console.error('AJAX error:', error);
                    }
                });
            }
        }
        
        // Function to auto-set account nature based on account type
        function autoSetAccountNature() {
            const selectedOption = accountTypeSelect.find('option:selected');
            const category = selectedOption.data('category');
            
            // Only auto-set if account nature is empty or set to auto-determine
            if (accountNatureSelect.val() === '' && category) {
                let defaultNature = '';
                
                switch(category) {
                    case 'ASSET':
                    case 'EXPENSE':
                        defaultNature = 'DEBIT';
                        break;
                    case 'LIABILITY':
                    case 'EQUITY':
                    case 'REVENUE':
                        defaultNature = 'CREDIT';
                        break;
                    default:
                        defaultNature = 'BOTH';
                }
                
                accountNatureSelect.val(defaultNature);
                showNotification(`Account nature auto-set to ${defaultNature} based on account type.`, 'info');
            }
        }
        
        // Handle account type change
        accountTypeSelect.on('change', function() {
            if (autoGenerateCheckbox.is(':checked')) {
                generateAccountCode();
            }
            autoSetAccountNature();
        });
        
        // Handle auto-generate checkbox change
        autoGenerateCheckbox.on('change', function() {
            if (this.checked) {
                accountCodeInput.prop('readonly', true);
                if (accountTypeSelect.val()) {
                    generateAccountCode();
                }
            } else {
                accountCodeInput.prop('readonly', false);
            }
        });
        
        // Handle account nature change
        accountNatureSelect.on('change', function() {
            const selectedValue = $(this).val();
            if (selectedValue === 'BOTH') {
                showNotification('Both option selected - this account can have both debit and credit transactions.', 'info');
            }
        });
        
        // Initialize on page load
        if (autoGenerateCheckbox.is(':checked')) {
            accountCodeInput.prop('readonly', true);
            if (accountTypeSelect.val()) {
                generateAccountCode();
            }
        }
        
        // Auto-set account nature on page load if empty
        if (accountTypeSelect.val() && accountNatureSelect.val() === '') {
            autoSetAccountNature();
        }
    }
}

/**
 * Initialize parent account autocomplete
 */
function initializeParentAccountAutocomplete() {
    const parentAccountInput = $('#parent_account_code');
    
    if (parentAccountInput.length) {
        let autocompleteTimeout;
        
        parentAccountInput.on('input', function() {
            const searchTerm = $(this).val();
            
            // Clear previous timeout
            clearTimeout(autocompleteTimeout);
            
            if (searchTerm.length >= 2) {
                // Set timeout to avoid too many requests
                autocompleteTimeout = setTimeout(function() {
                    $.ajax({
                        url: '/chart-of-accounts/ajax/parent-accounts/',
                        method: 'GET',
                        data: { q: searchTerm },
                        success: function(response) {
                            showParentAccountSuggestions(response.results, parentAccountInput);
                        },
                        error: function(xhr, status, error) {
                            console.error('Error fetching parent accounts:', error);
                        }
                    });
                }, 300);
            } else {
                hideParentAccountSuggestions();
            }
        });
        
        // Hide suggestions when clicking outside
        $(document).on('click', function(e) {
            if (!$(e.target).closest('.parent-account-suggestions').length) {
                hideParentAccountSuggestions();
            }
        });
    }
}

/**
 * Show parent account suggestions
 */
function showParentAccountSuggestions(suggestions, inputElement) {
    hideParentAccountSuggestions();
    
    if (suggestions.length > 0) {
        const suggestionsHtml = suggestions.map(function(item) {
            return `<div class="suggestion-item" data-value="${item.id}">${item.text}</div>`;
        }).join('');
        
        const suggestionsDiv = $(`
            <div class="parent-account-suggestions">
                ${suggestionsHtml}
            </div>
        `);
        
        inputElement.after(suggestionsDiv);
        
        // Handle suggestion click
        suggestionsDiv.on('click', '.suggestion-item', function() {
            const value = $(this).data('value');
            inputElement.val(value);
            hideParentAccountSuggestions();
        });
    }
}

/**
 * Hide parent account suggestions
 */
function hideParentAccountSuggestions() {
    $('.parent-account-suggestions').remove();
}

/**
 * Initialize account status toggle
 */
function initializeAccountStatusToggle() {
    $('.account-status-toggle').on('change', function() {
        const accountId = $(this).data('account-id');
        const isActive = $(this).is(':checked');
        
        $.ajax({
            url: `/chart-of-accounts/ajax/update-status/${accountId}/`,
            method: 'POST',
            data: {
                is_active: isActive,
                csrfmiddlewaretoken: $('[name=csrfmiddlewaretoken]').val()
            },
            success: function(response) {
                if (response.success) {
                    showNotification('Account status updated successfully!', 'success');
                } else {
                    showNotification('Error updating account status.', 'error');
                }
            },
            error: function(xhr, status, error) {
                showNotification('Error updating account status. Please try again.', 'error');
                console.error('AJAX error:', error);
            }
        });
    });
}

/**
 * Initialize search functionality
 */
function initializeSearchFunctionality() {
    const searchForm = $('#accountSearchForm');
    
    if (searchForm.length) {
        // Auto-submit form when search criteria changes
        searchForm.find('select, input[type="text"]').on('change keyup', function() {
            if ($(this).attr('type') === 'text') {
                // For text inputs, add delay
                clearTimeout(searchForm.data('timeout'));
                searchForm.data('timeout', setTimeout(function() {
                    searchForm.submit();
                }, 500));
            } else {
                // For selects, submit immediately
                searchForm.submit();
            }
        });
        
        // Clear search
        $('.clear-search').on('click', function(e) {
            e.preventDefault();
            searchForm.find('input[type="text"]').val('');
            searchForm.find('select').val('');
            searchForm.submit();
        });
    }
}

/**
 * Initialize export functionality
 */
function initializeExportFunctionality() {
    $('.export-accounts').on('click', function(e) {
        e.preventDefault();
        
        const searchParams = new URLSearchParams(window.location.search);
        const exportUrl = '/chart-of-accounts/export-csv/?' + searchParams.toString();
        
        // Create temporary link and trigger download
        const link = document.createElement('a');
        link.href = exportUrl;
        link.download = 'chart_of_accounts.csv';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        showNotification('Export started. File will download shortly.', 'success');
    });
}

/**
 * Show notification
 */
function showNotification(message, type = 'info') {
    const alertClass = type === 'success' ? 'alert-success' : 
                      type === 'error' ? 'alert-danger' : 'alert-info';
    
    const notification = $(`
        <div class="alert ${alertClass} alert-dismissible fade show notification-toast" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `);
    
    // Remove existing notifications
    $('.notification-toast').remove();
    
    // Add to page
    $('body').append(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(function() {
        notification.fadeOut(function() {
            $(this).remove();
        });
    }, 5000);
}

/**
 * Format currency
 */
function formatCurrency(amount, currency = 'AED') {
    return new Intl.NumberFormat('en-AE', {
        style: 'currency',
        currency: currency
    }).format(amount);
}

/**
 * Format account code with proper spacing
 */
function formatAccountCode(code) {
    if (!code) return '';
    
    // Add spaces every 2 digits for better readability
    return code.replace(/(\d{2})(?=\d)/g, '$1 ');
}

/**
 * Calculate account level based on code
 */
function calculateAccountLevel(code) {
    if (!code) return 0;
    
    // Count the number of non-zero digits to determine level
    const digits = code.replace(/0+$/, ''); // Remove trailing zeros
    return Math.ceil(digits.length / 2);
}

/**
 * Validate account code format
 */
function validateAccountCode(code) {
    // Account code should be numeric and 4-10 digits
    const codeRegex = /^\d{4,10}$/;
    return codeRegex.test(code);
}

/**
 * Initialize account hierarchy tree
 */
function initializeAccountHierarchy() {
    $('.account-tree-toggle').on('click', function(e) {
        e.preventDefault();
        
        const accountId = $(this).data('account-id');
        const toggleIcon = $(this).find('i');
        const subAccounts = $(`.account-sub-accounts[data-parent="${accountId}"]`);
        
        if (subAccounts.is(':visible')) {
            subAccounts.slideUp();
            toggleIcon.removeClass('bi-chevron-down').addClass('bi-chevron-right');
        } else {
            subAccounts.slideDown();
            toggleIcon.removeClass('bi-chevron-right').addClass('bi-chevron-down');
        }
    });
}

/**
 * Initialize account balance charts
 */
function initializeAccountBalanceCharts() {
    const balanceChartCanvas = document.getElementById('balanceChart');
    
    if (balanceChartCanvas) {
        const ctx = balanceChartCanvas.getContext('2d');
        
        // Sample data - replace with actual data from backend
        const chartData = {
            labels: ['Assets', 'Liabilities', 'Equity', 'Revenue', 'Expenses'],
            datasets: [{
                label: 'Account Balances',
                data: [1200000, 800000, 400000, 500000, 300000],
                backgroundColor: [
                    'rgba(75, 192, 192, 0.6)',
                    'rgba(255, 99, 132, 0.6)',
                    'rgba(54, 162, 235, 0.6)',
                    'rgba(255, 205, 86, 0.6)',
                    'rgba(153, 102, 255, 0.6)'
                ],
                borderColor: [
                    'rgba(75, 192, 192, 1)',
                    'rgba(255, 99, 132, 1)',
                    'rgba(54, 162, 235, 1)',
                    'rgba(255, 205, 86, 1)',
                    'rgba(153, 102, 255, 1)'
                ],
                borderWidth: 1
            }]
        };
        
        new Chart(ctx, {
            type: 'doughnut',
            data: chartData,
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'bottom',
                    },
                    title: {
                        display: true,
                        text: 'Account Balances by Category'
                    }
                }
            }
        });
    }
}

// Initialize additional features when DOM is ready
$(document).ready(function() {
    initializeAccountHierarchy();
    initializeAccountBalanceCharts();
}); 