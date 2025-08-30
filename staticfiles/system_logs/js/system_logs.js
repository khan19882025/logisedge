/**
 * System Logs JavaScript - Comprehensive functionality for error and debug logging
 */

// Global variables
let currentFilters = {};
let refreshInterval = null;
let autoRefreshEnabled = false;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeSystemLogs();
    setupEventListeners();
    loadInitialData();
});

/**
 * Initialize the system logs application
 */
function initializeSystemLogs() {
    console.log('Initializing System Logs application...');
    
    // Initialize tooltips
    initializeTooltips();
    
    // Initialize charts if they exist
    if (typeof Chart !== 'undefined') {
        initializeCharts();
    }
    
    // Setup auto-refresh if enabled
    setupAutoRefresh();
    
    // Initialize real-time updates
    initializeRealTimeUpdates();
}

/**
 * Setup event listeners for interactive elements
 */
function setupEventListeners() {
    // Filter form submission
    const filterForm = document.getElementById('filter-form');
    if (filterForm) {
        filterForm.addEventListener('submit', handleFilterSubmit);
    }
    
    // Bulk action form
    const bulkActionForm = document.getElementById('bulk-action-form');
    if (bulkActionForm) {
        bulkActionForm.addEventListener('submit', handleBulkAction);
    }
    
    // Select all checkboxes
    const selectAllCheckbox = document.getElementById('select-all-checkbox');
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', handleSelectAll);
    }
    
    // Individual log checkboxes
    const logCheckboxes = document.querySelectorAll('.log-checkbox');
    logCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', handleIndividualCheckbox);
    });
    
    // Quick action buttons
    setupQuickActionButtons();
    
    // Search input debouncing
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        searchInput.addEventListener('input', debounce(handleSearchInput, 300));
    }
    
    // Date range picker
    setupDateRangePicker();
    
    // Export buttons
    setupExportButtons();
}

/**
 * Initialize tooltips using Bootstrap
 */
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Initialize charts if Chart.js is available
 */
function initializeCharts() {
    // This would be implemented based on specific chart requirements
    console.log('Charts initialized');
}

/**
 * Setup auto-refresh functionality
 */
function setupAutoRefresh() {
    const autoRefreshToggle = document.getElementById('auto-refresh-toggle');
    if (autoRefreshToggle) {
        autoRefreshToggle.addEventListener('change', function() {
            autoRefreshEnabled = this.checked;
            if (autoRefreshEnabled) {
                startAutoRefresh();
            } else {
                stopAutoRefresh();
            }
        });
    }
}

/**
 * Start auto-refresh interval
 */
function startAutoRefresh() {
    if (refreshInterval) {
        clearInterval(refreshInterval);
    }
    
    refreshInterval = setInterval(() => {
        refreshData();
    }, 30000); // Refresh every 30 seconds
    
    console.log('Auto-refresh started');
}

/**
 * Stop auto-refresh interval
 */
function stopAutoRefresh() {
    if (refreshInterval) {
        clearInterval(refreshInterval);
        refreshInterval = null;
    }
    
    console.log('Auto-refresh stopped');
}

/**
 * Initialize real-time updates
 */
function initializeRealTimeUpdates() {
    // This could use WebSockets or Server-Sent Events for real-time updates
    console.log('Real-time updates initialized');
}

/**
 * Load initial data
 */
function loadInitialData() {
    // Load any initial data needed for the page
    console.log('Loading initial data...');
}

/**
 * Handle filter form submission
 */
function handleFilterSubmit(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const filters = {};
    
    for (let [key, value] of formData.entries()) {
        if (value) {
            filters[key] = value;
        }
    }
    
    currentFilters = filters;
    applyFilters(filters);
}

/**
 * Apply filters to the current view
 */
function applyFilters(filters) {
    // Build query string
    const queryString = new URLSearchParams(filters).toString();
    const currentUrl = new URL(window.location);
    
    // Update URL with filters
    currentUrl.search = queryString;
    window.history.pushState({}, '', currentUrl);
    
    // Reload data with filters
    refreshData();
}

/**
 * Handle bulk action form submission
 */
