// Audit Logs JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Auto-submit form on filter changes
    const autoSubmitFilters = ['log_type', 'user', 'status'];
    autoSubmitFilters.forEach(filterId => {
        const element = document.getElementById(filterId);
        if (element) {
            element.addEventListener('change', function() {
                document.getElementById('auditFilterForm').submit();
            });
        }
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

    // Search with debounce
    const searchInput = document.getElementById('search');
    if (searchInput) {
        let searchTimeout;
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                document.getElementById('auditFilterForm').submit();
            }, 500);
        });
    }
});

// Clear all filters
function clearFilters() {
    const form = document.getElementById('auditFilterForm');
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

// Export audit logs
function exportAuditLogs() {
    const form = document.getElementById('auditFilterForm');
    const exportForm = document.createElement('form');
    exportForm.method = 'POST';
    exportForm.action = window.location.pathname;
    
    // Add CSRF token
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    const csrfInput = document.createElement('input');
    csrfInput.type = 'hidden';
    csrfInput.name = 'csrfmiddlewaretoken';
    csrfInput.value = csrfToken;
    exportForm.appendChild(csrfInput);
    
    // Add export action
    const actionInput = document.createElement('input');
    actionInput.type = 'hidden';
    actionInput.name = 'action';
    actionInput.value = 'export';
    exportForm.appendChild(actionInput);
    
    // Copy current filters
    const formData = new FormData(form);
    for (let [key, value] of formData.entries()) {
        if (value) {
            const input = document.createElement('input');
            input.type = 'hidden';
            input.name = key;
            input.value = value;
            exportForm.appendChild(input);
        }
    }
    
    document.body.appendChild(exportForm);
    exportForm.submit();
    document.body.removeChild(exportForm);
}

// Clear old logs
function clearOldLogs() {
    if (confirm('Are you sure you want to clear logs older than 90 days? This action cannot be undone.')) {
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = window.location.pathname;
        
        // Add CSRF token
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        const csrfInput = document.createElement('input');
        csrfInput.type = 'hidden';
        csrfInput.name = 'csrfmiddlewaretoken';
        csrfInput.value = csrfToken;
        form.appendChild(csrfInput);
        
        // Add clear action
        const actionInput = document.createElement('input');
        actionInput.type = 'hidden';
        actionInput.name = 'action';
        actionInput.value = 'clear_old';
        form.appendChild(actionInput);
        
        document.body.appendChild(form);
        form.submit();
        document.body.removeChild(form);
    }
}

// View log details
function viewLogDetails(logId) {
    const modal = new bootstrap.Modal(document.getElementById('logDetailsModal'));
    const contentDiv = document.getElementById('logDetailsContent');
    
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
    fetch(`/settings/roles-permissions/audit-logs/${logId}/details/`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            contentDiv.innerHTML = formatLogDetails(data);
        })
        .catch(error => {
            console.error('Error:', error);
            contentDiv.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-triangle"></i>
                    Error loading log details. Please try again.
                </div>
            `;
        });
}

// Format log details for display
function formatLogDetails(data) {
    let html = `
        <div class="row">
            <div class="col-md-6">
                <h6 class="text-primary">Basic Information</h6>
                <table class="table table-sm">
                    <tr>
                        <td><strong>Timestamp:</strong></td>
                        <td>${data.timestamp}</td>
                    </tr>
                    <tr>
                        <td><strong>User:</strong></td>
                        <td>${data.user_name || 'Anonymous'}</td>
                    </tr>
                    <tr>
                        <td><strong>Action:</strong></td>
                        <td><span class="badge bg-${getActionBadgeColor(data.action)}">${data.action}</span></td>
                    </tr>
                    <tr>
                        <td><strong>Status:</strong></td>
                        <td><span class="badge bg-${data.status === 'success' ? 'success' : 'danger'}">${data.status}</span></td>
                    </tr>
                </table>
            </div>
            <div class="col-md-6">
                <h6 class="text-primary">Technical Details</h6>
                <table class="table table-sm">
                    <tr>
                        <td><strong>IP Address:</strong></td>
                        <td><code>${data.ip_address || 'N/A'}</code></td>
                    </tr>
                    <tr>
                        <td><strong>User Agent:</strong></td>
                        <td><small>${data.user_agent || 'N/A'}</small></td>
                    </tr>
                    <tr>
                        <td><strong>Resource:</strong></td>
                        <td><code>${data.resource || 'N/A'}</code></td>
                    </tr>
                    <tr>
                        <td><strong>Session ID:</strong></td>
                        <td><code>${data.session_id || 'N/A'}</code></td>
                    </tr>
                </table>
            </div>
        </div>
    `;
    
    if (data.details) {
        html += `
            <div class="row mt-3">
                <div class="col-12">
                    <h6 class="text-primary">Additional Details</h6>
                    <pre class="bg-light p-3 rounded"><code>${JSON.stringify(data.details, null, 2)}</code></pre>
                </div>
            </div>
        `;
    }
    
    if (data.error_message) {
        html += `
            <div class="row mt-3">
                <div class="col-12">
                    <h6 class="text-danger">Error Message</h6>
                    <div class="alert alert-danger">
                        <i class="fas fa-exclamation-triangle"></i>
                        ${data.error_message}
                    </div>
                </div>
            </div>
        `;
    }
    
    return html;
}

// Get badge color for action
function getActionBadgeColor(action) {
    const colors = {
        'login': 'success',
        'logout': 'secondary',
        'access_denied': 'danger',
        'permission_check': 'info',
        'role_assigned': 'warning',
        'role_removed': 'danger',
        'permission_granted': 'success',
        'permission_revoked': 'danger'
    };
    return colors[action] || 'info';
}

// Set page size
function setPageSize(size) {
    const url = new URL(window.location);
    url.searchParams.set('page_size', size);
    url.searchParams.delete('page'); // Reset to first page
    window.location.href = url.toString();
}

// Real-time updates (if enabled)
function enableRealTimeUpdates() {
    // Check for new logs every 30 seconds
    setInterval(() => {
        fetch('/settings/roles-permissions/audit-logs/check-updates/')
            .then(response => response.json())
            .then(data => {
                if (data.has_new_logs) {
                    // Show notification
                    showNotification('New audit logs available', 'info');
                    // Optionally refresh the page
                    // window.location.reload();
                }
            })
            .catch(error => console.error('Error checking for updates:', error));
    }, 30000);
}

// Show notification
function showNotification(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;
    
    const toastContainer = document.getElementById('toastContainer') || createToastContainer();
    toastContainer.appendChild(toast);
    
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    // Remove toast after it's hidden
    toast.addEventListener('hidden.bs.toast', () => {
        toast.remove();
    });
}

// Create toast container if it doesn't exist
function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toastContainer';
    container.className = 'toast-container position-fixed top-0 end-0 p-3';
    container.style.zIndex = '1055';
    document.body.appendChild(container);
    return container;
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
    
    // Ctrl/Cmd + E to export
    if ((e.ctrlKey || e.metaKey) && e.key === 'e') {
        e.preventDefault();
        exportAuditLogs();
    }
    
    // Escape to clear filters
    if (e.key === 'Escape') {
        const activeElement = document.activeElement;
        if (activeElement && (activeElement.tagName === 'INPUT' || activeElement.tagName === 'SELECT')) {
            activeElement.blur();
        }
    }
});

// Initialize real-time updates if user has permission
if (document.body.dataset.enableRealTime === 'true') {
    enableRealTimeUpdates();
}
