// Tax Filing Module JavaScript

$(document).ready(function() {
    // Initialize tooltips
    $('[data-toggle="tooltip"]').tooltip();
    
    // Initialize date pickers
    $('input[type="date"]').datepicker({
        format: 'yyyy-mm-dd',
        autoclose: true,
        todayHighlight: true
    });
    
    // Form validation
    $('form').on('submit', function() {
        var isValid = true;
        
        // Check required fields
        $(this).find('[required]').each(function() {
            if (!$(this).val()) {
                $(this).addClass('is-invalid');
                isValid = false;
            } else {
                $(this).removeClass('is-invalid');
            }
        });
        
        // Check date range
        var startDate = $('input[name="start_date"]').val();
        var endDate = $('input[name="end_date"]').val();
        
        if (startDate && endDate && startDate >= endDate) {
            $('input[name="end_date"]').addClass('is-invalid');
            isValid = false;
        }
        
        return isValid;
    });
    
    // Real-time search
    $('#search-input').on('keyup', function() {
        var value = $(this).val().toLowerCase();
        $('table tbody tr').filter(function() {
            $(this).toggle($(this).text().toLowerCase().indexOf(value) > -1);
        });
    });
    
    // Filter functionality
    $('.filter-form').on('change', 'select, input', function() {
        $(this).closest('form').submit();
    });
    
    // Export functionality
    $('.export-btn').on('click', function(e) {
        e.preventDefault();
        var format = $(this).data('format');
        var reportId = $(this).data('report-id');
        
        // Show loading spinner
        $(this).html('<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Exporting...');
        $(this).prop('disabled', true);
        
        // Make AJAX request
        $.ajax({
            url: '/tax-filing/reports/' + reportId + '/export/',
            method: 'POST',
            data: {
                export_format: format,
                csrfmiddlewaretoken: $('[name=csrfmiddlewaretoken]').val()
            },
            success: function(response) {
                // Show success message
                showAlert('success', 'Report exported successfully!');
                
                // Reset button
                $('.export-btn').html('Export');
                $('.export-btn').prop('disabled', false);
            },
            error: function(xhr, status, error) {
                // Show error message
                showAlert('danger', 'Export failed: ' + error);
                
                // Reset button
                $('.export-btn').html('Export');
                $('.export-btn').prop('disabled', false);
            }
        });
    });
    
    // Validation issue resolution
    $('.resolve-validation').on('click', function(e) {
        e.preventDefault();
        var validationId = $(this).data('validation-id');
        var row = $(this).closest('tr');
        
        if (confirm('Are you sure you want to mark this validation issue as resolved?')) {
            $.ajax({
                url: '/tax-filing/validations/' + validationId + '/resolve/',
                method: 'POST',
                data: {
                    csrfmiddlewaretoken: $('[name=csrfmiddlewaretoken]').val()
                },
                success: function(response) {
                    row.fadeOut();
                    showAlert('success', 'Validation issue resolved successfully!');
                },
                error: function(xhr, status, error) {
                    showAlert('danger', 'Failed to resolve validation issue: ' + error);
                }
            });
        }
    });
    
    // Chart initialization
    if (typeof Chart !== 'undefined') {
        // Monthly summary chart
        var ctx = document.getElementById('monthlySummaryChart');
        if (ctx) {
            var monthlyData = window.monthlyData || [];
            var labels = [];
            var outputData = [];
            var inputData = [];
            var adjustmentData = [];
            
            monthlyData.forEach(function(item) {
                var monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                                 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
                labels.push(monthNames[item.month - 1]);
                outputData.push(parseFloat(item.total_output));
                inputData.push(parseFloat(item.total_input));
                adjustmentData.push(parseFloat(item.total_adjustments));
            });
            
            new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Output Tax',
                        data: outputData,
                        borderColor: 'rgb(75, 192, 192)',
                        backgroundColor: 'rgba(75, 192, 192, 0.2)',
                        tension: 0.1
                    }, {
                        label: 'Input Tax',
                        data: inputData,
                        borderColor: 'rgb(255, 99, 132)',
                        backgroundColor: 'rgba(255, 99, 132, 0.2)',
                        tension: 0.1
                    }, {
                        label: 'Adjustments',
                        data: adjustmentData,
                        borderColor: 'rgb(255, 205, 86)',
                        backgroundColor: 'rgba(255, 205, 86, 0.2)',
                        tension: 0.1
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        }
    }
    
    // Print functionality
    $('.print-btn').on('click', function(e) {
        e.preventDefault();
        window.print();
    });
    
    // Bulk actions
    $('.bulk-action-form').on('submit', function(e) {
        var selectedItems = $('input[name="selected_items"]:checked');
        
        if (selectedItems.length === 0) {
            e.preventDefault();
            showAlert('warning', 'Please select at least one item.');
            return false;
        }
        
        var action = $('select[name="bulk_action"]').val();
        if (!action) {
            e.preventDefault();
            showAlert('warning', 'Please select an action.');
            return false;
        }
        
        if (!confirm('Are you sure you want to perform this action on ' + selectedItems.length + ' item(s)?')) {
            e.preventDefault();
            return false;
        }
    });
    
    // Select all functionality
    $('.select-all').on('change', function() {
        var isChecked = $(this).is(':checked');
        $('input[name="selected_items"]').prop('checked', isChecked);
    });
    
    // Auto-save functionality
    var autoSaveTimer;
    $('.auto-save-form').on('change', 'input, select, textarea', function() {
        clearTimeout(autoSaveTimer);
        autoSaveTimer = setTimeout(function() {
            $('.auto-save-form').submit();
        }, 2000);
    });
});

