// Access Logs JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Auto-submit filters on change
    const filterSelects = document.querySelectorAll('#accessFilterForm select');
    filterSelects.forEach(select => {
        select.addEventListener('change', function() {
            document.getElementById('accessFilterForm').submit();
        });
    });

    // Date range validation
    const dateFrom = document.getElementById('date_from');
    const dateTo = document.getElementById('date_to');
    
    if (dateFrom && dateTo) {
        dateFrom.addEventListener('change', function() {
            if (dateTo.value && this.value > dateTo.value) {
                dateTo.value = this.value;
            }
        });
        
        dateTo.addEventListener('change', function() {
            if (dateFrom.value && this.value < dateFrom.value) {
                dateFrom.value = this.value;
            }
        });
    }

    // Debounced search
    let searchTimeout;
    const searchInput = document.getElementById('search');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                document.getElementById('accessFilterForm').submit();
            }, 500);
        });
    }

    // Keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + F to focus search
        if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
            e.preventDefault();
            const searchInput = document.getElementById('search');
            if (searchInput) {
                searchInput.focus();
                searchInput.select();
            }
        }
        
        // Escape to clear filters
        if (e.key === 'Escape') {
            clearFilters();
        }
    });
});

// Clear all filters
function clearFilters() {
    const form = document.getElementById('accessFilterForm');
    const inputs = form.querySelectorAll('input, select');
    
    inputs.forEach(input => {
        if (input.type === 'text' || input.type === 'date') {
            input.value = '';
        } else if (input.tagName === 'SELECT') {
            input.selectedIndex = 0;
        }
    });
    
    form.submit();
}

// Export access logs
function exportAccessLogs() {
    const form = document.getElementById('accessFilterForm');
    const formData = new FormData(form);
    const params = new URLSearchParams(formData);
    
    // Add export parameter
    params.append('export', 'csv');
    
    // Create download link
    const url = window.location.pathname + '?' + params.toString();
    const link = document.createElement('a');
    link.href = url;
    link.download = 'access_logs_' + new Date().toISOString().split('T')[0] + '.csv';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    // Show success message
    showNotification('Access logs exported successfully!', 'success');
}

// Clear old access logs
function clearOldAccessLogs() {
    if (confirm('Are you sure you want to clear access logs older than 90 days? This action cannot be undone.')) {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        
        fetch('/settings/roles-permissions/access-logs/clear-old/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken,
            },
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification(`Cleared ${data.cleared_count} old access logs`, 'success');
                // Reload the page to show updated data
                setTimeout(() => {
                    window.location.reload();
                }, 1500);
            } else {
                showNotification('Failed to clear old logs: ' + data.error, 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showNotification('An error occurred while clearing old logs', 'error');
        });
    }
}

