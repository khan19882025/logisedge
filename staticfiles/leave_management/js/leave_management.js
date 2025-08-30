// Leave Management System JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all components
    initializeLeaveForms();
    initializeDateCalculations();
    initializeDatePickers();
    initializeLeaveTypeSelection();
    initializeNotifications();
    initializeCalendar();
    initializeSearchFilters();
    initializeApprovalWorkflow();
});

// Date Calculations Initialization
function initializeDateCalculations() {
    // Initialize date-related calculations and validations
    setupDateRangeValidation();
    setupDateChangeHandlers();
}

// Date Picker Initialization
function initializeDatePickers() {
    // Initialize Flatpickr date pickers if available
    if (typeof flatpickr !== 'undefined') {
        const dateInputs = document.querySelectorAll('input[type="date"]');
        dateInputs.forEach(input => {
            flatpickr(input, {
                dateFormat: "Y-m-d",
                minDate: "today",
                allowInput: true,
                clickOpens: true,
                onChange: function(selectedDates, dateStr, instance) {
                    // Trigger change event for form validation
                    const event = new Event('change', { bubbles: true });
                    instance.input.dispatchEvent(event);
                }
            });
        });
    }
}

// Setup date change handlers
function setupDateChangeHandlers() {
    const startDate = document.getElementById('id_start_date');
    const endDate = document.getElementById('id_end_date');
    
    if (startDate && endDate) {
        // Update end date minimum when start date changes
        startDate.addEventListener('change', function() {
            if (this.value) {
                endDate.min = this.value;
                // If end date is before new start date, clear it
                if (endDate.value && endDate.value < this.value) {
                    endDate.value = '';
                }
            }
        });
        
        // Calculate total days when either date changes
        [startDate, endDate].forEach(dateField => {
            dateField.addEventListener('change', calculateTotalDays);
        });
    }
}

// Leave Form Initialization
function initializeLeaveForms() {
    const leaveForm = document.getElementById('leave-request-form');
    if (leaveForm) {
        setupFormValidation(leaveForm);
        setupDateRangeValidation();
        setupFileUpload();
        setupPrioritySelection();
    }
}

// Form Validation
function setupFormValidation(form) {
    form.addEventListener('submit', function(e) {
        if (!validateLeaveForm()) {
            e.preventDefault();
            return false;
        }
        
        // Show loading state
        const submitBtn = form.querySelector('button[type="submit"]');
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Submitting...';
        }
    });
}

function validateLeaveForm() {
    let isValid = true;
    const errors = [];
    
    // Validate required fields
    const requiredFields = ['leave_type', 'start_date', 'end_date', 'reason'];
    requiredFields.forEach(fieldName => {
        const field = document.getElementById(`id_${fieldName}`);
        if (field && !field.value.trim()) {
            field.classList.add('is-invalid');
            errors.push(`${fieldName.replace('_', ' ')} is required`);
            isValid = false;
        } else if (field) {
            field.classList.remove('is-invalid');
        }
    });
    
    // Validate date range
    const startDate = document.getElementById('id_start_date');
    const endDate = document.getElementById('id_end_date');
    
    if (startDate && endDate && startDate.value && endDate.value) {
        const start = new Date(startDate.value);
        const end = new Date(endDate.value);
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        
        if (start < today) {
            startDate.classList.add('is-invalid');
            errors.push('Start date cannot be in the past');
            isValid = false;
        }
        
        if (end < start) {
            endDate.classList.add('is-invalid');
            errors.push('End date cannot be before start date');
            isValid = false;
        }
    }
    
    // Validate half day selection
    const isHalfDay = document.getElementById('id_is_half_day');
    const halfDayType = document.getElementById('id_half_day_type');
    
    if (isHalfDay && isHalfDay.checked && (!halfDayType || !halfDayType.value)) {
        halfDayType.classList.add('is-invalid');
        errors.push('Please select half day type');
        isValid = false;
    }
    
    // Display errors
    if (!isValid) {
        showFormErrors(errors);
    }
    
    return isValid;
}

