// Vendor Ledger Report JavaScript

$(document).ready(function() {
    // Initialize the vendor ledger report
    initializeVendorLedger();
});

function initializeVendorLedger() {
    // Initialize Select2 dropdowns
    initializeSelect2();
    
    // Initialize date pickers
    initializeDatePickers();
    
    // Initialize quick filters
    initializeQuickFilters();
    
    // Initialize form validation
    initializeFormValidation();
    
    // Initialize export functionality
    initializeExportFunctions();
    
    // Initialize table interactions
    initializeTableInteractions();
    
    // Add loading states
    initializeLoadingStates();
}

function initializeSelect2() {
    // Initialize Select2 for vendor dropdown
    $('#id_vendor').select2({
        theme: 'bootstrap-5',
        placeholder: 'Select Vendor (Leave blank for all vendors)',
        allowClear: true,
        width: '100%'
    });
    
    // Initialize Select2 for payment status
    $('#id_payment_status').select2({
        theme: 'bootstrap-5',
        minimumResultsForSearch: Infinity,
        width: '100%'
    });
}

function initializeDatePickers() {
    // Set default date range (current month)
    const today = new Date();
    const firstDay = new Date(today.getFullYear(), today.getMonth(), 1);
    const lastDay = new Date(today.getFullYear(), today.getMonth() + 1, 0);
    
    if (!$('#id_date_from').val()) {
        $('#id_date_from').val(formatDate(firstDay));
    }
    
    if (!$('#id_date_to').val()) {
        $('#id_date_to').val(formatDate(lastDay));
    }
    
    // Add date validation
    $('#id_date_from, #id_date_to').on('change', function() {
        validateDateRange();
    });
}

function initializeQuickFilters() {
    // Quick filter dropdown change handler
    $('#id_quick_filter').on('change', function() {
        const filterType = $(this).val();
        if (filterType) {
            setQuickFilter(filterType);
        }
    });
    
    // Add quick filter buttons
    addQuickFilterButtons();
}

function addQuickFilterButtons() {
    const quickFilters = [
        { label: 'Today', value: 'today' },
        { label: 'This Week', value: 'this_week' },
        { label: 'This Month', value: 'this_month' },
        { label: 'Last Month', value: 'last_month' }
    ];
    
    const buttonContainer = $('<div class="quick-filter-buttons mt-2"></div>');
    
    quickFilters.forEach(filter => {
        const button = $(`<button type="button" class="btn btn-outline-secondary btn-sm me-2 mb-1" data-filter="${filter.value}">${filter.label}</button>`);
        button.on('click', function() {
            setQuickFilter(filter.value);
            $('.quick-filter-buttons .btn').removeClass('active');
            $(this).addClass('active');
        });
        buttonContainer.append(button);
    });
    
    $('#id_quick_filter').closest('.col-md-2').after('<div class="col-12">' + buttonContainer.prop('outerHTML') + '</div>');
}

function setQuickFilter(filterType) {
    const today = new Date();
    let dateFrom, dateTo;
    
    switch (filterType) {
        case 'today':
            dateFrom = dateTo = today;
            break;
        case 'yesterday':
            dateFrom = dateTo = new Date(today.getTime() - 24 * 60 * 60 * 1000);
            break;
        case 'this_week':
            const startOfWeek = new Date(today);
            startOfWeek.setDate(today.getDate() - today.getDay());
            dateFrom = startOfWeek;
            dateTo = today;
            break;
        case 'last_week':
            const lastWeekStart = new Date(today);
            lastWeekStart.setDate(today.getDate() - today.getDay() - 7);
            const lastWeekEnd = new Date(lastWeekStart);
            lastWeekEnd.setDate(lastWeekStart.getDate() + 6);
            dateFrom = lastWeekStart;
            dateTo = lastWeekEnd;
            break;
        case 'this_month':
            dateFrom = new Date(today.getFullYear(), today.getMonth(), 1);
            dateTo = today;
            break;
        case 'last_month':
            const lastMonth = new Date(today.getFullYear(), today.getMonth() - 1, 1);
            const lastMonthEnd = new Date(today.getFullYear(), today.getMonth(), 0);
            dateFrom = lastMonth;
            dateTo = lastMonthEnd;
            break;
        case 'this_quarter':
            const quarterStart = new Date(today.getFullYear(), Math.floor(today.getMonth() / 3) * 3, 1);
            dateFrom = quarterStart;
            dateTo = today;
            break;
        case 'last_quarter':
            const lastQuarterStart = new Date(today.getFullYear(), Math.floor(today.getMonth() / 3) * 3 - 3, 1);
            const lastQuarterEnd = new Date(today.getFullYear(), Math.floor(today.getMonth() / 3) * 3, 0);
            dateFrom = lastQuarterStart;
            dateTo = lastQuarterEnd;
            break;
        case 'this_year':
            dateFrom = new Date(today.getFullYear(), 0, 1);
            dateTo = today;
            break;
        case 'last_year':
            dateFrom = new Date(today.getFullYear() - 1, 0, 1);
            dateTo = new Date(today.getFullYear() - 1, 11, 31);
            break;
        default:
            return;
    }
    
    $('#id_date_from').val(formatDate(dateFrom));
    $('#id_date_to').val(formatDate(dateTo));
    
    // Trigger change event to validate
    $('#id_date_from, #id_date_to').trigger('change');
}

