/**
 * Partner Ledger Report JavaScript
 * Handles interactive features, sorting, filtering, and export functionality
 */

// Global variables
let sortDirection = {};
let currentSort = null;

/**
 * Initialize Partner Ledger functionality
 */
function initializePartnerLedger() {
    initializeSelect2();
    initializeDatePickers();
    initializeTableInteractions();
    initializeSorting();
    initializeFormValidation();
    
    // Show loading on form submit
    $('#filterForm').on('submit', function() {
        showLoading();
    });
}

/**
 * Initialize Select2 for customer dropdown
 */
function initializeSelect2() {
    $('#id_customer').select2({
        placeholder: 'All Customers',
        allowClear: true,
        width: '100%'
    });
}

/**
 * Format customer result in dropdown
 */
function formatCustomerResult(customer) {
    if (customer.loading) {
        return customer.text;
    }
    
    return $('<span>' + customer.text + '</span>');
}

/**
 * Format customer selection
 */
function formatCustomerSelection(customer) {
    return customer.text || customer.id;
}

/**
 * Initialize date pickers
 */
function initializeDatePickers() {
    // Set default date format
    const dateFormat = 'YYYY-MM-DD';
    
    // Initialize date inputs with date picker
    $('#id_date_from, #id_date_to').on('focus', function() {
        $(this).attr('type', 'date');
    });
    
    // Validate date range
    $('#id_date_from, #id_date_to').on('change', function() {
        validateDateRange();
    });
}

/**
 * Validate date range
 */
function validateDateRange() {
    const dateFrom = $('#id_date_from').val();
    const dateTo = $('#id_date_to').val();
    
    if (dateFrom && dateTo && dateFrom > dateTo) {
        showAlert('Date From cannot be greater than Date To', 'warning');
        $('#id_date_to').val('');
    }
}

/**
 * Initialize table interactions
 */
function initializeTableInteractions() {
    // Customer row toggle
    $(document).on('click', '.toggle-customer', function(e) {
        e.preventDefault();
        const customerId = $(this).data('customer-id');
        toggleCustomerRows(customerId, $(this));
    });
    
    // Payment row toggle
    $(document).on('click', '.toggle-payments', function(e) {
        e.preventDefault();
        const invoiceId = $(this).data('invoice-id');
        togglePaymentRows(invoiceId, $(this));
    });
    
    // Row hover effects
    $(document).on('mouseenter', '.customer-header-row', function() {
        $(this).addClass('table-active');
    }).on('mouseleave', '.customer-header-row', function() {
        $(this).removeClass('table-active');
    });
}

/**
 * Toggle customer rows visibility
 */
function toggleCustomerRows(customerId, button) {
    const rows = $(`.customer-${customerId}-rows`);
    const icon = button.find('i');
    
    if (rows.is(':visible')) {
        // Collapse
        rows.slideUp(300);
        icon.removeClass('bi-chevron-down').addClass('bi-chevron-right');
        button.removeClass('expanded');
        
        // Also collapse any expanded payment rows
        rows.filter('.payment-row').hide();
        $('.toggle-payments').removeClass('expanded')
            .find('i').removeClass('bi-chevron-down').addClass('bi-chevron-right');
    } else {
        // Expand
        rows.slideDown(300, function() {
            $(this).addClass('slide-down');
        });
        icon.removeClass('bi-chevron-right').addClass('bi-chevron-down');
        button.addClass('expanded');
    }
}

/**
 * Toggle payment rows visibility
 */
function togglePaymentRows(invoiceId, button) {
    const rows = $(`.invoice-${invoiceId}-payments`);
    const icon = button.find('i');
    
    if (rows.is(':visible')) {
        // Collapse
        rows.slideUp(200);
        icon.removeClass('bi-chevron-down').addClass('bi-chevron-right');
        button.removeClass('expanded');
    } else {
        // Expand
        rows.slideDown(200, function() {
            $(this).addClass('slide-down');
        });
        icon.removeClass('bi-chevron-right').addClass('bi-chevron-down');
        button.addClass('expanded');
    }
}

/**
 * Expand all customer rows
 */
