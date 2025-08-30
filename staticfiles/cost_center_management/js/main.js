// Cost Center Management JavaScript

$(document).ready(function() {
    // Initialize tooltips
    $('[data-toggle="tooltip"]').tooltip();
    
    // Initialize popovers
    $('[data-toggle="popover"]').popover();
    
    // Auto-format cost center codes
    $('.cost-center-code').on('input', function() {
        this.value = this.value.toUpperCase();
    });
    
    // Date validation
    $('.date-input').on('change', function() {
        var startDate = $('#id_start_date').val();
        var endDate = $('#id_end_date').val();
        
        if (startDate && endDate && startDate > endDate) {
            alert('Start date cannot be after end date.');
            $(this).val('');
        }
    });
    
    // Budget amount formatting
    $('.budget-amount').on('input', function() {
        var value = this.value.replace(/[^\d.]/g, '');
        if (value) {
            var num = parseFloat(value);
            if (!isNaN(num)) {
                this.value = num.toFixed(2);
            }
        }
    });
    
    // Search functionality
    $('#searchInput').on('keyup', function() {
        var value = $(this).val().toLowerCase();
        $('.cost-center-row').filter(function() {
            $(this).toggle($(this).text().toLowerCase().indexOf(value) > -1);
        });
    });
    
    // Filter functionality
    $('.filter-select').on('change', function() {
        var filterValue = $(this).val();
        var filterType = $(this).data('filter');
        
        if (filterValue) {
            $('.cost-center-row').hide();
            $('.cost-center-row[data-' + filterType + '="' + filterValue + '"]').show();
        } else {
            $('.cost-center-row').show();
        }
    });
    
    // Budget variance calculation
    function calculateBudgetVariance() {
        $('.budget-variance').each(function() {
            var budget = parseFloat($(this).data('budget')) || 0;
            var expenses = parseFloat($(this).data('expenses')) || 0;
            var variance = budget - expenses;
            
            $(this).text(variance.toFixed(2));
            $(this).removeClass('text-success text-danger');
            
            if (variance > 0) {
                $(this).addClass('text-success');
            } else if (variance < 0) {
                $(this).addClass('text-danger');
            }
        });
    }
    
    // Call budget variance calculation
    calculateBudgetVariance();
    
    // Progress bar animation
    $('.progress-bar').each(function() {
        var percentage = $(this).data('percentage');
        $(this).css('width', percentage + '%');
    });
    
    // Form validation
    $('.needs-validation').on('submit', function(event) {
        if (!this.checkValidity()) {
            event.preventDefault();
            event.stopPropagation();
        }
        $(this).addClass('was-validated');
    });
    
    // AJAX form submission
    $('.ajax-form').on('submit', function(e) {
        e.preventDefault();
        var form = $(this);
        var submitBtn = form.find('button[type="submit"]');
        var originalText = submitBtn.text();
        
        // Show loading state
        submitBtn.prop('disabled', true);
        submitBtn.html('<span class="loading-spinner"></span> Saving...');
        
        $.ajax({
            url: form.attr('action'),
            method: 'POST',
            data: form.serialize(),
            success: function(response) {
                if (response.success) {
                    showAlert('success', response.message);
                    if (response.redirect) {
                        setTimeout(function() {
                            window.location.href = response.redirect;
                        }, 1500);
                    }
                } else {
                    showAlert('danger', response.message || 'An error occurred.');
                }
            },
            error: function(xhr, status, error) {
                showAlert('danger', 'An error occurred while saving the data.');
            },
            complete: function() {
                // Restore button state
                submitBtn.prop('disabled', false);
                submitBtn.text(originalText);
            }
        });
    });
    
    // Delete confirmation
    $('.delete-confirm').on('click', function(e) {
        if (!confirm('Are you sure you want to delete this item? This action cannot be undone.')) {
            e.preventDefault();
        }
    });
    
    // Export functionality
    $('.export-btn').on('click', function(e) {
        e.preventDefault();
        var format = $(this).data('format');
        var url = $(this).attr('href');
        
        // Show loading state
        $(this).prop('disabled', true);
        $(this).html('<span class="loading-spinner"></span> Exporting...');
        
        // Create a temporary form for download
        var form = $('<form>', {
            'method': 'POST',
            'action': url
        }).append($('<input>', {
            'type': 'hidden',
            'name': 'format',
            'value': format
        })).append($('<input>', {
            'type': 'hidden',
            'name': 'csrfmiddlewaretoken',
            'value': $('[name=csrfmiddlewaretoken]').val()
        }));
        
        $('body').append(form);
        form.submit();
        form.remove();
        
        // Restore button state
        setTimeout(function() {
            $('.export-btn').prop('disabled', false);
            $('.export-btn').html('Export');
        }, 2000);
    });
    
    // Chart initialization (if Chart.js is available)
    if (typeof Chart !== 'undefined') {
        initializeCharts();
    }
    
    // Real-time updates
    if ($('.dashboard').length > 0) {
        setInterval(function() {
            updateDashboardStats();
        }, 300000); // Update every 5 minutes
    }
});

