// Container Management JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all components
    initializeContainerSearch();
    initializeStatusUpdates();
    initializeFormValidation();
    initializeNotifications();
    initializeCharts();
    initializeBulkUpload();
    initializeRealTimeUpdates();
});

// Container Search Functionality
function initializeContainerSearch() {
    const searchInput = document.getElementById('container-search');
    const searchResults = document.getElementById('search-results');
    
    if (searchInput) {
        let searchTimeout;
        
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            const query = this.value.trim();
            
            if (query.length >= 3) {
                searchTimeout = setTimeout(() => {
                    performContainerSearch(query);
                }, 300);
            } else {
                hideSearchResults();
            }
        });
        
        // Hide results when clicking outside
        document.addEventListener('click', function(e) {
            if (!searchInput.contains(e.target) && !searchResults.contains(e.target)) {
                hideSearchResults();
            }
        });
    }
}

function performContainerSearch(query) {
    const searchResults = document.getElementById('search-results');
    
    fetch(`/container-management/ajax/container-search/?q=${encodeURIComponent(query)}`)
        .then(response => response.json())
        .then(data => {
            displaySearchResults(data.results);
        })
        .catch(error => {
            console.error('Search error:', error);
        });
}

function displaySearchResults(results) {
    const searchResults = document.getElementById('search-results');
    
    if (results.length === 0) {
        searchResults.innerHTML = '<div class="p-3 text-muted">No containers found</div>';
    } else {
        const html = results.map(container => `
            <div class="search-result-item p-2 border-bottom" onclick="selectContainer(${JSON.stringify(container.id)}, ${JSON.stringify(container.container_number)})">
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <strong>${container.container_number}</strong>
                        <br>
                        <small class="text-muted">${container.container_type}</small>
                    </div>
                    <span class="badge bg-${getStatusColor(container.status)}">${container.status}</span>
                </div>
            </div>
        `).join('');
        
        searchResults.innerHTML = html;
    }
    
    searchResults.style.display = 'block';
}

function hideSearchResults() {
    const searchResults = document.getElementById('search-results');
    if (searchResults) {
        searchResults.style.display = 'none';
    }
}

function selectContainer(containerId, containerNumber) {
    const searchInput = document.getElementById('container-search');
    if (searchInput) {
        searchInput.value = containerNumber;
        searchInput.setAttribute('data-container-id', containerId);
    }
    hideSearchResults();
}

// Status Update Functionality
function initializeStatusUpdates() {
    const statusUpdateForms = document.querySelectorAll('.status-update-form');
    
    statusUpdateForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            updateContainerStatus(this);
        });
    });
}

function updateContainerStatus(form) {
    const formData = new FormData(form);
    const containerId = form.getAttribute('data-container-id');
    
    // Show loading state
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML = '<i class="bi bi-hourglass-split"></i> Updating...';
    submitBtn.disabled = true;
    
    fetch(`/container-management/ajax/container/${containerId}/status-update/`, {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': getCSRFToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Status updated successfully!', 'success');
            // Refresh the page or update the UI
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        } else {
            showNotification('Failed to update status: ' + data.message, 'error');
        }
    })
    .catch(error => {
        console.error('Status update error:', error);
        showNotification('An error occurred while updating status', 'error');
    })
    .finally(() => {
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
    });
}

// Form Validation
function initializeFormValidation() {
    const forms = document.querySelectorAll('.needs-validation');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!form.checkValidity()) {
                e.preventDefault();
                e.stopPropagation();
            }
            form.classList.add('was-validated');
        });
        
        // Real-time validation
        const inputs = form.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            input.addEventListener('blur', function() {
                validateField(this);
            });
        });
    });
}

