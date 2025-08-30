// Tax Settings Dashboard JavaScript

$(document).ready(function() {
    // Initialize dashboard functionality
    initializeDashboard();
    
    // Auto-refresh statistics every 5 minutes
    setInterval(refreshStatistics, 300000);
    
    // Initialize tooltips
    $('[data-toggle="tooltip"]').tooltip();
    
    // Initialize popovers
    $('[data-toggle="popover"]').popover();
});

function initializeDashboard() {
    // Add loading states to cards
    addLoadingStates();
    
    // Initialize real-time updates
    initializeRealTimeUpdates();
    
    // Add card hover effects
    addCardHoverEffects();
    
    // Initialize search functionality
    initializeSearch();
    
    // Add export functionality
    initializeExport();
}

function addLoadingStates() {
    // Add loading state to statistics cards
    $('.card').on('click', function() {
        if (!$(this).hasClass('loading')) {
            $(this).addClass('loading');
            setTimeout(() => {
                $(this).removeClass('loading');
            }, 1000);
        }
    });
}

function initializeRealTimeUpdates() {
    // Update VAT summary in real-time
    updateVATSummary();
    
    // Update recent transactions
    updateRecentTransactions();
    
    // Update audit logs
    updateAuditLogs();
}

function updateVATSummary() {
    // Fetch current month VAT summary via AJAX
    $.ajax({
        url: '/tax-settings/api/vat-summary/',
        method: 'GET',
        success: function(data) {
            if (data.success) {
                updateVATSummaryDisplay(data.summary);
            }
        },
        error: function(xhr, status, error) {
            console.error('Error fetching VAT summary:', error);
        }
    });
}

function updateVATSummaryDisplay(summary) {
    // Update the VAT summary display with new data
    $('.vat-summary .total-sales').text('AED ' + summary.total_sales);
    $('.vat-summary .total-purchases').text('AED ' + summary.total_purchases);
    $('.vat-summary .sales-tax').text('AED ' + summary.total_sales_tax);
    $('.vat-summary .purchase-tax').text('AED ' + summary.total_purchase_tax);
    $('.vat-summary .net-vat').text('AED ' + summary.net_vat_payable);
    
    // Add animation effect
    $('.vat-summary .card-body').addClass('updated');
    setTimeout(() => {
        $('.vat-summary .card-body').removeClass('updated');
    }, 1000);
}

function updateRecentTransactions() {
    // Fetch recent transactions via AJAX
    $.ajax({
        url: '/tax-settings/api/recent-transactions/',
        method: 'GET',
        success: function(data) {
            if (data.success) {
                updateTransactionsTable(data.transactions);
            }
        },
        error: function(xhr, status, error) {
            console.error('Error fetching recent transactions:', error);
        }
    });
}

function updateTransactionsTable(transactions) {
    const tbody = $('.recent-transactions tbody');
    tbody.empty();
    
    transactions.forEach(function(transaction) {
        const row = `
            <tr>
                <td>${transaction.document_number}</td>
                <td>
                    <span class="badge badge-${transaction.transaction_type === 'sale' ? 'success' : 'info'}">
                        ${transaction.transaction_type_display}
                    </span>
                </td>
                <td>AED ${transaction.total_amount}</td>
                <td>${transaction.document_date}</td>
            </tr>
        `;
        tbody.append(row);
    });
}

function updateAuditLogs() {
    // Fetch recent audit logs via AJAX
    $.ajax({
        url: '/tax-settings/api/recent-audit-logs/',
        method: 'GET',
        success: function(data) {
            if (data.success) {
                updateAuditLogsTable(data.logs);
            }
        },
        error: function(xhr, status, error) {
            console.error('Error fetching audit logs:', error);
        }
    });
}

function updateAuditLogsTable(logs) {
    const tbody = $('.audit-logs tbody');
    tbody.empty();
    
    logs.forEach(function(log) {
        const actionClass = log.action === 'create' ? 'success' : 
                           log.action === 'update' ? 'warning' : 'danger';
        
        const row = `
            <tr>
                <td>
                    <span class="badge badge-${actionClass}">
                        ${log.action_display}
                    </span>
                </td>
                <td>${log.model_name}</td>
                <td>${log.field_name || '-'}</td>
                <td>${log.user || 'System'}</td>
                <td>${log.timestamp}</td>
            </tr>
        `;
        tbody.append(row);
    });
}

function addCardHoverEffects() {
    // Add smooth hover effects to cards
    $('.card').hover(
        function() {
            $(this).addClass('card-hover');
        },
        function() {
            $(this).removeClass('card-hover');
        }
    );
}

function initializeSearch() {
    // Initialize search functionality
    $('#searchInput').on('keyup', function() {
        const searchTerm = $(this).val().toLowerCase();
        
        $('.table tbody tr').each(function() {
            const text = $(this).text().toLowerCase();
            if (text.includes(searchTerm)) {
                $(this).show();
            } else {
                $(this).hide();
            }
        });
    });
}

function initializeExport() {
    // Add export functionality to export button
    $('.export-btn').on('click', function(e) {
        e.preventDefault();
        
        const button = $(this);
        const originalText = button.text();
        
        // Show loading state
        button.text('Exporting...').prop('disabled', true);
        
        // Trigger export
        window.location.href = '/tax-settings/export/';
        
        // Reset button after delay
        setTimeout(() => {
            button.text(originalText).prop('disabled', false);
        }, 2000);
    });
}

