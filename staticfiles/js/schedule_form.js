/**
 * Backup Scheduler - Schedule Form JavaScript
 * Handles dynamic form behavior and validation
 */

document.addEventListener('DOMContentLoaded', function() {
    initializeForm();
    setupEventListeners();
    setupDynamicFields();
});

/**
 * Initialize the form
 */
function initializeForm() {
    // Set initial field visibility based on frequency
    updateDynamicFields();
    
    // Add loading state to form
    const form = document.getElementById('scheduleForm');
    if (form) {
        form.addEventListener('submit', handleFormSubmit);
    }
}

/**
 * Setup event listeners
 */
function setupEventListeners() {
    // Frequency change handler
    const frequencySelect = document.getElementById('id_frequency');
    if (frequencySelect) {
        frequencySelect.addEventListener('change', updateDynamicFields);
    }
    
    // Form validation on input
    const formInputs = document.querySelectorAll('#scheduleForm input, #scheduleForm select, #scheduleForm textarea');
    formInputs.forEach(input => {
        input.addEventListener('blur', validateField);
        input.addEventListener('input', clearFieldValidation);
    });
    
    // Date and time picker initialization
    initializeDateTimePickers();
}

/**
 * Setup dynamic fields based on frequency selection
 */
function setupDynamicFields() {
    const frequencySelect = document.getElementById('id_frequency');
    if (!frequencySelect) return;
    
    // Get field containers
    const weeklyFields = document.getElementById('weeklyFields');
    const monthlyFields = document.getElementById('monthlyFields');
    const customFields = document.getElementById('customFields');
    
    if (weeklyFields && monthlyFields && customFields) {
        // Add CSS classes for animations
        weeklyFields.classList.add('dynamic-field');
        monthlyFields.classList.add('dynamic-field');
        customFields.classList.add('dynamic-field');
    }
}

/**
 * Update dynamic fields visibility based on frequency selection
 */
function updateDynamicFields() {
    const frequencySelect = document.getElementById('id_frequency');
    if (!frequencySelect) return;
    
    const selectedFrequency = frequencySelect.value;
    const weeklyFields = document.getElementById('weeklyFields');
    const monthlyFields = document.getElementById('monthlyFields');
    const customFields = document.getElementById('customFields');
    
    if (!weeklyFields || !monthlyFields || !customFields) return;
    
    // Hide all dynamic fields first
    hideField(weeklyFields);
    hideField(monthlyFields);
    hideField(customFields);
    
    // Show relevant fields based on frequency
    switch (selectedFrequency) {
        case 'weekly':
            showField(weeklyFields);
            break;
        case 'monthly':
            showField(monthlyFields);
            break;
        case 'custom':
            showField(customFields);
            break;
    }
    
    // Update field requirements
    updateFieldRequirements(selectedFrequency);
}

/**
 * Show a dynamic field with animation
 */
function showField(fieldContainer) {
    if (!fieldContainer) return;
    
    fieldContainer.style.display = 'block';
    fieldContainer.classList.remove('hide');
    fieldContainer.classList.add('show');
    
    // Trigger animation
    setTimeout(() => {
        fieldContainer.classList.add('field-enter');
    }, 10);
}

/**
 * Hide a dynamic field with animation
 */
function hideField(fieldContainer) {
    if (!fieldContainer) return;
    
    fieldContainer.classList.remove('show', 'field-enter');
    fieldContainer.classList.add('field-exit');
    
    setTimeout(() => {
        fieldContainer.style.display = 'none';
        fieldContainer.classList.remove('field-exit');
        fieldContainer.classList.add('hide');
    }, 300);
}

/**
 * Update field requirements based on frequency
 */
function updateFieldRequirements(frequency) {
    const weeklyField = document.getElementById('id_weekday');
    const monthlyField = document.getElementById('id_day_of_month');
    const cronField = document.getElementById('id_cron_expression');
    
    // Reset all fields
    if (weeklyField) weeklyField.removeAttribute('required');
    if (monthlyField) monthlyField.removeAttribute('required');
    if (cronField) cronField.removeAttribute('required');
    
    // Set required fields based on frequency
    switch (frequency) {
        case 'weekly':
            if (weeklyField) weeklyField.setAttribute('required', 'required');
            break;
        case 'monthly':
            if (monthlyField) monthlyField.setAttribute('required', 'required');
            break;
        case 'custom':
            if (cronField) cronField.setAttribute('required', 'required');
            break;
    }
}

/**
 * Initialize date and time pickers
 */
