// Cost Center Reports JavaScript

$(document).ready(function() {
    // Initialize tooltips
    $('[data-toggle="tooltip"]').tooltip();
    
    // Initialize progress bars
    $('.progress-bar').each(function() {
        var width = $(this).data('width');
        if (width) {
            $(this).css('width', width + '%');
        }
    });
    
    // Initialize DataTables for tables
    if ($.fn.DataTable) {
        $('.datatable').DataTable({
            "pageLength": 25,
            "order": [[0, "desc"]],
            "responsive": true,
            "language": {
                "search": "Search:",
                "lengthMenu": "Show _MENU_ entries per page",
                "info": "Showing _START_ to _END_ of _TOTAL_ entries",
                "infoEmpty": "Showing 0 to 0 of 0 entries",
                "infoFiltered": "(filtered from _MAX_ total entries)",
                "paginate": {
                    "first": "First",
                    "last": "Last",
                    "next": "Next",
                    "previous": "Previous"
                }
            }
        });
    }
    
    // Form validation
    $('.needs-validation').on('submit', function(event) {
        if (!this.checkValidity()) {
            event.preventDefault();
            event.stopPropagation();
        }
        $(this).addClass('was-validated');
    });
    
    // Date range picker initialization
    if ($.fn.daterangepicker) {
        $('.daterange').daterangepicker({
            opens: 'left',
            locale: {
                format: 'YYYY-MM-DD'
            }
        });
    }
    
    // Auto-generate report name
    $('#id_report_type, #id_start_date, #id_end_date').on('change', function() {
        generateReportName();
    });
    
    // Export functionality
    $('.export-btn').on('click', function(e) {
        e.preventDefault();
        var exportType = $(this).data('type');
        var reportId = $(this).data('report-id');
        
        if (confirm('Are you sure you want to export this report as ' + exportType.toUpperCase() + '?')) {
            window.location.href = '/accounting/cost-center-reports/reports/' + reportId + '/export/?type=' + exportType;
        }
    });
    
    // Delete confirmation
    $('.delete-btn').on('click', function(e) {
        if (!confirm('Are you sure you want to delete this item? This action cannot be undone.')) {
            e.preventDefault();
        }
    });
    
    // Toggle view functionality
    $('.toggle-view-btn').on('click', function(e) {
        e.preventDefault();
        var target = $(this).data('target');
        $('.view-content').hide();
        $('#' + target).show();
        $('.toggle-view-btn').removeClass('active');
        $(this).addClass('active');
    });
    
    // Search functionality
    $('#search-form').on('submit', function(e) {
        var searchTerm = $('#search-input').val().trim();
        if (searchTerm === '') {
            e.preventDefault();
            alert('Please enter a search term.');
        }
    });
    
    // Real-time search
    $('#search-input').on('keyup', function() {
        var searchTerm = $(this).val().toLowerCase();
        $('.searchable-item').each(function() {
            var text = $(this).text().toLowerCase();
            if (text.includes(searchTerm)) {
                $(this).show();
            } else {
                $(this).hide();
            }
        });
    });
    
    // Chart initialization (if Chart.js is available)
    if (typeof Chart !== 'undefined') {
        initializeCharts();
    }
    
    // Print functionality
    $('.print-btn').on('click', function(e) {
        e.preventDefault();
        window.print();
    });
});

// Generate report name based on selected options
function generateReportName() {
    var reportType = $('#id_report_type').val();
    var startDate = $('#id_start_date').val();
    var endDate = $('#id_end_date').val();
    var costCenter = $('#id_cost_center option:selected').text();
    var department = $('#id_department option:selected').text();
    
    if (reportType && startDate && endDate) {
        var name = reportType.charAt(0).toUpperCase() + reportType.slice(1).replace('_', ' ') + ' Report';
        name += ' - ' + startDate + ' to ' + endDate;
        
        if (costCenter && costCenter !== '---------') {
            name += ' - ' + costCenter;
        } else if (department && department !== '---------') {
            name += ' - ' + department;
        }
        
        $('#id_report_name').val(name);
    }
}

