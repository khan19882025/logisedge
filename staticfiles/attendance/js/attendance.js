/**
 * Attendance & Time Tracking Module JavaScript
 * Handles all client-side functionality for the attendance system
 */

// Global variables
let currentTime = new Date();
let isClockRunning = false;
let attendanceData = {};

// Initialize attendance module
document.addEventListener('DOMContentLoaded', function() {
    initializeAttendanceModule();
});

/**
 * Initialize the attendance module
 */
function initializeAttendanceModule() {
    console.log('Initializing Attendance & Time Tracking Module...');
    
    // Initialize components
    initializeClock();
    initializeFormValidation();
    initializeAJAXHandlers();
    initializeRealTimeUpdates();
    initializeInteractiveElements();
    
    // Set up event listeners
    setupEventListeners();
    
    console.log('Attendance module initialized successfully');
}

/**
 * Initialize real-time clock
 */
function initializeClock() {
    const clockElement = document.getElementById('current-time');
    if (clockElement) {
        updateClock();
        setInterval(updateClock, 1000);
        isClockRunning = true;
    }
}

/**
 * Update the clock display
 */
function updateClock() {
    const now = new Date();
    const timeString = now.toLocaleTimeString('en-US', {
        hour12: false,
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
    
    const clockElement = document.getElementById('current-time');
    if (clockElement) {
        clockElement.textContent = timeString;
    }
    
    currentTime = now;
}

/**
 * Initialize form validation
 */
function initializeFormValidation() {
    // Attendance entry form validation
    const attendanceForm = document.getElementById('attendance-form');
    if (attendanceForm) {
        attendanceForm.addEventListener('submit', validateAttendanceForm);
    }
    
    // Search form validation
    const searchForm = document.getElementById('search-form');
    if (searchForm) {
        searchForm.addEventListener('submit', validateSearchForm);
    }
    
    // Real-time validation for time inputs
    const timeInputs = document.querySelectorAll('input[type="time"], input[type="datetime-local"]');
    timeInputs.forEach(input => {
        input.addEventListener('change', validateTimeInput);
        input.addEventListener('blur', validateTimeInput);
    });
}

/**
 * Validate attendance form
 */
function validateAttendanceForm(event) {
    const form = event.target;
    let isValid = true;
    
    // Clear previous errors
    clearFormErrors(form);
    
    // Validate required fields
    const requiredFields = form.querySelectorAll('[required]');
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            showFieldError(field, 'This field is required');
            isValid = false;
        }
    });
    
    // Validate check-in and check-out times
    const checkInTime = form.querySelector('[name="check_in_time"]');
    const checkOutTime = form.querySelector('[name="check_out_time"]');
    
    if (checkInTime && checkOutTime && checkInTime.value && checkOutTime.value) {
        const checkIn = new Date(checkInTime.value);
        const checkOut = new Date(checkOutTime.value);
        
        if (checkOut <= checkIn) {
            showFieldError(checkOutTime, 'Check-out time must be after check-in time');
            isValid = false;
        }
    }
    
    // Validate date
    const dateField = form.querySelector('[name="date"]');
    if (dateField && dateField.value) {
        const selectedDate = new Date(dateField.value);
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        
        if (selectedDate > today) {
            showFieldError(dateField, 'Cannot create attendance for future dates');
            isValid = false;
        }
    }
    
    if (!isValid) {
        event.preventDefault();
        showFormError('Please correct the errors below');
    }
}

/**
 * Validate search form
 */
function validateSearchForm(event) {
    const form = event.target;
    const startDate = form.querySelector('[name="start_date"]');
    const endDate = form.querySelector('[name="end_date"]');
    
    if (startDate && endDate && startDate.value && endDate.value) {
        const start = new Date(startDate.value);
        const end = new Date(endDate.value);
        
        if (end < start) {
            event.preventDefault();
            showFormError('End date cannot be before start date');
        }
    }
}

/**
 * Validate time input
 */
function validateTimeInput(event) {
    const input = event.target;
    const value = input.value;
    
    if (value) {
        const time = new Date(`2000-01-01T${value}`);
        if (isNaN(time.getTime())) {
            showFieldError(input, 'Please enter a valid time');
        } else {
            clearFieldError(input);
        }
    }
}