function refreshStatistics() {
    // Refresh all statistics on the dashboard
    console.log('Refreshing dashboard statistics...');
    
    // Add refresh animation
    $('.statistics-card').addClass('refreshing');
    
    // Fetch updated statistics
    $.ajax({
        url: '/tax-settings/api/dashboard-stats/',
        method: 'GET',
        success: function(data) {
            if (data.success) {
                updateStatistics(data.stats);
            }
        },
        error: function(xhr, status, error) {
            console.error('Error refreshing statistics:', error);
        },
        complete: function() {
            // Remove refresh animation
            setTimeout(() => {
                $('.statistics-card').removeClass('refreshing');
            }, 500);
        }
    });
}

function updateStatistics(stats) {
    // Update statistics display
    $('.total-jurisdictions').text(stats.total_jurisdictions);
    $('.total-tax-types').text(stats.total_tax_types);
    $('.total-tax-rates').text(stats.total_tax_rates);
    $('.total-product-categories').text(stats.total_product_categories);
    $('.total-customer-profiles').text(stats.total_customer_profiles);
    $('.total-supplier-profiles').text(stats.total_supplier_profiles);
}

// Tax Calculator functionality
function initializeTaxCalculator() {
    $('#taxCalculatorForm').on('submit', function(e) {
        e.preventDefault();
        
        const formData = {
            taxable_amount: $('#id_taxable_amount').val(),
            tax_rate: $('#id_tax_rate').val(),
            currency: $('#id_currency').val()
        };
        
        // Show loading state
        $('#calculatorResult').html('<div class="text-center"><i class="fas fa-spinner fa-spin"></i> Calculating...</div>');
        
        // Calculate tax via AJAX
        $.ajax({
            url: '/tax-settings/api/calculate-tax/',
            method: 'POST',
            data: JSON.stringify(formData),
            contentType: 'application/json',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            },
            success: function(data) {
                if (data.success) {
                    displayTaxCalculationResult(data.result);
                } else {
                    $('#calculatorResult').html('<div class="alert alert-danger">Error: ' + data.error + '</div>');
                }
            },
            error: function(xhr, status, error) {
                $('#calculatorResult').html('<div class="alert alert-danger">Error calculating tax. Please try again.</div>');
            }
        });
    });
}

function displayTaxCalculationResult(result) {
    const resultHtml = `
        <div class="card">
            <div class="card-header">
                <h6 class="mb-0">Tax Calculation Result</h6>
            </div>
            <div class="card-body">
                <div class="row">
                    <div class="col-md-6">
                        <p><strong>Taxable Amount:</strong> ${result.currency} ${result.taxable_amount}</p>
                        <p><strong>Tax Rate:</strong> ${result.tax_rate_name} (${result.tax_rate_percentage}%)</p>
                    </div>
                    <div class="col-md-6">
                        <p><strong>Tax Amount:</strong> ${result.currency} ${result.tax_amount}</p>
                        <p><strong>Total Amount:</strong> ${result.currency} ${result.total_amount}</p>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    $('#calculatorResult').html(resultHtml);
}

// Utility functions
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

// Chart functionality (if using charts)
function initializeCharts() {
    // Initialize any charts on the dashboard
    if (typeof Chart !== 'undefined') {
        // VAT Summary Chart
        const ctx = document.getElementById('vatSummaryChart');
        if (ctx) {
            new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: ['Sales Tax', 'Purchase Tax'],
                    datasets: [{
                        data: [12, 19],
                        backgroundColor: [
                            '#1cc88a',
                            '#36b9cc'
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false
                }
            });
        }
    }
}

// Notification system
function showNotification(message, type = 'info') {
    const notification = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="close" data-dismiss="alert" aria-label="Close">
                <span aria-hidden="true">&times;</span>
            </button>
        </div>
    `;
    
    $('#notifications').append(notification);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        $('.alert').fadeOut();
    }, 5000);
}

// Keyboard shortcuts
$(document).on('keydown', function(e) {
    // Ctrl/Cmd + N for new tax rate
    if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
        e.preventDefault();
        window.location.href = '/tax-settings/tax-rates/create/';
    }
    
    // Ctrl/Cmd + C for calculator
    if ((e.ctrlKey || e.metaKey) && e.key === 'c') {
        e.preventDefault();
        window.location.href = '/tax-settings/calculator/';
    }
    
    // Ctrl/Cmd + R for refresh
    if ((e.ctrlKey || e.metaKey) && e.key === 'r') {
        e.preventDefault();
        refreshStatistics();
    }
});

// Print functionality
function printDashboard() {
    window.print();
}

// Export functionality
function exportDashboardData() {
    const format = $('#exportFormat').val();
    const url = `/tax-settings/export/?format=${format}`;
    window.location.href = url;
}

// Initialize everything when document is ready
$(document).ready(function() {
    initializeDashboard();
    initializeTaxCalculator();
    initializeCharts();
    
    // Show welcome notification
    showNotification('Welcome to Tax Settings Dashboard!', 'success');
});