function expandAllRows() {
    $('.toggle-customer').each(function() {
        const customerId = $(this).data('customer-id');
        const rows = $(`.customer-${customerId}-rows`);
        
        if (!rows.is(':visible')) {
            toggleCustomerRows(customerId, $(this));
        }
    });
}

/**
 * Collapse all customer rows
 */
function collapseAllRows() {
    $('.toggle-customer').each(function() {
        const customerId = $(this).data('customer-id');
        const rows = $(`.customer-${customerId}-rows`);
        
        if (rows.is(':visible')) {
            toggleCustomerRows(customerId, $(this));
        }
    });
}

/**
 * Initialize table sorting
 */
function initializeSorting() {
    $('.sortable').on('click', function() {
        const column = $(this).data('sort');
        sortTable(column, $(this));
    });
}

/**
 * Sort table by column
 */
function sortTable(column, headerElement) {
    // Reset other headers
    $('.sortable').not(headerElement).removeClass('asc desc');
    
    // Determine sort direction
    let direction = 'asc';
    if (headerElement.hasClass('asc')) {
        direction = 'desc';
        headerElement.removeClass('asc').addClass('desc');
    } else {
        direction = 'asc';
        headerElement.removeClass('desc').addClass('asc');
    }
    
    // Get all customer groups
    const customerGroups = [];
    $('.customer-header-row').each(function() {
        const customerId = $(this).data('customer-id');
        const customerRows = [$(this)];
        
        // Collect all rows for this customer
        $(`.customer-${customerId}-rows`).each(function() {
            customerRows.push($(this));
        });
        
        customerGroups.push({
            customerId: customerId,
            rows: customerRows,
            sortValue: getSortValue($(this), column)
        });
    });
    
    // Sort customer groups
    customerGroups.sort(function(a, b) {
        if (direction === 'asc') {
            return a.sortValue.localeCompare(b.sortValue, undefined, {numeric: true});
        } else {
            return b.sortValue.localeCompare(a.sortValue, undefined, {numeric: true});
        }
    });
    
    // Reorder rows in table
    const tbody = $('#partnerLedgerTable tbody');
    tbody.empty();
    
    customerGroups.forEach(function(group) {
        group.rows.forEach(function(row) {
            tbody.append(row);
        });
    });
    
    // Add animation
    tbody.find('tr').addClass('slide-down');
    setTimeout(function() {
        tbody.find('tr').removeClass('slide-down');
    }, 300);
}

/**
 * Get sort value for a row based on column
 */
function getSortValue(row, column) {
    switch (column) {
        case 'customer':
            return row.find('td:eq(1)').text().trim();
        case 'date':
            return row.find('td:eq(2)').text().trim();
        case 'invoice':
            return parseFloat(row.find('td:eq(5)').text().replace(/[^0-9.-]/g, '')) || 0;
        case 'payment':
            return parseFloat(row.find('td:eq(6)').text().replace(/[^0-9.-]/g, '')) || 0;
        case 'balance':
            return parseFloat(row.find('td:eq(7)').text().replace(/[^0-9.-]/g, '')) || 0;
        default:
            return row.find('td:eq(1)').text().trim();
    }
}

/**
 * Initialize form validation
 */
function initializeFormValidation() {
    $('#filterForm').on('submit', function(e) {
        const dateFrom = $('#id_date_from').val();
        const dateTo = $('#id_date_to').val();
        
        // Only validate if both dates are provided
        if (dateFrom && dateTo) {
            if (dateFrom > dateTo) {
                e.preventDefault();
                showAlert('Date From cannot be greater than Date To', 'warning');
                return false;
            }
        }
        
        // If no dates are provided, let the server handle defaults
        return true;
    });
}

/**
 * Show loading modal
 */
function showLoading() {
    $('#loadingModal').modal('show');
}

/**
 * Hide loading modal
 */
function hideLoading() {
    $('#loadingModal').modal('hide');
}

/**
 * Show alert message
 */