/**
 * Show field error
 */
function showFieldError(field, message) {
    field.classList.add('is-invalid');
    
    let errorDiv = field.parentNode.querySelector('.invalid-feedback');
    if (!errorDiv) {
        errorDiv = document.createElement('div');
        errorDiv.className = 'invalid-feedback';
        field.parentNode.appendChild(errorDiv);
    }
    
    errorDiv.textContent = message;
}

/**
 * Clear field error
 */
function clearFieldError(field) {
    field.classList.remove('is-invalid');
    const errorDiv = field.parentNode.querySelector('.invalid-feedback');
    if (errorDiv) {
        errorDiv.remove();
    }
}

/**
 * Clear all form errors
 */
function clearFormErrors(form) {
    const invalidFields = form.querySelectorAll('.is-invalid');
    invalidFields.forEach(field => {
        clearFieldError(field);
    });
    
    const formErrors = form.querySelectorAll('.alert-danger');
    formErrors.forEach(error => {
        error.remove();
    });
}

/**
 * Show form error
 */
function showFormError(message) {
    const form = document.querySelector('form');
    if (form) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'alert alert-danger';
        errorDiv.textContent = message;
        form.insertBefore(errorDiv, form.firstChild);
    }
}

/**
 * Initialize AJAX handlers
 */
function initializeAJAXHandlers() {
    // Set up CSRF token for AJAX requests
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
    if (csrfToken) {
        window.csrfToken = csrfToken.value;
    }
    
    // Handle AJAX form submissions
    const ajaxForms = document.querySelectorAll('.ajax-form');
    ajaxForms.forEach(form => {
        form.addEventListener('submit', handleAJAXFormSubmit);
    });
}

/**
 * Handle AJAX form submission
 */
function handleAJAXFormSubmit(event) {
    event.preventDefault();
    
    const form = event.target;
    const formData = new FormData(form);
    const submitButton = form.querySelector('[type="submit"]');
    const originalText = submitButton.textContent;
    
    // Show loading state
    submitButton.disabled = true;
    submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
    
    fetch(form.action, {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': window.csrfToken
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showSuccessMessage(data.message || 'Operation completed successfully');
            if (data.redirect) {
                setTimeout(() => {
                    window.location.href = data.redirect;
                }, 1500);
            }
        } else {
            showErrorMessage(data.message || 'An error occurred');
        }
    })
    .catch(error => {
        console.error('AJAX Error:', error);
        showErrorMessage('Network error occurred');
    })
    .finally(() => {
        // Restore button state
        submitButton.disabled = false;
        submitButton.textContent = originalText;
    });
}

/**
 * Initialize real-time updates
 */
function initializeRealTimeUpdates() {
    // Auto-refresh dashboard every 30 seconds
    if (document.querySelector('.attendance-dashboard')) {
        setInterval(refreshDashboard, 30000);
    }
    
    // Real-time attendance status updates
    if (document.querySelector('.time-tracking')) {
        setInterval(updateAttendanceStatus, 10000);
    }
}

/**
 * Refresh dashboard data
 */
function refreshDashboard() {
    fetch('/hr/attendance/api/attendance-status/')
        .then(response => response.json())
        .then(data => {
            updateDashboardStats(data);
        })
        .catch(error => {
            console.error('Dashboard refresh error:', error);
        });
}

/**
 * Update dashboard statistics
 */
function updateDashboardStats(data) {
    // Update present count
    const presentElement = document.querySelector('.stat-card.present .stat-number');
    if (presentElement && data.present_count !== undefined) {
        presentElement.textContent = data.present_count;
    }
    
    // Update absent count
    const absentElement = document.querySelector('.stat-card.absent .stat-number');
    if (absentElement && data.absent_count !== undefined) {
        absentElement.textContent = data.absent_count;
    }
    
    // Update late count
    const lateElement = document.querySelector('.stat-card.late .stat-number');
    if (lateElement && data.late_count !== undefined) {
        lateElement.textContent = data.late_count;
    }
}

/**
 * Update attendance status
 */