function initializeFormValidation() {
    $('#vendorLedgerForm').on('submit', function(e) {
        if (!validateForm()) {
            e.preventDefault();
            return false;
        }
        
        // Show loading state
        showLoadingState();
    });
}

function validateForm() {
    let isValid = true;
    
    // Clear previous errors
    $('.is-invalid').removeClass('is-invalid');
    $('.invalid-feedback').remove();
    
    // Validate date range
    if (!validateDateRange()) {
        isValid = false;
    }
    
    // Validate required fields
    const dateFrom = $('#id_date_from').val();
    const dateTo = $('#id_date_to').val();
    
    if (!dateFrom) {
        showFieldError('#id_date_from', 'From date is required.');
        isValid = false;
    }
    
    if (!dateTo) {
        showFieldError('#id_date_to', 'To date is required.');
        isValid = false;
    }
    
    return isValid;
}

function validateDateRange() {
    const dateFrom = new Date($('#id_date_from').val());
    const dateTo = new Date($('#id_date_to').val());
    const today = new Date();
    
    // Clear previous date errors
    $('#id_date_from, #id_date_to').removeClass('is-invalid');
    $('.date-error').remove();
    
    if (dateFrom && dateTo) {
        if (dateFrom > dateTo) {
            showFieldError('#id_date_from', 'From date cannot be later than to date.');
            return false;
        }
        
        if (dateFrom > today) {
            showFieldError('#id_date_from', 'From date cannot be in the future.');
            return false;
        }
        
        // Check for reasonable date range (not more than 2 years)
        const daysDiff = (dateTo - dateFrom) / (1000 * 60 * 60 * 24);
        if (daysDiff > 730) {
            showFieldError('#id_date_to', 'Date range cannot exceed 2 years.');
            return false;
        }
    }
    
    return true;
}

function showFieldError(fieldSelector, message) {
    const field = $(fieldSelector);
    field.addClass('is-invalid');
    
    const errorDiv = $(`<div class="invalid-feedback date-error">${message}</div>`);
    field.after(errorDiv);
}

function initializeExportFunctions() {
    // Handle export form submissions
    $('form[action*="export"]').on('submit', function(e) {
        const form = $(this);
        const button = form.find('button[type="submit"]');
        
        // Disable button and show loading
        button.prop('disabled', true);
        const originalText = button.html();
        button.html('<i class="fas fa-spinner fa-spin me-1"></i>Exporting...');
        
        // Re-enable button after a delay
        setTimeout(() => {
            button.prop('disabled', false);
            button.html(originalText);
        }, 3000);
    });
}

function initializeTableInteractions() {
    // Add hover effects to transaction rows
    $(document).on('mouseenter', '.transaction-table tbody tr', function() {
        $(this).addClass('table-hover-effect');
    }).on('mouseleave', '.transaction-table tbody tr', function() {
        $(this).removeClass('table-hover-effect');
    });
    
    // Add click handler for transaction details
    $(document).on('click', '.transaction-table tbody tr', function() {
        const reference = $(this).find('td:nth-child(3)').text().trim();
        if (reference && reference !== '-') {
            // You can add logic here to show transaction details
            console.log('Transaction clicked:', reference);
        }
    });
}

function initializeLoadingStates() {
    // Add loading overlay to vendor sections
    $('.vendor-section').each(function() {
        $(this).addClass('fade-in');
    });
}

function showLoadingState() {
    // Show loading overlay
    const loadingOverlay = $(`
        <div class="loading-overlay">
            <div class="loading-spinner">
                <i class="fas fa-spinner fa-spin fa-3x"></i>
                <p class="mt-3">Generating report...</p>
            </div>
        </div>
    `);
    
    $('body').append(loadingOverlay);
    
    // Add loading styles
    $('<style>').prop('type', 'text/css').html(`
        .loading-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(255, 255, 255, 0.9);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 9999;
        }
        .loading-spinner {
            text-align: center;
            color: #667eea;
        }
        .table-hover-effect {
            background-color: #f8f9fa !important;
            transform: scale(1.01);
            transition: all 0.2s ease;
        }
    `).appendTo('head');
}

function formatDate(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

// Utility functions
function showToast(message, type = 'info') {
    const toast = $(`
        <div class="toast align-items-center text-white bg-${type} border-0" role="alert">
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        </div>
    `);
    
    $('.toast-container').append(toast);
    const bsToast = new bootstrap.Toast(toast[0]);
    bsToast.show();
}

function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 2
    }).format(amount);
}

function exportTableToCSV(tableSelector, filename) {
    const csv = [];
    const rows = $(tableSelector + ' tr');
    
    rows.each(function() {
        const row = [];
        $(this).find('th, td').each(function() {
            row.push('"' + $(this).text().replace(/"/g, '""') + '"');
        });
        csv.push(row.join(','));
    });
    
    const csvContent = csv.join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    
    window.URL.revokeObjectURL(url);
}

// Print functionality
function printReport() {
    window.print();
}

// Add print button if needed
$(document).ready(function() {
    if ($('.report-data').length > 0) {
        const printButton = $(`
            <button type="button" class="btn btn-outline-secondary btn-export" onclick="printReport()">
                <i class="fas fa-print me-1"></i>Print Report
            </button>
        `);
        $('.export-buttons').append(printButton);
    }
});