// Utility functions
function showAlert(type, message) {
    var alertHtml = '<div class="alert alert-' + type + ' alert-dismissible fade show" role="alert">' +
        message +
        '<button type="button" class="close" data-dismiss="alert" aria-label="Close">' +
        '<span aria-hidden="true">&times;</span>' +
        '</button>' +
        '</div>';
    
    $('.alert-container').prepend(alertHtml);
    
    // Auto-dismiss after 5 seconds
    setTimeout(function() {
        $('.alert').fadeOut();
    }, 5000);
}

function updateDashboardStats() {
    $.ajax({
        url: '/cost-center-management/api/dashboard-stats/',
        method: 'GET',
        success: function(data) {
            $('#total-cost-centers').text(data.total_cost_centers);
            $('#total-departments').text(data.total_departments);
            $('#total-budgets').text(data.total_budgets);
            $('#total-transactions').text(data.total_transactions);
        }
    });
}

function initializeCharts() {
    // Budget utilization chart
    var budgetCtx = document.getElementById('budgetUtilizationChart');
    if (budgetCtx) {
        new Chart(budgetCtx, {
            type: 'doughnut',
            data: {
                labels: ['Used', 'Remaining'],
                datasets: [{
                    data: [70, 30],
                    backgroundColor: ['#e74a3b', '#1cc88a'],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                legend: {
                    position: 'bottom'
                }
            }
        });
    }
    
    // Expense trend chart
    var expenseCtx = document.getElementById('expenseTrendChart');
    if (expenseCtx) {
        new Chart(expenseCtx, {
            type: 'line',
            data: {
                labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                datasets: [{
                    label: 'Expenses',
                    data: [12000, 19000, 15000, 25000, 22000, 30000],
                    borderColor: '#4e73df',
                    backgroundColor: 'rgba(78, 115, 223, 0.1)',
                    borderWidth: 2,
                    fill: true
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

// Cost center specific functions
function loadCostCenterDetails(costCenterId) {
    $.ajax({
        url: '/cost-center-management/api/cost-centers/' + costCenterId + '/stats/',
        method: 'GET',
        success: function(data) {
            $('#cost-center-stats').html(data.html);
        }
    });
}

function refreshCostCenterList() {
    location.reload();
}

// Department specific functions
function loadDepartmentCostCenters(departmentId) {
    $.ajax({
        url: '/cost-center-management/api/departments/' + departmentId + '/cost-centers/',
        method: 'GET',
        success: function(data) {
            $('#department-cost-centers').html(data.html);
        }
    });
}

// Budget specific functions
function calculateBudgetUtilization(budgetId) {
    $.ajax({
        url: '/cost-center-management/api/budgets/' + budgetId + '/utilization/',
        method: 'GET',
        success: function(data) {
            $('#budget-utilization-' + budgetId).text(data.utilization_percentage + '%');
            $('#budget-variance-' + budgetId).text(data.variance);
        }
    });
}