// View access log details
function viewAccessLogDetails(logId) {
    const modal = new bootstrap.Modal(document.getElementById('accessLogDetailsModal'));
    const contentDiv = document.getElementById('accessLogDetailsContent');
    
    // Show loading state
    contentDiv.innerHTML = `
        <div class="text-center py-4">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <p class="mt-2">Loading log details...</p>
        </div>
    `;
    
    modal.show();
    
    // Fetch log details
    fetch(`/settings/roles-permissions/access-logs/${logId}/details/`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                contentDiv.innerHTML = `
                    <div class="alert alert-danger">
                        <i class="fas fa-exclamation-triangle"></i>
                        ${data.error}
                    </div>
                `;
            } else {
                contentDiv.innerHTML = formatAccessLogDetails(data);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            contentDiv.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-triangle"></i>
                    Failed to load log details. Please try again.
                </div>
            `;
        });
}

// Format access log details for display
function formatAccessLogDetails(data) {
    return `
        <div class="row">
            <div class="col-md-6">
                <h6 class="text-primary mb-3">Basic Information</h6>
                <table class="table table-sm">
                    <tr>
                        <td><strong>Timestamp:</strong></td>
                        <td>${data.timestamp}</td>
                    </tr>
                    <tr>
                        <td><strong>User:</strong></td>
                        <td>${data.user_name}</td>
                    </tr>
                    <tr>
                        <td><strong>Action:</strong></td>
                        <td>
                            <span class="badge bg-${getActionBadgeColor(data.action)}">
                                ${data.action}
                            </span>
                        </td>
                    </tr>
                    <tr>
                        <td><strong>Status:</strong></td>
                        <td>
                            <span class="badge bg-${data.status === 'success' ? 'success' : 'danger'}">
                                ${data.status}
                            </span>
                        </td>
                    </tr>
                </table>
            </div>
            <div class="col-md-6">
                <h6 class="text-primary mb-3">Technical Details</h6>
                <table class="table table-sm">
                    <tr>
                        <td><strong>IP Address:</strong></td>
                        <td><code>${data.ip_address}</code></td>
                    </tr>
                    <tr>
                        <td><strong>Resource:</strong></td>
                        <td><code>${data.resource}</code></td>
                    </tr>
                    <tr>
                        <td><strong>Session ID:</strong></td>
                        <td><code>${data.session_id}</code></td>
                    </tr>
                    <tr>
                        <td><strong>User Agent:</strong></td>
                        <td><small class="text-muted">${data.user_agent}</small></td>
                    </tr>
                </table>
            </div>
        </div>
        ${data.details ? `
        <div class="row mt-3">
            <div class="col-12">
                <h6 class="text-primary mb-3">Additional Details</h6>
                <div class="bg-light p-3 rounded">
                    <pre class="mb-0"><code>${JSON.stringify(data.details, null, 2)}</code></pre>
                </div>
            </div>
        </div>
        ` : ''}
        ${data.error_message ? `
        <div class="row mt-3">
            <div class="col-12">
                <h6 class="text-danger mb-3">Error Message</h6>
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-triangle"></i>
                    ${data.error_message}
                </div>
            </div>
        </div>
        ` : ''}
    `;
}

// Get badge color for action
function getActionBadgeColor(action) {
    switch (action) {
        case 'login':
            return 'success';
        case 'logout':
            return 'secondary';
        case 'access_denied':
            return 'danger';
        case 'password_change':
        case 'password_reset':
            return 'warning';
        default:
            return 'info';
    }
}

// Set page size
function setPageSize(size) {
    const url = new URL(window.location);
    url.searchParams.set('page_size', size);
    url.searchParams.delete('page'); // Reset to first page
    window.location.href = url.toString();
}

// Show notification
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // Add to page
    document.body.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 5000);
}

// Refresh data periodically (every 30 seconds)
setInterval(() => {
    // Only refresh if user is not actively interacting
    if (!document.hasFocus()) {
        const currentUrl = window.location.href;
        if (!currentUrl.includes('page=') && !currentUrl.includes('search=')) {
            // Reload only if not on a specific page or search
            window.location.reload();
        }
    }
}, 30000);

// Add loading state to buttons
document.addEventListener('click', function(e) {
    if (e.target.matches('button[onclick*="exportAccessLogs"], button[onclick*="clearOldAccessLogs"]')) {
        const button = e.target;
        const originalText = button.innerHTML;
        
        button.disabled = true;
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
        
        // Reset button after 3 seconds (in case of errors)
        setTimeout(() => {
            button.disabled = false;
            button.innerHTML = originalText;
        }, 3000);
    }
});

// Enhanced table functionality
document.addEventListener('DOMContentLoaded', function() {
    const table = document.getElementById('accessLogsTable');
    if (table) {
        // Add row highlighting on hover
        const rows = table.querySelectorAll('tbody tr');
        rows.forEach(row => {
            row.addEventListener('mouseenter', function() {
                this.style.backgroundColor = '#f8f9fc';
            });
            
            row.addEventListener('mouseleave', function() {
                this.style.backgroundColor = '';
            });
        });
        
        // Add click to select row
        rows.forEach(row => {
            row.addEventListener('click', function() {
                // Remove selection from other rows
                rows.forEach(r => r.classList.remove('table-active'));
                // Add selection to current row
                this.classList.add('table-active');
            });
        });
    }
});

// Form validation
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('accessFilterForm');
    if (form) {
        form.addEventListener('submit', function(e) {
            const dateFrom = document.getElementById('date_from');
            const dateTo = document.getElementById('date_to');
            
            if (dateFrom.value && dateTo.value && dateFrom.value > dateTo.value) {
                e.preventDefault();
                showNotification('Start date cannot be after end date', 'error');
                return false;
            }
        });
    }
});

// Responsive table handling
function handleResponsiveTable() {
    const table = document.getElementById('accessLogsTable');
    if (table && window.innerWidth < 768) {
        // On mobile, make table scrollable horizontally
        table.parentElement.style.overflowX = 'auto';
        
        // Add mobile-specific classes
        table.classList.add('table-sm');
    }
}

// Call on load and resize
window.addEventListener('load', handleResponsiveTable);
window.addEventListener('resize', handleResponsiveTable);