// Utility functions
function showAlert(type, message) {
    var alertHtml = '<div class="alert alert-' + type + ' alert-dismissible fade show" role="alert">' +
                    message +
                    '<button type="button" class="close" data-dismiss="alert" aria-label="Close">' +
                    '<span aria-hidden="true">&times;</span>' +
                    '</button>' +
                    '</div>';
    
    $('.alert-container').html(alertHtml);
    
    // Auto-dismiss after 5 seconds
    setTimeout(function() {
        $('.alert').fadeOut();
    }, 5000);
}

function formatCurrency(amount, currency) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: currency || 'AED'
    }).format(amount);
}

function formatDate(dateString) {
    var date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

// API functions
function getTaxFilingData(reportId) {
    return $.ajax({
        url: '/tax-filing/api/reports/' + reportId + '/',
        method: 'GET'
    });
}

function updateTaxFilingStatus(reportId, status) {
    return $.ajax({
        url: '/tax-filing/api/reports/' + reportId + '/status/',
        method: 'POST',
        data: {
            status: status,
            csrfmiddlewaretoken: $('[name=csrfmiddlewaretoken]').val()
        }
    });
}

// Validation functions
function validateVATNumber(vatNumber) {
    // Basic VAT number validation (can be customized based on country)
    var vatRegex = /^[A-Z]{2}[0-9A-Z]+$/;
    return vatRegex.test(vatNumber);
}

function validateTaxRate(rate) {
    var validRates = [0, 5, 12, 18];
    return validRates.includes(parseFloat(rate));
}

// Export functions
function exportToPDF(reportId) {
    window.open('/tax-filing/reports/' + reportId + '/export/?format=pdf', '_blank');
}

function exportToExcel(reportId) {
    window.open('/tax-filing/reports/' + reportId + '/export/?format=excel', '_blank');
}

// Chart functions
function updateChart(chartId, newData) {
    var chart = Chart.getChart(chartId);
    if (chart) {
        chart.data = newData;
        chart.update();
    }
}

// Print functions
function printReport(reportId) {
    var printWindow = window.open('/tax-filing/reports/' + reportId + '/print/', '_blank');
    printWindow.onload = function() {
        printWindow.print();
    };
}
