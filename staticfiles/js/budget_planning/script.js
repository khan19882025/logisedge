// Budget Planning Module JavaScript

$(document).ready(function() {
    // Initialize all components
    initializeBudgetVsActual();
    initializeCharts();
    initializeFormValidation();
    initializeDynamicFilters();
    initializeExportFunctions();
});

// Budget vs Actual Comparison Functions
function initializeBudgetVsActual() {
    // Auto-refresh dashboard data every 5 minutes
    setInterval(function() {
        refreshDashboardData();
    }, 300000);
    
    // Initialize tooltips
    $('[data-toggle="tooltip"]').tooltip();
    
    // Initialize popovers
    $('[data-toggle="popover"]').popover();
}

// Chart initialization
function initializeCharts() {
    // Budget vs Actual Chart
    const budgetVsActualCtx = document.getElementById('budgetVsActualChart');
    if (budgetVsActualCtx) {
        new Chart(budgetVsActualCtx.getContext('2d'), {
            type: 'bar',
            data: {
                labels: ['Budget', 'Actual'],
                datasets: [{
                    label: 'Amount (AED)',
                    data: [0, 0],
                    backgroundColor: [
                        'rgba(54, 162, 235, 0.8)',
                        'rgba(255, 99, 132, 0.8)'
                    ],
                    borderColor: [
                        'rgba(54, 162, 235, 1)',
                        'rgba(255, 99, 132, 1)'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return 'AED ' + value.toLocaleString();
                            }
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    }
                }
            }
        });
    }
    
    // Variance Distribution Chart
    const varianceDistributionCtx = document.getElementById('varianceDistributionChart');
    if (varianceDistributionCtx) {
        new Chart(varianceDistributionCtx.getContext('2d'), {
            type: 'doughnut',
            data: {
                labels: ['Under Budget', 'Over Budget', 'On Target'],
                datasets: [{
                    data: [0, 0, 0],
                    backgroundColor: [
                        'rgba(40, 167, 69, 0.8)',
                        'rgba(220, 53, 69, 0.8)',
                        'rgba(255, 193, 7, 0.8)'
                    ],
                    borderColor: [
                        'rgba(40, 167, 69, 1)',
                        'rgba(220, 53, 69, 1)',
                        'rgba(255, 193, 7, 1)'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        display: true,
                        position: 'bottom'
                    }
                }
            }
        });
    }
}

// Form validation
function initializeFormValidation() {
    $('.needs-validation').on('submit', function(event) {
        if (!this.checkValidity()) {
            event.preventDefault();
            event.stopPropagation();
        }
        $(this).addClass('was-validated');
    });
    
    // Custom validation for date ranges
    $('#id_end_date').on('change', function() {
        const startDate = $('#id_start_date').val();
        const endDate = $(this).val();
        
        if (startDate && endDate && startDate >= endDate) {
            $(this).addClass('is-invalid');
            $(this).next('.invalid-feedback').text('End date must be after start date.');
        } else {
            $(this).removeClass('is-invalid');
            $(this).next('.invalid-feedback').text('');
        }
    });
}

// Dynamic filters
function initializeDynamicFilters() {
    // Department change handler
    $('#id_department').change(function() {
        const departmentId = $(this).val();
        const costCenterSelect = $('#id_cost_center');
        
        if (departmentId) {
            // Show loading spinner
            costCenterSelect.prop('disabled', true);
            costCenterSelect.html('<option value="">Loading...</option>');
            
            // Load cost centers for the selected department
            $.get(`/accounting/budget-planning/api/cost-centers-by-department/?department_id=${departmentId}`)
                .done(function(data) {
                    costCenterSelect.empty();
                    costCenterSelect.append('<option value="">All Cost Centers</option>');
                    
                    data.cost_centers.forEach(function(costCenter) {
                        costCenterSelect.append(
                            `<option value="${costCenter.id}">${costCenter.code} - ${costCenter.name}</option>`
                        );
                    });
                })
                .fail(function() {
                    costCenterSelect.html('<option value="">Error loading cost centers</option>');
                })
                .always(function() {
                    costCenterSelect.prop('disabled', false);
                });
        } else {
            // Reset cost center options
            costCenterSelect.empty();
            costCenterSelect.append('<option value="">All Cost Centers</option>');
        }
    });
    
    // Period change handler
    $('#id_period').change(function() {
        const period = $(this).val();
        const startDateField = $('#id_start_date');
        const endDateField = $('#id_end_date');
        
        if (period === 'custom') {
            startDateField.prop('required', true);
            endDateField.prop('required', true);
            startDateField.closest('.form-group').show();
            endDateField.closest('.form-group').show();
        } else {
            startDateField.prop('required', false);
            endDateField.prop('required', false);
            startDateField.closest('.form-group').hide();
            endDateField.closest('.form-group').hide();
        }
    });
}

// Export functions
function initializeExportFunctions() {
    // Excel export
    window.exportToExcel = function() {
        const table = document.querySelector('.table-responsive table');
        if (!table) {
            alert('No data to export');
            return;
        }
        
        // Create workbook and worksheet
        const wb = XLSX.utils.book_new();
        const ws = XLSX.utils.table_to_sheet(table);
        
        // Add worksheet to workbook
        XLSX.utils.book_append_sheet(wb, ws, 'Budget vs Actual Report');
        
        // Generate filename
        const filename = `budget_vs_actual_report_${new Date().toISOString().split('T')[0]}.xlsx`;
        
        // Save file
        XLSX.writeFile(wb, filename);
    };
    
    // PDF export
    window.exportToPDF = function() {
        const element = document.querySelector('.table-responsive');
        if (!element) {
            alert('No data to export');
            return;
        }
        
        const opt = {
            margin: 1,
            filename: `budget_vs_actual_report_${new Date().toISOString().split('T')[0]}.pdf`,
            image: { type: 'jpeg', quality: 0.98 },
            html2canvas: { scale: 2 },
            jsPDF: { unit: 'in', format: 'letter', orientation: 'landscape' }
        };
        
        html2pdf().set(opt).from(element).save();
    };
}

// Refresh dashboard data
function refreshDashboardData() {
    $.get('/accounting/budget-planning/api/budget-summary/')
        .done(function(data) {
            // Update summary statistics
            updateSummaryStats(data);
            
            // Update charts
            updateCharts(data);
        })
        .fail(function() {
            console.log('Failed to refresh dashboard data');
        });
}

// Update summary statistics
function updateSummaryStats(data) {
    if (data.total_budget_amount !== undefined) {
        $('.total-budget-amount').text('AED ' + parseFloat(data.total_budget_amount).toLocaleString());
    }
    if (data.total_actual_amount !== undefined) {
        $('.total-actual-amount').text('AED ' + parseFloat(data.total_actual_amount).toLocaleString());
    }
    if (data.total_variance !== undefined) {
        $('.total-variance').text('AED ' + parseFloat(data.total_variance).toLocaleString());
    }
}

// Update charts
function updateCharts(data) {
    // This would update the existing charts with new data
    // Implementation depends on the specific chart library being used
}

// Load template
function loadTemplate(template) {
    const today = new Date();
    const currentYear = today.getFullYear();
    let startDate, endDate, reportName, reportType, period;
    
    switch(template) {
        case 'monthly':
            startDate = new Date(today.getFullYear(), today.getMonth(), 1);
            endDate = new Date(today.getFullYear(), today.getMonth() + 1, 0);
            reportName = `Monthly Budget vs Actual Report - ${startDate.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}`;
            reportType = 'summary';
            period = 'monthly';
            break;
        case 'quarterly':
            const quarter = Math.floor(today.getMonth() / 3);
            startDate = new Date(today.getFullYear(), quarter * 3, 1);
            endDate = new Date(today.getFullYear(), (quarter + 1) * 3, 0);
            reportName = `Quarterly Budget vs Actual Report - Q${quarter + 1} ${today.getFullYear()}`;
            reportType = 'summary';
            period = 'quarterly';
            break;
        case 'annual':
            startDate = new Date(today.getFullYear(), 0, 1);
            endDate = new Date(today.getFullYear(), 11, 31);
            reportName = `Annual Budget vs Actual Report - ${today.getFullYear()}`;
            reportType = 'summary';
            period = 'yearly';
            break;
        case 'variance':
            startDate = new Date(today.getFullYear(), today.getMonth(), 1);
            endDate = today;
            reportName = `Variance Analysis Report - ${startDate.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}`;
            reportType = 'variance';
            period = 'monthly';
            break;
    }
    
    // Populate form fields
    $('#id_report_name').val(reportName);
    $('#id_report_type').val(reportType);
    $('#id_fiscal_year').val(currentYear);
    $('#id_period').val(period);
    $('#id_start_date').val(startDate.toISOString().split('T')[0]);
    $('#id_end_date').val(endDate.toISOString().split('T')[0]);
    
    // Show success message
    showAlert('Template loaded successfully!', 'success');
}

// Show alert message
function showAlert(message, type = 'info') {
    const alertClass = type === 'success' ? 'alert-success' : 
                      type === 'error' ? 'alert-danger' : 
                      type === 'warning' ? 'alert-warning' : 'alert-info';
    
    const alertHtml = `
        <div class="alert ${alertClass} alert-dismissible fade show" role="alert">
            <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : type === 'warning' ? 'exclamation-triangle' : 'info-circle'} mr-2"></i>
            ${message}
            <button type="button" class="close" data-dismiss="alert">
                <span>&times;</span>
            </button>
        </div>
    `;
    
    $('.card-header').after(alertHtml);
    
    // Auto-dismiss after 3 seconds
    setTimeout(function() {
        $('.alert').fadeOut();
    }, 3000);
}

// Format currency
function formatCurrency(amount) {
    return 'AED ' + parseFloat(amount).toLocaleString('en-US', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}

// Format percentage
function formatPercentage(value) {
    return parseFloat(value).toFixed(1) + '%';
}

// Calculate variance
function calculateVariance(budget, actual) {
    return budget - actual;
}

// Calculate variance percentage
function calculateVariancePercentage(budget, actual) {
    if (budget === 0) return 0;
    return ((budget - actual) / budget) * 100;
}

// Check if over budget
function isOverBudget(budget, actual) {
    return actual > budget;
}

// Get variance status
function getVarianceStatus(variance) {
    if (variance < 0) return 'over-budget';
    if (variance > 0) return 'under-budget';
    return 'on-target';
}

// Initialize data tables
function initializeDataTables() {
    if ($.fn.DataTable) {
        $('.data-table').DataTable({
            responsive: true,
            pageLength: 25,
            order: [[0, 'desc']],
            language: {
                search: "Search:",
                lengthMenu: "Show _MENU_ entries per page",
                info: "Showing _START_ to _END_ of _TOTAL_ entries",
                paginate: {
                    first: "First",
                    last: "Last",
                    next: "Next",
                    previous: "Previous"
                }
            }
        });
    }
}

// Initialize select2 for better dropdowns
function initializeSelect2() {
    if ($.fn.select2) {
        $('.select2').select2({
            theme: 'bootstrap4',
            width: '100%'
        });
    }
}

// Initialize date pickers
function initializeDatePickers() {
    if ($.fn.datepicker) {
        $('.datepicker').datepicker({
            format: 'yyyy-mm-dd',
            autoclose: true,
            todayHighlight: true
        });
    }
}

// Initialize all components when document is ready
$(document).ready(function() {
    initializeDataTables();
    initializeSelect2();
    initializeDatePickers();
});