// Form Validation for Leave Request Form
function validateLeaveRequestForm() {
    let isValid = true;
    const errors = [];
    
    // Validate required fields
    const requiredFields = ['leave_type', 'start_date', 'end_date', 'reason'];
    requiredFields.forEach(fieldName => {
        const field = document.getElementById(`id_${fieldName}`);
        if (field && !field.value.trim()) {
            field.classList.add('is-invalid');
            errors.push(`${fieldName.replace('_', ' ')} is required`);
            isValid = false;
        } else if (field) {
            field.classList.remove('is-invalid');
        }
    });
    
    // Validate employee field if it exists
    const employeeField = document.getElementById('id_employee');
    if (employeeField && employeeField.style.display !== 'none' && !employeeField.value) {
        employeeField.classList.add('is-invalid');
        errors.push('Employee selection is required');
        isValid = false;
    } else if (employeeField) {
        employeeField.classList.remove('is-invalid');
    }
    
    // Validate date range
    const startDate = document.getElementById('id_start_date');
    const endDate = document.getElementById('id_end_date');
    
    if (startDate && endDate && startDate.value && endDate.value) {
        const start = new Date(startDate.value);
        const end = new Date(endDate.value);
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        
        if (start < today) {
            startDate.classList.add('is-invalid');
            errors.push('Start date cannot be in the past');
            isValid = false;
        }
        
        if (end < start) {
            endDate.classList.add('is-invalid');
            errors.push('End date cannot be before start date');
            isValid = false;
        }
    }
    
    // Validate half day selection
    const isHalfDay = document.getElementById('id_is_half_day');
    const halfDayType = document.getElementById('id_half_day_type');
    
    if (isHalfDay && isHalfDay.checked && (!halfDayType || !halfDayType.value)) {
        halfDayType.classList.add('is-invalid');
        errors.push('Please select half day type');
        isValid = false;
    }
    
    // Display errors
    if (!isValid) {
        showFormErrors(errors);
    }
    
    return isValid;
}