// Initialize charts
function initializeCharts() {
    // Cost Center Distribution Chart
    var ctx = document.getElementById('costCenterChart');
    if (ctx) {
        new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: chartData.labels,
                datasets: [{
                    data: chartData.values,
                    backgroundColor: [
                        '#4e73df',
                        '#1cc88a',
                        '#36b9cc',
                        '#f6c23e',
                        '#e74a3b',
                        '#6f42c1',
                        '#fd7e14',
                        '#20c9a6'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }
    
    // Budget vs Actual Chart
    var budgetCtx = document.getElementById('budgetChart');
    if (budgetCtx) {
        new Chart(budgetCtx, {
            type: 'bar',
            data: {
                labels: budgetData.labels,
                datasets: [{
                    label: 'Budget',
                    data: budgetData.budget,
                    backgroundColor: '#4e73df'
                }, {
                    label: 'Actual',
                    data: budgetData.actual,
                    backgroundColor: '#1cc88a'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }
}

// Format currency
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-AE', {
        style: 'currency',
        currency: 'AED'
    }).format(amount);
}

// Format percentage
function formatPercentage(value) {
    return value.toFixed(2) + '%';
}

// Show loading spinner
function showLoading() {
    $('#loading-spinner').show();
}

// Hide loading spinner
function hideLoading() {
    $('#loading-spinner').hide();
}

// Show success message
function showSuccess(message) {
    var alert = '<div class="alert alert-success alert-dismissible fade show" role="alert">' +
                message +
                '<button type="button" class="close" data-dismiss="alert" aria-label="Close">' +
                '<span aria-hidden="true">&times;</span>' +
                '</button>' +
                '</div>';
    $('#alerts-container').append(alert);
}

// Show error message
function showError(message) {
    var alert = '<div class="alert alert-danger alert-dismissible fade show" role="alert">' +
                message +
                '<button type="button" class="close" data-dismiss="alert" aria-label="Close">' +
                '<span aria-hidden="true">&times;</span>' +
                '</button>' +
                '</div>';
    $('#alerts-container').append(alert);
}

// AJAX request helper
function ajaxRequest(url, method, data, successCallback, errorCallback) {
    $.ajax({
        url: url,
        method: method,
        data: data,
        headers: {
            'X-CSRFToken': $('[name=csrfmiddlewaretoken]').val()
        },
        success: function(response) {
            if (successCallback) {
                successCallback(response);
            }
        },
        error: function(xhr, status, error) {
            if (errorCallback) {
                errorCallback(xhr, status, error);
            } else {
                showError('An error occurred: ' + error);
            }
        }
    });
}

// Export report function
function exportReport(reportId, format) {
    showLoading();
    ajaxRequest(
        '/accounting/cost-center-reports/reports/' + reportId + '/export/',
        'POST',
        {export_type: format},
        function(response) {
            hideLoading();
            if (response.success) {
                showSuccess('Report exported successfully!');
                // Trigger download
                window.location.href = response.download_url;
            } else {
                showError('Failed to export report: ' + response.error);
            }
        },
        function(xhr, status, error) {
            hideLoading();
            showError('Export failed: ' + error);
        }
    );
}

// Refresh report data
function refreshReportData(reportId) {
    showLoading();
    ajaxRequest(
        '/accounting/cost-center-reports/reports/' + reportId + '/refresh/',
        'POST',
        {},
        function(response) {
            hideLoading();
            if (response.success) {
                showSuccess('Report data refreshed successfully!');
                location.reload();
            } else {
                showError('Failed to refresh report data: ' + response.error);
            }
        },
        function(xhr, status, error) {
            hideLoading();
            showError('Refresh failed: ' + error);
        }
    );
}