function initializeDateTimePickers() {
    // Date picker for start date
    const startDateField = document.getElementById('id_start_date');
    if (startDateField) {
        // Set minimum date to today
        const today = new Date().toISOString().split('T')[0];
        startDateField.setAttribute('min', today);
        
        // Add change event for validation
        startDateField.addEventListener('change', validateStartDate);
    }
    
    // Time picker for start time
    const startTimeField = document.getElementById('id_start_time');
    if (startTimeField) {
        // Set default time to current time + 1 hour
        const now = new Date();
        now.setHours(now.getHours() + 1);
        const timeString = now.toTimeString().slice(0, 5);
        startTimeField.value = timeString;
    }
}

/**
 * Validate start date
 */
function validateStartDate() {
    const startDateField = document.getElementById('id_start_date');
    if (!startDateField) return;
    
    const selectedDate = new Date(startDateField.value);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    
    if (selectedDate < today) {
        showFieldError(startDateField, 'Start date cannot be in the past');
        return false;
    }
    
    clearFieldError(startDateField);
    return true;
}

/**
 * Validate individual field
 */
function validateField(event) {
    const field = event.target;
    const value = field.value.trim();
    
    // Check if field is required
    if (field.hasAttribute('required') && !value) {
        showFieldError(field, 'This field is required');
        return false;
    }
    
    // Field-specific validation
    switch (field.name) {
        case 'name':
            if (value.length < 3) {
                showFieldError(field, 'Name must be at least 3 characters long');
                return false;
            }
            break;
            
        case 'retention_days':
            if (value < 1 || value > 3650) { // Max 10 years
                showFieldError(field, 'Retention days must be between 1 and 3650');
                return false;
            }
            break;
            
        case 'max_backups':
            if (value < 1 || value > 1000) {
                showFieldError(field, 'Maximum backups must be between 1 and 1000');
                return false;
            }
            break;
            
        case 'cron_expression':
            if (!validateCronExpression(value)) {
                showFieldError(field, 'Invalid cron expression format');
                return false;
            }
            break;
    }
    
    clearFieldError(field);
    return true;
}

/**
 * Validate cron expression format
 */
function validateCronExpression(cronString) {
    if (!cronString) return false;
    
    // Basic cron validation: 5 fields separated by spaces
    const cronParts = cronString.trim().split(/\s+/);
    if (cronParts.length !== 5) return false;
    
    // Validate each part
    const patterns = [
        /^(\*|[0-5]?[0-9])(\/[0-9]+)?$/, // Minutes: 0-59
        /^(\*|1?[0-9]|2[0-3])(\/[0-9]+)?$/, // Hours: 0-23
        /^(\*|[1-9]|[12][0-9]|3[01])(\/[0-9]+)?$/, // Day of month: 1-31
        /^(\*|[1-9]|1[0-2])(\/[0-9]+)?$/, // Month: 1-12
        /^(\*|[0-6])(\/[0-9]+)?$/ // Day of week: 0-6 (Sunday=0)
    ];
    
    for (let i = 0; i < 5; i++) {
        if (!patterns[i].test(cronParts[i])) {
            return false;
        }
    }
    
    return true;
}

/**
 * Show field error
 */
function showFieldError(field, message) {
    // Remove existing error
    clearFieldError(field);
    
    // Add error class
    field.classList.add('is-invalid');
    
    // Create error message
    const errorDiv = document.createElement('div');
    errorDiv.className = 'invalid-feedback';
    errorDiv.textContent = message;
    
    // Insert after field
    field.parentNode.appendChild(errorDiv);
}

/**
 * Clear field error
 */
function clearFieldError(field) {
    field.classList.remove('is-invalid');
    
    // Remove error message
    const errorDiv = field.parentNode.querySelector('.invalid-feedback');
    if (errorDiv) {
        errorDiv.remove();
    }
}

/**
 * Clear field validation on input
 */
function clearFieldValidation(event) {
    const field = event.target;
    if (field.classList.contains('is-invalid')) {
        clearFieldError(field);
    }
}

/**
 * Handle form submission
 */
function handleFormSubmit(event) {
    event.preventDefault();
    
    // Validate all fields
    if (!validateForm()) {
        return false;
    }
    
    // Show loading state
    showFormLoading();
    
    // Submit form
    const form = event.target;
    form.submit();
}

/**
 * Validate entire form
 */
function validateForm() {
    const form = document.getElementById('scheduleForm');
    if (!form) return false;
    
    const requiredFields = form.querySelectorAll('[required]');
    let isValid = true;
    
    requiredFields.forEach(field => {
        if (!validateField({ target: field })) {
            isValid = false;
        }
    });
    
    // Additional validation
    if (!validateStartDate()) {
        isValid = false;
    }
    
    return isValid;
}