function validateField(field) {
    const value = field.value.trim();
    const fieldName = field.name;
    let isValid = true;
    let errorMessage = '';
    
    // Container number validation
    if (fieldName === 'container_number') {
        if (value.length !== 11) {
            isValid = false;
            errorMessage = 'Container number must be exactly 11 characters';
        }
    }
    
    // Date validation
    if (fieldName.includes('date') || fieldName.includes('Date')) {
        if (value && new Date(value) < new Date()) {
            if (fieldName.includes('pickup')) {
                isValid = false;
                errorMessage = 'Pickup date cannot be in the past';
            }
        }
    }
    
    // Weight and volume validation
    if (fieldName === 'weight' || fieldName === 'volume' || fieldName === 'tare_weight' || fieldName === 'max_payload') {
        if (value && parseFloat(value) <= 0) {
            isValid = false;
            errorMessage = 'Value must be greater than 0';
        }
    }
    
    // Display validation result
    const feedback = field.parentNode.querySelector('.invalid-feedback');
    if (feedback) {
        if (!isValid) {
            feedback.textContent = errorMessage;
            field.classList.add('is-invalid');
        } else {
            field.classList.remove('is-invalid');
            field.classList.add('is-valid');
        }
    }
    
    return isValid;
}

// Notification System
function initializeNotifications() {
    // Check for unread notifications
    checkUnreadNotifications();
    
    // Mark notifications as read
    const notificationItems = document.querySelectorAll('.notification-item');
    notificationItems.forEach(item => {
        item.addEventListener('click', function() {
            markNotificationAsRead(this.getAttribute('data-notification-id'));
        });
    });
}

function checkUnreadNotifications() {
    fetch('/container-management/notifications/unread-count/')
        .then(response => response.json())
        .then(data => {
            updateNotificationBadge(data.count);
        })
        .catch(error => {
            console.error('Error checking notifications:', error);
        });
}

function updateNotificationBadge(count) {
    const badge = document.getElementById('notification-badge');
    if (badge) {
        if (count > 0) {
            badge.textContent = count;
            badge.style.display = 'inline';
        } else {
            badge.style.display = 'none';
        }
    }
}