function updateAttendanceStatus() {
    const today = new Date().toISOString().split('T')[0];
    
    fetch(`/hr/attendance/api/attendance-status/?date=${today}`)
        .then(response => response.json())
        .then(data => {
            updateAttendanceTable(data.data);
        })
        .catch(error => {
            console.error('Status update error:', error);
        });
}

/**
 * Update attendance table
 */
function updateAttendanceTable(attendanceData) {
    const tableBody = document.querySelector('.attendance-table tbody');
    if (!tableBody) return;
    
    attendanceData.forEach(record => {
        const row = tableBody.querySelector(`[data-employee-id="${record.employee_id}"]`);
        if (row) {
            // Update check-in time
            const checkInCell = row.querySelector('.check-in-time');
            if (checkInCell) {
                checkInCell.textContent = record.check_in_time || '-';
            }
            
            // Update check-out time
            const checkOutCell = row.querySelector('.check-out-time');
            if (checkOutCell) {
                checkOutCell.textContent = record.check_out_time || '-';
            }
            
            // Update status
            const statusCell = row.querySelector('.status-badge');
            if (statusCell) {
                statusCell.className = `status-badge status-${record.status}`;
                statusCell.textContent = record.status_display;
            }
        }
    });
}

/**
 * Initialize interactive elements
 */
function initializeInteractiveElements() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Initialize modals
    const modalTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="modal"]'));
    modalTriggerList.forEach(trigger => {
        trigger.addEventListener('click', handleModalTrigger);
    });
}

/**
 * Handle modal trigger
 */
function handleModalTrigger(event) {
    const trigger = event.target;
    const modalId = trigger.getAttribute('data-bs-target');
    const modal = document.querySelector(modalId);
    
    if (modal) {
        const modalInstance = new bootstrap.Modal(modal);
        modalInstance.show();
    }
}

/**
 * Set up event listeners
 */
function setupEventListeners() {
    // Bulk actions
    const bulkActionButtons = document.querySelectorAll('.bulk-action-btn');
    bulkActionButtons.forEach(button => {
        button.addEventListener('click', handleBulkAction);
    });
    
    // Export buttons
    const exportButtons = document.querySelectorAll('.export-btn');
    exportButtons.forEach(button => {
        button.addEventListener('click', handleExport);
    });
    
    // Delete confirmations
    const deleteButtons = document.querySelectorAll('.delete-btn');
    deleteButtons.forEach(button => {
        button.addEventListener('click', confirmDelete);
    });
    
    // Quick actions
    const quickActionButtons = document.querySelectorAll('.quick-action-btn');
    quickActionButtons.forEach(button => {
        button.addEventListener('click', handleQuickAction);
    });
}

/**
 * Handle bulk actions
 */
function handleBulkAction(event) {
    const action = event.target.getAttribute('data-action');
    const selectedRows = document.querySelectorAll('.attendance-checkbox:checked');
    
    if (selectedRows.length === 0) {
        showWarningMessage('Please select at least one record');
        return;
    }
    
    const confirmMessage = `Are you sure you want to ${action} ${selectedRows.length} record(s)?`;
    if (confirm(confirmMessage)) {
        const formData = new FormData();
        formData.append('action', action);
        
        selectedRows.forEach(checkbox => {
            formData.append('records', checkbox.value);
        });
        
        fetch('/hr/attendance/bulk-action/', {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': window.csrfToken
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showSuccessMessage(data.message);
                location.reload();
            } else {
                showErrorMessage(data.message);
            }
        })
        .catch(error => {
            console.error('Bulk action error:', error);
            showErrorMessage('An error occurred during bulk action');
        });
    }
}

/**
 * Handle export
 */
function handleExport(event) {
    const format = event.target.getAttribute('data-format');
    const currentUrl = new URL(window.location);
    currentUrl.searchParams.set('export', format);
    
    window.location.href = currentUrl.toString();
}

/**
 * Confirm delete
 */
function confirmDelete(event) {
    const message = event.target.getAttribute('data-confirm') || 'Are you sure you want to delete this record?';
    if (!confirm(message)) {
        event.preventDefault();
    }
}

/**
 * Handle quick actions
 */