function showFormErrors(errors) {
    // Remove existing error alerts
    const existingAlerts = document.querySelectorAll('.alert-danger');
    existingAlerts.forEach(alert => alert.remove());
    
    // Create error alert
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-danger alert-dismissible fade show';
    alertDiv.innerHTML = `
        <strong>Please correct the following errors:</strong>
        <ul class="mb-0 mt-2">
            ${errors.map(error => `<li>${error}</li>`).join('')}
        </ul>
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    const form = document.getElementById('leave-request-form');
    form.insertBefore(alertDiv, form.firstChild);
}

// Date Range Validation and Calculation
function setupDateRangeValidation() {
    const startDate = document.getElementById('id_start_date');
    const endDate = document.getElementById('id_end_date');
    const totalDaysDisplay = document.getElementById('total-days');
    
    if (startDate && endDate) {
        [startDate, endDate].forEach(dateField => {
            dateField.addEventListener('change', calculateTotalDays);
        });
    }
}

function calculateTotalDays() {
    const startDate = document.getElementById('id_start_date');
    const endDate = document.getElementById('id_end_date');
    const totalDaysDisplay = document.getElementById('total-days');
    const isHalfDay = document.getElementById('id_is_half_day');
    
    if (startDate && endDate && startDate.value && endDate.value) {
        const start = new Date(startDate.value);
        const end = new Date(endDate.value);
        
        // Calculate business days (excluding weekends)
        let totalDays = 0;
        const current = new Date(start);
        
        while (current <= end) {
            const dayOfWeek = current.getDay();
            if (dayOfWeek !== 0 && dayOfWeek !== 6) { // Not Sunday or Saturday
                totalDays++;
            }
            current.setDate(current.getDate() + 1);
        }
        
        // Adjust for half day
        if (isHalfDay && isHalfDay.checked) {
            totalDays = 0.5;
        }
        
        if (totalDaysDisplay) {
            totalDaysDisplay.textContent = totalDays;
        }
        
        // Check leave balance
        checkLeaveBalance(totalDays);
    }
}

function checkLeaveBalance(totalDays) {
    const leaveType = document.getElementById('id_leave_type');
    if (leaveType && leaveType.value) {
        // This would typically make an AJAX call to check balance
        // For now, we'll just show a warning if more than 30 days
        if (totalDays > 30) {
            showBalanceWarning('Leave request exceeds 30 days. Please ensure this is correct.');
        }
    }
}

function showBalanceWarning(message) {
    const warningDiv = document.createElement('div');
    warningDiv.className = 'alert alert-warning alert-dismissible fade show';
    warningDiv.innerHTML = `
        <i class="fas fa-exclamation-triangle me-2"></i>${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    const form = document.getElementById('leave-request-form');
    form.insertBefore(warningDiv, form.firstChild);
}

// Leave Type Selection
function initializeLeaveTypeSelection() {
    const leaveTypeCards = document.querySelectorAll('.leave-type-card');
    const leaveTypeInput = document.getElementById('id_leave_type');
    
    leaveTypeCards.forEach(card => {
        card.addEventListener('click', function() {
            // Remove selection from all cards
            leaveTypeCards.forEach(c => c.classList.remove('selected'));
            
            // Add selection to clicked card
            this.classList.add('selected');
            
            // Update hidden input
            const leaveTypeId = this.dataset.leaveTypeId;
            if (leaveTypeInput) {
                leaveTypeInput.value = leaveTypeId;
            }
            
            // Show leave type details
            showLeaveTypeDetails(this.dataset);
        });
    });
}

function showLeaveTypeDetails(data) {
    const detailsContainer = document.getElementById('leave-type-details');
    if (detailsContainer && data) {
        detailsContainer.innerHTML = `
            <div class="card">
                <div class="card-body">
                    <h6 class="card-title">${data.name}</h6>
                    <p class="card-text">${data.description || 'No description available'}</p>
                    <div class="row">
                        <div class="col-6">
                            <small class="text-muted">Max Days/Year:</small>
                            <div>${data.maxDays || 'Unlimited'}</div>
                        </div>
                        <div class="col-6">
                            <small class="text-muted">Notice Required:</small>
                            <div>${data.minNotice || '0'} days</div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        detailsContainer.style.display = 'block';
    }
}

// File Upload
function setupFileUpload() {
    const fileInput = document.getElementById('id_attachment');
    const filePreview = document.getElementById('file-preview');
    
    if (fileInput) {
        fileInput.addEventListener('change', function() {
            const file = this.files[0];
            if (file) {
                // Validate file type
                const allowedTypes = ['application/pdf', 'application/msword', 
                                    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                                    'image/jpeg', 'image/png'];
                
                if (!allowedTypes.includes(file.type)) {
                    alert('Please select a valid file type (PDF, DOC, DOCX, JPG, PNG)');
                    this.value = '';
                    return;
                }
                
                // Validate file size (5MB limit)
                if (file.size > 5 * 1024 * 1024) {
                    alert('File size must be less than 5MB');
                    this.value = '';
                    return;
                }
                
                // Show file preview
                if (filePreview) {
                    filePreview.innerHTML = `
                        <div class="alert alert-info">
                            <i class="fas fa-file me-2"></i>
                            ${file.name} (${(file.size / 1024 / 1024).toFixed(2)} MB)
                        </div>
                    `;
                }
            } else if (filePreview) {
                filePreview.innerHTML = '';
            }
        });
    }
}

// Priority Selection
function setupPrioritySelection() {
    const priorityInputs = document.querySelectorAll('input[name="priority"]');
    const priorityCards = document.querySelectorAll('.priority-card');
    
    priorityCards.forEach(card => {
        card.addEventListener('click', function() {
            const priority = this.dataset.priority;
            
            // Update radio button
            const radio = document.querySelector(`input[name="priority"][value="${priority}"]`);
            if (radio) {
                radio.checked = true;
            }
            
            // Update visual selection
            priorityCards.forEach(c => c.classList.remove('selected'));
            this.classList.add('selected');
        });
    });
}

// Notifications
function initializeNotifications() {
    // Mark notification as read
    const notificationItems = document.querySelectorAll('.notification-item');
    notificationItems.forEach(item => {
        item.addEventListener('click', function() {
            const notificationId = this.dataset.notificationId;
            if (notificationId) {
                markNotificationAsRead(notificationId, this);
            }
        });
    });
    
    // Real-time notification updates
    setupNotificationPolling();
}

function markNotificationAsRead(notificationId, element) {
    fetch('/leave-management/notifications/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            notification_id: notificationId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            element.classList.add('read');
            const unreadIndicator = element.querySelector('.notification-unread');
            if (unreadIndicator) {
                unreadIndicator.style.display = 'none';
            }
        }
    })
    .catch(error => console.error('Error marking notification as read:', error));
}

function setupNotificationPolling() {
    // Poll for new notifications every 30 seconds
    setInterval(() => {
        fetch('/leave-management/notifications/count/')
            .then(response => response.json())
            .then(data => {
                updateNotificationBadge(data.count);
            })
            .catch(error => console.error('Error fetching notification count:', error));
    }, 30000);
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

// Calendar
function initializeCalendar() {
    const calendar = document.getElementById('leave-calendar');
    if (calendar) {
        setupCalendarNavigation();
        setupCalendarEvents();
    }
}

function setupCalendarNavigation() {
    const prevBtn = document.getElementById('calendar-prev');
    const nextBtn = document.getElementById('calendar-next');
    const monthYearDisplay = document.getElementById('calendar-month-year');
    
    if (prevBtn && nextBtn) {
        prevBtn.addEventListener('click', () => navigateCalendar(-1));
        nextBtn.addEventListener('click', () => navigateCalendar(1));
    }
}

function navigateCalendar(direction) {
    const currentUrl = new URL(window.location);
    const currentYear = parseInt(currentUrl.searchParams.get('year') || new Date().getFullYear());
    const currentMonth = parseInt(currentUrl.searchParams.get('month') || new Date().getMonth() + 1);
    
    let newMonth = currentMonth + direction;
    let newYear = currentYear;
    
    if (newMonth > 12) {
        newMonth = 1;
        newYear++;
    } else if (newMonth < 1) {
        newMonth = 12;
        newYear--;
    }
    
    currentUrl.searchParams.set('year', newYear);
    currentUrl.searchParams.set('month', newMonth);
    window.location.href = currentUrl.toString();
}

function setupCalendarEvents() {
    const calendarDays = document.querySelectorAll('.calendar-day');
    calendarDays.forEach(day => {
        day.addEventListener('click', function() {
            const date = this.dataset.date;
            if (date) {
                showDayDetails(date);
            }
        });
    });
}

function showDayDetails(date) {
    // This would typically show a modal with leave details for the selected date
    console.log('Show details for date:', date);
}

// Search and Filters
function initializeSearchFilters() {
    const searchForm = document.getElementById('search-form');
    if (searchForm) {
        setupFilterReset();
        setupFilterAutoSubmit();
    }
}

function setupFilterReset() {
    const resetBtn = document.getElementById('reset-filters');
    if (resetBtn) {
        resetBtn.addEventListener('click', function(e) {
            e.preventDefault();
            const form = document.getElementById('search-form');
            form.reset();
            form.submit();
        });
    }
}

function setupFilterAutoSubmit() {
    const filterInputs = document.querySelectorAll('#search-form select, #search-form input[type="date"]');
    filterInputs.forEach(input => {
        input.addEventListener('change', function() {
            document.getElementById('search-form').submit();
        });
    });
}

// Approval Workflow
function initializeApprovalWorkflow() {
    const approvalForm = document.getElementById('approval-form');
    if (approvalForm) {
        setupApprovalActions();
        setupApprovalComments();
    }
}

function setupApprovalActions() {
    const actionButtons = document.querySelectorAll('.approval-action-btn');
    actionButtons.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const action = this.dataset.action;
            const requestId = this.dataset.requestId;
            
            if (confirm(`Are you sure you want to ${action} this leave request?`)) {
                submitApproval(action, requestId);
            }
        });
    });
}

function submitApproval(action, requestId) {
    const form = document.getElementById('approval-form');
    const actionInput = document.getElementById('id_action');
    const commentsInput = document.getElementById('id_comments');
    
    if (actionInput) actionInput.value = action;
    
    // Validate comments for rejections
    if (action === 'reject' && (!commentsInput || !commentsInput.value.trim())) {
        alert('Please provide comments when rejecting a request.');
        commentsInput.focus();
        return;
    }
    
    form.submit();
}

function setupApprovalComments() {
    const actionSelect = document.getElementById('id_action');
    const commentsField = document.getElementById('id_comments');
    
    if (actionSelect && commentsField) {
        actionSelect.addEventListener('change', function() {
            if (this.value === 'reject') {
                commentsField.setAttribute('required', 'required');
                commentsField.placeholder = 'Please provide a reason for rejection...';
            } else {
                commentsField.removeAttribute('required');
                commentsField.placeholder = 'Enter your comments...';
            }
        });
    }
}

// Utility Functions
function getCookie(name) {
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

function showLoading(element) {
    if (element) {
        element.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Loading...';
        element.disabled = true;
    }
}

function hideLoading(element, originalText) {
    if (element) {
        element.innerHTML = originalText;
        element.disabled = false;
    }
}

function showToast(message, type = 'info') {
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
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    const toastContainer = document.getElementById('toast-container') || document.body;
    toastContainer.appendChild(toast);
    
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    // Remove toast element after it's hidden
    toast.addEventListener('hidden.bs.toast', () => {
        toast.remove();
    });
}

// Export functions for use in other scripts
window.LeaveManagement = {
    showToast,
    showLoading,
    hideLoading,
    calculateTotalDays,
    validateLeaveForm
}; 