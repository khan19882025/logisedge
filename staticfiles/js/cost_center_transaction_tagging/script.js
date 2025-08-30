// Cost Center Transaction Tagging JavaScript

$(document).ready(function() {
    // Initialize tooltips and popovers
    $('[data-toggle="tooltip"]').tooltip();
    $('[data-toggle="popover"]').popover();
    
    // Initialize DataTables if available
    if ($.fn.DataTable) {
        $('.datatable').DataTable({
            "pageLength": 25,
            "responsive": true,
            "language": {
                "search": "Search:",
                "lengthMenu": "Show _MENU_ entries per page",
                "info": "Showing _START_ to _END_ of _TOTAL_ entries",
                "infoEmpty": "Showing 0 to 0 of 0 entries",
                "infoFiltered": "(filtered from _MAX_ total entries)",
                "emptyTable": "No data available in table",
                "zeroRecords": "No matching records found"
            }
        });
    }
    
    // Auto-format amount fields
    $('.amount-input').on('input', function() {
        var value = $(this).val();
        // Remove non-numeric characters except decimal point
        value = value.replace(/[^\d.]/g, '');
        // Ensure only one decimal point
        var parts = value.split('.');
        if (parts.length > 2) {
            value = parts[0] + '.' + parts.slice(1).join('');
        }
        // Limit to 2 decimal places
        if (parts.length === 2 && parts[1].length > 2) {
            value = parts[0] + '.' + parts[1].substring(0, 2);
        }
        $(this).val(value);
    });
    
    // Auto-generate transaction ID if empty
    $('#id_transaction_id').on('blur', function() {
        if (!$(this).val()) {
            var timestamp = new Date().getTime();
            var random = Math.floor(Math.random() * 1000);
            $(this).val('TXN-' + timestamp + '-' + random);
        }
    });
    
    // Set default date to today if empty
    if (!$('#id_transaction_date').val()) {
        var today = new Date().toISOString().split('T')[0];
        $('#id_transaction_date').val(today);
    }
    
    // Cost center change handler
    $('#id_cost_center').on('change', function() {
        var costCenterId = $(this).val();
        if (costCenterId) {
            // You can add AJAX call here to get cost center details
            // and update related fields
        }
    });
    
    // Transaction type change handler
    $('#id_transaction_type').on('change', function() {
        var transactionType = $(this).val();
        // You can add logic here to show/hide fields based on transaction type
    });
    
    // Form validation
    $('.needs-validation').on('submit', function(event) {
        if (!this.checkValidity()) {
            event.preventDefault();
            event.stopPropagation();
        }
        $(this).addClass('was-validated');
    });
    
    // Search and filter functionality
    $('#searchForm').on('submit', function(e) {
        // Add any custom search logic here
    });
    
    // Bulk tagging functionality
    $('#bulkTaggingForm').on('submit', function(e) {
        var transactionIds = $('#id_transaction_ids').val();
        if (!transactionIds.trim()) {
            e.preventDefault();
            alert('Please enter at least one transaction ID');
            return false;
        }
    });
    
    // Export functionality
    $('.export-btn').on('click', function(e) {
        e.preventDefault();
        var format = $(this).data('format');
        var url = $(this).data('url');
        
        if (url) {
            window.location.href = url + '?format=' + format;
        } else {
            alert('Export functionality will be implemented here');
        }
    });
    
    // Delete confirmation
    $('.delete-btn').on('click', function(e) {
        if (!confirm('Are you sure you want to delete this item?')) {
            e.preventDefault();
            return false;
        }
    });
    
    // Status change handler
    $('.status-change').on('change', function() {
        var status = $(this).val();
        var transactionId = $(this).data('transaction-id');
        
        // You can add AJAX call here to update status
        $.ajax({
            url: '/accounting/assign-transactions/api/update-status/',
            method: 'POST',
            data: {
                transaction_id: transactionId,
                status: status,
                csrfmiddlewaretoken: $('[name=csrfmiddlewaretoken]').val()
            },
            success: function(response) {
                if (response.success) {
                    showAlert('Status updated successfully', 'success');
                } else {
                    showAlert('Failed to update status', 'danger');
                }
            },
            error: function() {
                showAlert('Error updating status', 'danger');
            }
        });
    });
    
    // Auto-refresh functionality
    if ($('.auto-refresh').length) {
        setInterval(function() {
            location.reload();
        }, 300000); // Refresh every 5 minutes
    }
    
    // Chart initialization (if Chart.js is available)
    if (typeof Chart !== 'undefined') {
        initializeCharts();
    }
    
    // Real-time updates (if WebSocket is available)
    if (typeof WebSocket !== 'undefined') {
        initializeWebSocket();
    }
});

// Utility functions
function showAlert(message, type) {
    var alertHtml = '<div class="alert alert-' + type + ' alert-dismissible fade show" role="alert">' +
        message +
        '<button type="button" class="close" data-dismiss="alert"><span>&times;</span></button>' +
        '</div>';
    
    $('.alert-container').prepend(alertHtml);
    
    // Auto-dismiss after 5 seconds
    setTimeout(function() {
        $('.alert').fadeOut();
    }, 5000);
}