function handleQuickAction(event) {
    const action = event.target.getAttribute('data-action');
    
    switch (action) {
        case 'punch-in':
            handlePunchIn();
            break;
        case 'punch-out':
            handlePunchOut();
            break;
        case 'add-break':
            showBreakModal();
            break;
        default:
            console.log('Unknown quick action:', action);
    }
}

/**
 * Handle punch in
 */
function handlePunchIn() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            position => {
                const formData = new FormData();
                formData.append('action', 'check_in');
                formData.append('latitude', position.coords.latitude);
                formData.append('longitude', position.coords.longitude);
                
                submitPunch(formData);
            },
            error => {
                console.error('Geolocation error:', error);
                // Submit without location
                const formData = new FormData();
                formData.append('action', 'check_in');
                submitPunch(formData);
            }
        );
    } else {
        // Submit without location
        const formData = new FormData();
        formData.append('action', 'check_in');
        submitPunch(formData);
    }
}

/**
 * Handle punch out
 */
function handlePunchOut() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            position => {
                const formData = new FormData();
                formData.append('action', 'check_out');
                formData.append('latitude', position.coords.latitude);
                formData.append('longitude', position.coords.longitude);
                
                submitPunch(formData);
            },
            error => {
                console.error('Geolocation error:', error);
                // Submit without location
                const formData = new FormData();
                formData.append('action', 'check_out');
                submitPunch(formData);
            }
        );
    } else {
        // Submit without location
        const formData = new FormData();
        formData.append('action', 'check_out');
        submitPunch(formData);
    }
}

/**
 * Submit punch data
 */
function submitPunch(formData) {
    fetch('/hr/attendance/api/punch/', {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': window.csrfToken
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showSuccessMessage(data.message);
            setTimeout(() => {
                location.reload();
            }, 1500);
        } else {
            showErrorMessage(data.message);
        }
    })
    .catch(error => {
        console.error('Punch error:', error);
        showErrorMessage('An error occurred during punch');
    });
}

/**
 * Show break modal
 */
function showBreakModal() {
    const modal = document.getElementById('breakModal');
    if (modal) {
        const modalInstance = new bootstrap.Modal(modal);
        modalInstance.show();
    }
}

/**
 * Show success message
 */
function showSuccessMessage(message) {
    showMessage(message, 'success');
}

/**
 * Show error message
 */
function showErrorMessage(message) {
    showMessage(message, 'danger');
}

/**
 * Show warning message
 */
function showWarningMessage(message) {
    showMessage(message, 'warning');
}

/**
 * Show info message
 */
function showInfoMessage(message) {
    showMessage(message, 'info');
}

/**
 * Show message
 */
function showMessage(message, type) {
    const alertContainer = document.getElementById('alert-container') || document.body;
    
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    alertContainer.insertBefore(alertDiv, alertContainer.firstChild);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}

/**
 * Format time
 */
function formatTime(timeString) {
    if (!timeString) return '-';
    
    const time = new Date(timeString);
    return time.toLocaleTimeString('en-US', {
        hour12: false,
        hour: '2-digit',
        minute: '2-digit'
    });
}

/**
 * Format date
 */
function formatDate(dateString) {
    if (!dateString) return '-';
    
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

/**
 * Calculate hours between two times
 */
function calculateHours(startTime, endTime) {
    if (!startTime || !endTime) return 0;
    
    const start = new Date(startTime);
    const end = new Date(endTime);
    const diffMs = end - start;
    const diffHours = diffMs / (1000 * 60 * 60);
    
    return Math.round(diffHours * 100) / 100;
}

/**
 * Get current location
 */
function getCurrentLocation() {
    return new Promise((resolve, reject) => {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                position => {
                    resolve({
                        latitude: position.coords.latitude,
                        longitude: position.coords.longitude
                    });
                },
                error => {
                    reject(error);
                }
            );
        } else {
            reject(new Error('Geolocation is not supported'));
        }
    });
}

/**
 * Debounce function
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
 * Throttle function
 */
function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// Export functions for global use
window.AttendanceModule = {
    initialize: initializeAttendanceModule,
    showSuccessMessage,
    showErrorMessage,
    showWarningMessage,
    showInfoMessage,
    formatTime,
    formatDate,
    calculateHours,
    getCurrentLocation
}; 