/**
 * Show form loading state
 */
function showFormLoading() {
    const form = document.getElementById('scheduleForm');
    if (!form) return;
    
    form.classList.add('form-loading');
    
    // Disable submit button
    const submitBtn = form.querySelector('button[type="submit"]');
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Saving...';
    }
}

/**
 * Show success message
 */
function showSuccessMessage(message) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'success-message fade-in';
    messageDiv.innerHTML = `<i class="fas fa-check-circle"></i>${message}`;
    
    const form = document.getElementById('scheduleForm');
    if (form) {
        form.insertBefore(messageDiv, form.firstChild);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            messageDiv.remove();
        }, 5000);
    }
}

/**
 * Show error message
 */
function showErrorMessage(message) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'error-message fade-in';
    messageDiv.innerHTML = `<i class="fas fa-exclamation-circle"></i>${message}`;
    
    const form = document.getElementById('scheduleForm');
    if (form) {
        form.insertBefore(messageDiv, form.firstChild);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            messageDiv.remove();
        }, 5000);
    }
}

/**
 * Format cron expression for display
 */
function formatCronExpression(cronString) {
    if (!cronString) return '';
    
    const parts = cronString.split(' ');
    if (parts.length !== 5) return cronString;
    
    const descriptions = [];
    
    // Minutes
    if (parts[0] === '*') {
        descriptions.push('Every minute');
    } else if (parts[0].includes('/')) {
        const interval = parts[0].split('/')[1];
        descriptions.push(`Every ${interval} minutes`);
    } else {
        descriptions.push(`At minute ${parts[0]}`);
    }
    
    // Hours
    if (parts[1] === '*') {
        descriptions.push('of every hour');
    } else if (parts[1].includes('/')) {
        const interval = parts[1].split('/')[1];
        descriptions.push(`every ${interval} hours`);
    } else {
        descriptions.push(`at ${parts[1]}:00`);
    }
    
    // Day of month
    if (parts[2] === '*') {
        descriptions.push('of every day');
    } else if (parts[2].includes('/')) {
        const interval = parts[2].split('/')[1];
        descriptions.push(`every ${interval} days`);
    } else {
        descriptions.push(`on day ${parts[2]}`);
    }
    
    // Month
    if (parts[3] === '*') {
        descriptions.push('of every month');
    } else if (parts[3].includes('/')) {
        const interval = parts[3].split('/')[1];
        descriptions.push(`every ${interval} months`);
    } else {
        const months = ['January', 'February', 'March', 'April', 'May', 'June',
                       'July', 'August', 'September', 'October', 'November', 'December'];
        descriptions.push(`in ${months[parseInt(parts[3]) - 1]}`);
    }
    
    // Day of week
    if (parts[4] === '*') {
        descriptions.push('on any day of the week');
    } else if (parts[4].includes('/')) {
        const interval = parts[4].split('/')[1];
        descriptions.push(`every ${interval} days of the week`);
    } else {
        const weekdays = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
        descriptions.push(`on ${weekdays[parseInt(parts[4])]}`);
    }
    
    return descriptions.join(' ');
}

/**
 * Auto-save form data to localStorage
 */
function autoSaveForm() {
    const form = document.getElementById('scheduleForm');
    if (!form) return;
    
    const formData = new FormData(form);
    const data = {};
    
    for (let [key, value] of formData.entries()) {
        data[key] = value;
    }
    
    localStorage.setItem('backup_schedule_draft', JSON.stringify(data));
}

/**
 * Restore form data from localStorage
 */
function restoreFormData() {
    const savedData = localStorage.getItem('backup_schedule_draft');
    if (!savedData) return;
    
    try {
        const data = JSON.parse(savedData);
        const form = document.getElementById('scheduleForm');
        if (!form) return;
        
        Object.keys(data).forEach(key => {
            const field = form.querySelector(`[name="${key}"]`);
            if (field) {
                field.value = data[key];
            }
        });
        
        // Update dynamic fields
        updateDynamicFields();
        
        // Show restore message
        showSuccessMessage('Form data restored from previous session');
        
    } catch (error) {
        console.error('Error restoring form data:', error);
    }
}

/**
 * Clear saved form data
 */
function clearSavedFormData() {
    localStorage.removeItem('backup_schedule_draft');
}

// Auto-save form every 30 seconds
setInterval(autoSaveForm, 30000);

// Restore form data on page load
document.addEventListener('DOMContentLoaded', restoreFormData);

// Clear saved data when form is successfully submitted
document.addEventListener('submit', function(event) {
    if (event.target.id === 'scheduleForm') {
        clearSavedFormData();
    }
});