function handleBulkAction(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const action = formData.get('action');
    const selectedLogs = formData.get('selected_logs');
    
    if (!action || !selectedLogs) {
        showNotification('Please select an action and at least one log entry.', 'warning');
        return;
    }
    
    // Confirm action
    if (!confirm(`Are you sure you want to ${action} the selected logs?`)) {
        return;
    }
    
    // Submit bulk action
    submitBulkAction(action, selectedLogs);
}

/**
 * Submit bulk action to server
 */
function submitBulkAction(action, selectedLogs) {
    const formData = new FormData();
    formData.append('action', action);
    formData.append('selected_logs', selectedLogs);
    
    // Add additional form data
    const form = document.getElementById('bulk-action-form');
    const additionalData = new FormData(form);
    for (let [key, value] of additionalData.entries()) {
        if (key !== 'action' && key !== 'selected_logs') {
            formData.append(key, value);
        }
    }
    
    fetch('/utilities/system-logs/bulk-action/', {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': getCSRFToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification(data.message, 'success');
            refreshData();
        } else {
            showNotification(data.message || 'Bulk action failed.', 'error');
        }
    })
    .catch(error => {
        console.error('Bulk action error:', error);
        showNotification('An error occurred while processing the bulk action.', 'error');
    });
}

/**
 * Handle select all checkbox
 */
function handleSelectAll(event) {
    const isChecked = event.target.checked;
    const logCheckboxes = document.querySelectorAll('.log-checkbox');
    
    logCheckboxes.forEach(checkbox => {
        checkbox.checked = isChecked;
    });
    
    updateBulkActionButton();
}

/**
 * Handle individual checkbox selection
 */
function handleIndividualCheckbox() {
    updateBulkActionButton();
    updateSelectAllCheckbox();
}

/**
 * Update bulk action button state
 */
function updateBulkActionButton() {
    const checkedBoxes = document.querySelectorAll('.log-checkbox:checked');
    const bulkActionBtn = document.getElementById('bulk-action-btn');
    const selectedLogsInput = document.getElementById('selected-logs');
    
    if (bulkActionBtn && selectedLogsInput) {
        if (checkedBoxes.length > 0) {
            bulkActionBtn.disabled = false;
            const selectedIds = Array.from(checkedBoxes).map(cb => cb.value);
            selectedLogsInput.value = JSON.stringify(selectedIds);
        } else {
            bulkActionBtn.disabled = true;
            selectedLogsInput.value = '';
        }
    }
}

/**
 * Update select all checkbox state
 */
function updateSelectAllCheckbox() {
    const selectAllCheckbox = document.getElementById('select-all-checkbox');
    const logCheckboxes = document.querySelectorAll('.log-checkbox');
    const checkedBoxes = document.querySelectorAll('.log-checkbox:checked');
    
    if (selectAllCheckbox) {
        if (checkedBoxes.length === 0) {
            selectAllCheckbox.indeterminate = false;
            selectAllCheckbox.checked = false;
        } else if (checkedBoxes.length === logCheckboxes.length) {
            selectAllCheckbox.indeterminate = false;
            selectAllCheckbox.checked = true;
        } else {
            selectAllCheckbox.indeterminate = true;
            selectAllCheckbox.checked = false;
        }
    }
}

/**
 * Setup quick action buttons
 */
function setupQuickActionButtons() {
    // Resolve button
    const resolveButtons = document.querySelectorAll('.btn-resolve');
    resolveButtons.forEach(button => {
        button.addEventListener('click', function() {
            const logId = this.dataset.logId;
            resolveLog(logId);
        });
    });
    
    // Escalate button
    const escalateButtons = document.querySelectorAll('.btn-escalate');
    escalateButtons.forEach(button => {
        button.addEventListener('click', function() {
            const logId = this.dataset.logId;
            escalateLog(logId);
        });
    });
    
    // Archive button
    const archiveButtons = document.querySelectorAll('.btn-archive');
    archiveButtons.forEach(button => {
        button.addEventListener('click', function() {
            const logId = this.dataset.logId;
            archiveLog(logId);
        });
    });
}

/**
 * Resolve a log entry
 */