function markNotificationAsRead(notificationId) {
    fetch(`/container-management/notifications/${notificationId}/mark-read/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCSRFToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const notificationItem = document.querySelector(`[data-notification-id="${notificationId}"]`);
            if (notificationItem) {
                notificationItem.classList.remove('unread');
            }
        }
    })
    .catch(error => {
        console.error('Error marking notification as read:', error);
    });
}

// Charts and Visualizations
function initializeCharts() {
    // Container type distribution chart
    const containerTypeChart = document.getElementById('container-type-chart');
    if (containerTypeChart) {
        createContainerTypeChart();
    }
    
    // Port inventory chart
    const portInventoryChart = document.getElementById('port-inventory-chart');
    if (portInventoryChart) {
        createPortInventoryChart();
    }
}

function createContainerTypeChart() {
    // This would use Chart.js or similar library
    // For now, we'll use CSS-based progress bars
    const progressBars = document.querySelectorAll('.container-type-progress');
    progressBars.forEach(bar => {
        const percentage = bar.getAttribute('data-percentage');
        bar.style.width = percentage + '%';
    });
}

function createPortInventoryChart() {
    // Similar implementation for port inventory visualization
}

// Bulk Upload Functionality
function initializeBulkUpload() {
    const bulkUploadForm = document.getElementById('bulk-upload-form');
    const fileInput = document.getElementById('bulk-upload-file');
    
    if (bulkUploadForm && fileInput) {
        fileInput.addEventListener('change', function() {
            validateBulkUploadFile(this);
        });
        
        bulkUploadForm.addEventListener('submit', function(e) {
            e.preventDefault();
            handleBulkUpload(this);
        });
    }
}

function validateBulkUploadFile(fileInput) {
    const file = fileInput.files[0];
    const allowedTypes = ['.xlsx', '.xls', '.csv'];
    const maxSize = 5 * 1024 * 1024; // 5MB
    
    if (file) {
        const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
        
        if (!allowedTypes.includes(fileExtension)) {
            showNotification('Please select a valid Excel or CSV file', 'error');
            fileInput.value = '';
            return false;
        }
        
        if (file.size > maxSize) {
            showNotification('File size must be less than 5MB', 'error');
            fileInput.value = '';
            return false;
        }
        
        return true;
    }
    
    return false;
}

function handleBulkUpload(form) {
    const formData = new FormData(form);
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    
    submitBtn.innerHTML = '<i class="bi bi-hourglass-split"></i> Uploading...';
    submitBtn.disabled = true;
    
    fetch('/container-management/bulk-upload/', {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': getCSRFToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification(`Successfully uploaded ${data.count} containers`, 'success');
            setTimeout(() => {
                window.location.href = '/container-management/containers/';
            }, 2000);
        } else {
            showNotification('Upload failed: ' + data.message, 'error');
        }
    })
    .catch(error => {
        console.error('Bulk upload error:', error);
        showNotification('An error occurred during upload', 'error');
    })
    .finally(() => {
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
    });
}

// Real-time Updates
function initializeRealTimeUpdates() {
    // Set up WebSocket or polling for real-time updates
    setInterval(checkForUpdates, 30000); // Check every 30 seconds
}

function checkForUpdates() {
    fetch('/container-management/ajax/updates/')
        .then(response => response.json())
        .then(data => {
            if (data.has_updates) {
                updateDashboard(data.updates);
            }
        })
        .catch(error => {
            console.error('Error checking for updates:', error);
        });
}

function updateDashboard(updates) {
    // Update dashboard statistics and recent activities
    if (updates.statistics) {
        updateStatistics(updates.statistics);
    }
    
    if (updates.recent_activities) {
        updateRecentActivities(updates.recent_activities);
    }
}

// Utility Functions
function getCSRFToken() {
    const token = document.querySelector('meta[name="csrf-token"]');
    return token ? token.getAttribute('content') : '';
}

function getStatusColor(status) {
    const colors = {
        'available': 'success',
        'booked': 'info',
        'in_use': 'primary',
        'maintenance': 'warning',
        'retired': 'secondary'
    };
    return colors[status] || 'secondary';
}

function showNotification(message, type = 'info') {
    const alertClass = type === 'success' ? 'alert-success' : 
                      type === 'error' ? 'alert-danger' : 
                      type === 'warning' ? 'alert-warning' : 'alert-info';
    
    const notification = document.createElement('div');
    notification.className = `alert ${alertClass} alert-dismissible fade show position-fixed`;
    notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 5000);
}

// Export Functions
function exportContainerData(format = 'excel') {
    const filters = getCurrentFilters();
    
    fetch(`/container-management/export/?format=${format}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify(filters)
    })
    .then(response => response.blob())
    .then(blob => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `container_data_${new Date().toISOString().split('T')[0]}.${format}`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        a.remove();
    })
    .catch(error => {
        console.error('Export error:', error);
        showNotification('Export failed', 'error');
    });
}

function getCurrentFilters() {
    const filters = {};
    const searchForm = document.querySelector('.search-form');
    
    if (searchForm) {
        const formData = new FormData(searchForm);
        for (let [key, value] of formData.entries()) {
            if (value) {
                filters[key] = value;
            }
        }
    }
    
    return filters;
}

// Print Functionality
function printContainerReport() {
    window.print();
}

// Keyboard Shortcuts
document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + N for new container
    if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
        e.preventDefault();
        window.location.href = '/container-management/containers/create/';
    }
    
    // Ctrl/Cmd + F for search
    if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
        e.preventDefault();
        const searchInput = document.getElementById('container-search');
        if (searchInput) {
            searchInput.focus();
        }
    }
    
    // Escape to close modals
    if (e.key === 'Escape') {
        const modals = document.querySelectorAll('.modal.show');
        modals.forEach(modal => {
            const modalInstance = bootstrap.Modal.getInstance(modal);
            if (modalInstance) {
                modalInstance.hide();
            }
        });
    }
});

// Mobile-specific functionality
if (window.innerWidth <= 768) {
    // Add mobile-specific event listeners
    const mobileMenuToggle = document.getElementById('mobile-menu-toggle');
    if (mobileMenuToggle) {
        mobileMenuToggle.addEventListener('click', function() {
            const sidebar = document.querySelector('.sidebar');
            sidebar.classList.toggle('show');
        });
    }
}

// Performance optimization
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

// Apply debouncing to search
const debouncedSearch = debounce(performContainerSearch, 300);

// Initialize tooltips
document.addEventListener('DOMContentLoaded', function() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});