function showAlert(message, type = 'info') {
    const alertClass = `alert-${type}`;
    const alertHtml = `
        <div class="alert ${alertClass} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    // Remove existing alerts
    $('.alert').remove();
    
    // Add new alert at the top of the container
    $('.container-fluid').prepend(alertHtml);
    
    // Auto-dismiss after 5 seconds
    setTimeout(function() {
        $('.alert').fadeOut();
    }, 5000);
}

/**
 * Format currency for display
 */
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 2
    }).format(amount);
}

/**
 * Format number with commas
 */
function formatNumber(number) {
    return new Intl.NumberFormat('en-US').format(number);
}

/**
 * Debounce function for search
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Export functionality
 */
function exportData(format) {
    const form = $('#filterForm');
    const formData = form.serialize();
    
    if (!formData.includes('date_from') || !formData.includes('date_to')) {
        showAlert('Please generate a report first before exporting', 'warning');
        return;
    }
    
    showLoading();
    
    let exportUrl;
    if (format === 'excel') {
        exportUrl = '/reports/partner-ledger/export/excel/';
    } else if (format === 'pdf') {
        exportUrl = '/reports/partner-ledger/export/pdf/';
    }
    
    // Create a temporary form for export
    const exportForm = $('<form>', {
        method: 'GET',
        action: exportUrl
    });
    
    // Add form data as hidden inputs
    const params = new URLSearchParams(formData);
    for (const [key, value] of params) {
        exportForm.append($('<input>', {
            type: 'hidden',
            name: key,
            value: value
        }));
    }
    
    // Submit form
    $('body').append(exportForm);
    exportForm.submit();
    exportForm.remove();
    
    // Hide loading after a delay
    setTimeout(hideLoading, 2000);
}

/**
 * Print functionality
 */
function printReport() {
    // Expand all rows for printing
    expandAllRows();
    
    setTimeout(function() {
        window.print();
    }, 500);
}

/**
 * Search within table
 */
function searchTable(searchTerm) {
    const term = searchTerm.toLowerCase();
    
    $('.customer-header-row').each(function() {
        const row = $(this);
        const customerId = row.data('customer-id');
        const customerRows = $(`.customer-${customerId}-rows`);
        const customerText = row.text().toLowerCase();
        
        let hasMatch = customerText.includes(term);
        
        // Check invoice and payment rows
        if (!hasMatch) {
            customerRows.each(function() {
                if ($(this).text().toLowerCase().includes(term)) {
                    hasMatch = true;
                    return false; // break
                }
            });
        }
        
        if (hasMatch) {
            row.show();
            customerRows.show();
        } else {
            row.hide();
            customerRows.hide();
        }
    });
}

/**
 * Reset search
 */
function resetSearch() {
    $('.customer-header-row, .invoice-row, .payment-row').show();
    $('#searchInput').val('');
}

/**
 * Utility function to get URL parameters
 */
function getUrlParameter(name) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(name);
}

/**
 * Update URL with current filters
 */
function updateUrl(params) {
    const url = new URL(window.location);
    Object.keys(params).forEach(key => {
        if (params[key]) {
            url.searchParams.set(key, params[key]);
        } else {
            url.searchParams.delete(key);
        }
    });
    window.history.replaceState({}, '', url);
}

/**
 * Initialize keyboard shortcuts
 */
function initializeKeyboardShortcuts() {
    $(document).on('keydown', function(e) {
        // Ctrl+E for Excel export
        if (e.ctrlKey && e.key === 'e') {
            e.preventDefault();
            exportData('excel');
        }
        
        // Ctrl+P for PDF export
        if (e.ctrlKey && e.key === 'p') {
            e.preventDefault();
            exportData('pdf');
        }
        
        // Ctrl+F for search
        if (e.ctrlKey && e.key === 'f') {
            e.preventDefault();
            $('#searchInput').focus();
        }
    });
}

// Initialize when document is ready
$(document).ready(function() {
    initializePartnerLedger();
    initializeKeyboardShortcuts();
    
    // Hide loading on page load
    hideLoading();
});

// Export functions to global scope
window.expandAllRows = expandAllRows;
window.collapseAllRows = collapseAllRows;
window.exportData = exportData;
window.printReport = printReport;
window.searchTable = searchTable;
window.resetSearch = resetSearch;