function resolveLog(logId) {
    if (!confirm('Mark this log as resolved?')) {
        return;
    }
    
    const formData = new FormData();
    formData.append('action', 'resolve');
    formData.append('selected_logs', JSON.stringify([logId]));
    
    fetch('/utilities/system-logs/bulk-action/', {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': getCSRFToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Log marked as resolved.', 'success');
            refreshData();
        } else {
            showNotification(data.message || 'Failed to resolve log.', 'error');
        }
    })
    .catch(error => {
        console.error('Resolve error:', error);
        showNotification('An error occurred while resolving the log.', 'error');
    });
}

/**
 * Escalate a log entry
 */
function escalateLog(logId) {
    const level = prompt('Enter escalation level (1-5):', '1');
    if (!level || isNaN(level) || level < 1 || level > 5) {
        showNotification('Please enter a valid escalation level (1-5).', 'warning');
        return;
    }
    
    const formData = new FormData();
    formData.append('action', 'escalate');
    formData.append('selected_logs', JSON.stringify([logId]));
    formData.append('escalation_level', level);
    
    fetch('/utilities/system-logs/bulk-action/', {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': getCSRFToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification(`Log escalated to level ${level}.`, 'success');
            refreshData();
        } else {
            showNotification(data.message || 'Failed to escalate log.', 'error');
        }
    })
    .catch(error => {
        console.error('Escalate error:', error);
        showNotification('An error occurred while escalating the log.', 'error');
    });
}

/**
 * Archive a log entry
 */
function archiveLog(logId) {
    if (!confirm('Archive this log entry?')) {
        return;
    }
    
    const formData = new FormData();
    formData.append('action', 'archive');
    formData.append('selected_logs', JSON.stringify([logId]));
    
    fetch('/utilities/system-logs/bulk-action/', {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': getCSRFToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Log archived successfully.', 'success');
            refreshData();
        } else {
            showNotification(data.message || 'Failed to archive log.', 'error');
        }
    })
    .catch(error => {
        console.error('Archive error:', error);
        showNotification('An error occurred while archiving the log.', 'error');
    });
}

/**
 * Setup date range picker
 */
function setupDateRangePicker() {
    const dateFromInput = document.getElementById('date_from');
    const dateToInput = document.getElementById('date_to');
    
    if (dateFromInput && dateToInput) {
        // Set default date range (last 30 days)
        const today = new Date();
        const thirtyDaysAgo = new Date(today.getTime() - (30 * 24 * 60 * 60 * 1000));
        
        dateFromInput.value = thirtyDaysAgo.toISOString().split('T')[0];
        dateToInput.value = today.toISOString().split('T')[0];
        
        // Add change event listeners
        dateFromInput.addEventListener('change', handleDateChange);
        dateToInput.addEventListener('change', handleDateChange);
    }
}

/**
 * Handle date range changes
 */
function handleDateChange() {
    const dateFrom = document.getElementById('date_from').value;
    const dateTo = document.getElementById('date_to').value;
    
    if (dateFrom && dateTo) {
        if (dateFrom > dateTo) {
            showNotification('Start date cannot be after end date.', 'warning');
            return;
        }
        
        // Apply date filter
        currentFilters.date_from = dateFrom;
        currentFilters.date_to = dateTo;
        applyFilters(currentFilters);
    }
}

/**
 * Setup export buttons
 */
function setupExportButtons() {
    const exportButtons = document.querySelectorAll('.btn-export');
    exportButtons.forEach(button => {
        button.addEventListener('click', function() {
            const format = this.dataset.format;
            const logIds = this.dataset.logIds;
            exportLogs(format, logIds);
        });
    });
}

/**
 * Export logs in specified format
 */