function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'AED'
    }).format(amount);
}

function formatDate(date) {
    return new Date(date).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

function validateTransactionForm() {
    var isValid = true;
    var errors = [];
    
    // Check required fields
    $('.required-field').each(function() {
        if (!$(this).val()) {
            isValid = false;
            errors.push($(this).attr('placeholder') + ' is required');
            $(this).addClass('is-invalid');
        } else {
            $(this).removeClass('is-invalid');
        }
    });
    
    // Check amount
    var amount = $('#id_amount').val();
    if (amount && parseFloat(amount) <= 0) {
        isValid = false;
        errors.push('Amount must be greater than zero');
        $('#id_amount').addClass('is-invalid');
    }
    
    // Check date
    var date = $('#id_transaction_date').val();
    if (date) {
        var selectedDate = new Date(date);
        var today = new Date();
        if (selectedDate > today) {
            isValid = false;
            errors.push('Transaction date cannot be in the future');
            $('#id_transaction_date').addClass('is-invalid');
        }
    }
    
    if (!isValid) {
        showAlert('Please fix the following errors:<br>' + errors.join('<br>'), 'danger');
    }
    
    return isValid;
}

function initializeCharts() {
    // Transaction type distribution chart
    var ctx = document.getElementById('transactionTypeChart');
    if (ctx) {
        new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Journal Entry', 'Purchase Invoice', 'Sales Invoice', 'Expense Claim', 'Payment', 'Receipt'],
                datasets: [{
                    data: [12, 19, 3, 5, 2, 3],
                    backgroundColor: [
                        '#4e73df',
                        '#1cc88a',
                        '#36b9cc',
                        '#f6c23e',
                        '#e74a3b',
                        '#6f42c1'
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
    
    // Cost center amount chart
    var ctx2 = document.getElementById('costCenterChart');
    if (ctx2) {
        new Chart(ctx2, {
            type: 'bar',
            data: {
                labels: ['CC001', 'CC002', 'CC003', 'CC004', 'CC005'],
                datasets: [{
                    label: 'Total Amount',
                    data: [12000, 19000, 3000, 5000, 2000],
                    backgroundColor: '#4e73df'
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

function initializeWebSocket() {
    // WebSocket implementation for real-time updates
    // This is a placeholder for future implementation
}

// AJAX functions
function getDefaultCostCenter(mappingType, entityId) {
    $.ajax({
        url: '/accounting/assign-transactions/api/get-default-cost-center/',
        method: 'POST',
        data: {
            mapping_type: mappingType,
            entity_id: entityId,
            csrfmiddlewaretoken: $('[name=csrfmiddlewaretoken]').val()
        },
        success: function(response) {
            if (response.success) {
                $('#id_cost_center').val(response.cost_center_id);
                showAlert('Default cost center loaded: ' + response.cost_center_name, 'info');
            }
        },
        error: function() {
            showAlert('Failed to load default cost center', 'warning');
        }
    });
}

function loadTransactionDetails(transactionId) {
    $.ajax({
        url: '/accounting/assign-transactions/api/transaction-details/' + transactionId + '/',
        method: 'GET',
        success: function(response) {
            $('#transactionDetailsModal .modal-body').html(response.html);
            $('#transactionDetailsModal').modal('show');
        },
        error: function() {
            showAlert('Failed to load transaction details', 'danger');
        }
    });
}

// Export functions
function exportToExcel() {
    var url = window.location.href;
    if (url.indexOf('?') > -1) {
        url += '&format=excel';
    } else {
        url += '?format=excel';
    }
    window.location.href = url;
}

function exportToPDF() {
    var url = window.location.href;
    if (url.indexOf('?') > -1) {
        url += '&format=pdf';
    } else {
        url += '?format=pdf';
    }
    window.location.href = url;
}

// Print functionality
function printReport() {
    window.print();
}

// Bulk operations
function selectAllTransactions() {
    $('.transaction-checkbox').prop('checked', $('#selectAll').prop('checked'));
}

function getSelectedTransactions() {
    var selected = [];
    $('.transaction-checkbox:checked').each(function() {
        selected.push($(this).val());
    });
    return selected;
}

function bulkUpdateStatus(status) {
    var selected = getSelectedTransactions();
    if (selected.length === 0) {
        showAlert('Please select at least one transaction', 'warning');
        return;
    }
    
    if (confirm('Are you sure you want to update ' + selected.length + ' transaction(s)?')) {
        $.ajax({
            url: '/accounting/assign-transactions/api/bulk-update-status/',
            method: 'POST',
            data: {
                transaction_ids: selected,
                status: status,
                csrfmiddlewaretoken: $('[name=csrfmiddlewaretoken]').val()
            },
            success: function(response) {
                if (response.success) {
                    showAlert('Successfully updated ' + response.updated_count + ' transaction(s)', 'success');
                    location.reload();
                } else {
                    showAlert('Failed to update transactions', 'danger');
                }
            },
            error: function() {
                showAlert('Error updating transactions', 'danger');
            }
        });
    }
}