function exportLogs(format, logIds = null) {
    const formData = new FormData();
    formData.append('export_format', format);
    formData.append('include_headers', 'true');
    formData.append('include_metadata', 'true');
    formData.append('max_records', '10000');
    formData.append('filename_prefix', 'system_logs_export');
    
    if (logIds) {
        formData.append('selected_ids', logIds);
    }
    
    // Add current filters
    Object.keys(currentFilters).forEach(key => {
        formData.append(key, currentFilters[key]);
    });
    
    // Create temporary form and submit
    const tempForm = document.createElement('form');
    tempForm.method = 'POST';
    tempForm.action = '/utilities/system-logs/export/';
    tempForm.style.display = 'none';
    
    // Add CSRF token
    const csrfInput = document.createElement('input');
    csrfInput.type = 'hidden';
    csrfInput.name = 'csrfmiddlewaretoken';
    csrfInput.value = getCSRFToken();
    tempForm.appendChild(csrfInput);
    
    // Add form data
    for (let [key, value] of formData.entries()) {
        const input = document.createElement('input');
        input.type = 'hidden';
        input.name = key;
        input.value = value;
        tempForm.appendChild(input);
    }
    
    document.body.appendChild(tempForm);
    tempForm.submit();
    document.body.removeChild(tempForm);
}

/**
 * Handle search input with debouncing
 */
function handleSearchInput(event) {
    const searchTerm = event.target.value.trim();
    
    if (searchTerm.length >= 2 || searchTerm.length === 0) {
        currentFilters.search = searchTerm;
        applyFilters(currentFilters);
    }
}

/**
 * Setup search functionality
 */
function setupSearch() {
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        searchInput.addEventListener('input', debounce(handleSearchInput, 300));
    }
}

/**
 * Refresh data based on current filters
 */
function refreshData() {
    // Show loading indicator
    showLoadingIndicator();
    
    // Reload the page with current filters
    const queryString = new URLSearchParams(currentFilters).toString();
    const currentUrl = new URL(window.location);
    currentUrl.search = queryString;
    
    window.location.href = currentUrl.toString();
}

/**
 * Show loading indicator
 */
function showLoadingIndicator() {
    const loadingDiv = document.createElement('div');
    loadingDiv.id = 'loading-indicator';
    loadingDiv.className = 'loading-overlay';
    loadingDiv.innerHTML = `
        <div class="spinner-border text-primary" role="status">
            <span class="visually-hidden">Loading...</span>
        </div>
        <p class="mt-2 text-primary">Refreshing data...</p>
    `;
    
    document.body.appendChild(loadingDiv);
}

/**
 * Hide loading indicator
 */
function hideLoadingIndicator() {
    const loadingDiv = document.getElementById('loading-indicator');
    if (loadingDiv) {
        loadingDiv.remove();
    }
}

/**
 * Show notification message
 */
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

/**
 * Get CSRF token from cookies
 */
function getCSRFToken() {
    const name = 'csrftoken';
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

/**
 * Debounce function for search input
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
 * Format date for display
 */
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}

/**
 * Format file size
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * Copy text to clipboard
 */
function copyToClipboard(text) {
    if (navigator.clipboard) {
        navigator.clipboard.writeText(text).then(() => {
            showNotification('Text copied to clipboard!', 'success');
        }).catch(() => {
            fallbackCopyTextToClipboard(text);
        });
    } else {
        fallbackCopyTextToClipboard(text);
    }
}

/**
 * Fallback copy text to clipboard
 */
function fallbackCopyTextToClipboard(text) {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.left = '-999999px';
    textArea.style.top = '-999999px';
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    
    try {
        document.execCommand('copy');
        showNotification('Text copied to clipboard!', 'success');
    } catch (err) {
        showNotification('Failed to copy text to clipboard.', 'error');
    }
    
    document.body.removeChild(textArea);
}

/**
 * Export page data
 */
window.exportPageData = function() {
    const pageData = {
        url: window.location.href,
        title: document.title,
        timestamp: new Date().toISOString(),
        filters: currentFilters
    };
    
    const dataStr = JSON.stringify(pageData, null, 2);
    const dataBlob = new Blob([dataStr], {type: 'application/json'});
    
    const link = document.createElement('a');
    link.href = URL.createObjectURL(dataBlob);
    link.download = 'system_logs_page_data.json';
    link.click();
};

/**
 * Print current page
 */
window.printPage = function() {
    window.print();
};

// Export functions for global use
window.SystemLogs = {
    resolveLog,
    escalateLog,
    archiveLog,
    exportLogs,
    showNotification,
    copyToClipboard,
    formatDate,
    formatFileSize
};
