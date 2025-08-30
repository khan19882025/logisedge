// User Management JavaScript

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeUserManagement();
});

function initializeUserManagement() {
    // Initialize tooltips
    initializeTooltips();
    
    // Initialize confirmation dialogs
    initializeConfirmationDialogs();
    
    // Initialize search functionality
    initializeSearch();
    
    // Initialize form validation
    initializeFormValidation();
}

// Initialize Bootstrap tooltips
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Initialize confirmation dialogs for delete actions
function initializeConfirmationDialogs() {
    const deleteButtons = document.querySelectorAll('.btn-delete');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const userName = this.dataset.userName || 'this user';
            
            if (confirm(`Are you sure you want to delete ${userName}? This action cannot be undone.`)) {
                // If confirmed, submit the form or redirect to delete URL
                const deleteUrl = this.href;
                if (deleteUrl) {
                    window.location.href = deleteUrl;
                }
            }
        });
    });
}

// Initialize search functionality with debouncing
function initializeSearch() {
    const searchInput = document.querySelector('input[name="search"]');
    if (searchInput) {
        let searchTimeout;
        
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                // Auto-submit search after 500ms of no typing
                if (this.value.length >= 2 || this.value.length === 0) {
                    this.form.submit();
                }
            }, 500);
        });
    }
}

// Initialize form validation
function initializeFormValidation() {
    const forms = document.querySelectorAll('.needs-validation');
    
    Array.prototype.slice.call(forms).forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });
}

// Utility function to show alerts
function showAlert(message, type = 'info', duration = 5000) {
    // Remove existing alerts
    const existingAlerts = document.querySelectorAll('.alert-floating');
    existingAlerts.forEach(alert => alert.remove());
    
    // Create new alert
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible fade show alert-floating`;
    alert.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 1050;
        min-width: 300px;
    `;
    
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    document.body.appendChild(alert);
    
    // Auto-remove after specified duration
    if (duration > 0) {
        setTimeout(() => {
            if (alert.parentNode) {
                alert.remove();
            }
        }, duration);
    }
}

// Function to handle AJAX form submissions
function submitFormAjax(form, successCallback, errorCallback) {
    const formData = new FormData(form);
    const url = form.action || window.location.href;
    
    fetch(url, {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': getCSRFToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            if (successCallback) {
                successCallback(data);
            } else {
                showAlert(data.message || 'Operation completed successfully!', 'success');
            }
        } else {
            if (errorCallback) {
                errorCallback(data);
            } else {
                showAlert(data.error || 'An error occurred. Please try again.', 'danger');
            }
        }
    })
    .catch(error => {
        console.error('Error:', error);
        if (errorCallback) {
            errorCallback({ error: 'Network error occurred' });
        } else {
            showAlert('Network error occurred. Please try again.', 'danger');
        }
    });
}

// Get CSRF token from cookie or meta tag
function getCSRFToken() {
    // Try to get from meta tag first
    const metaToken = document.querySelector('meta[name="csrf-token"]');
    if (metaToken) {
        return metaToken.getAttribute('content');
    }
    
    // Try to get from form input
    const inputToken = document.querySelector('input[name="csrfmiddlewaretoken"]');
    if (inputToken) {
        return inputToken.value;
    }
    
    // Try to get from cookie
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
        const [name, value] = cookie.trim().split('=');
        if (name === 'csrftoken') {
            return value;
        }
    }
    
    return '';
}

// Function to handle password generation
function generatePassword(length = 12) {
    const charset = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*';
    let password = '';
    
    // Ensure at least one character from each category
    const lowercase = 'abcdefghijklmnopqrstuvwxyz';
    const uppercase = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
    const numbers = '0123456789';
    const symbols = '!@#$%^&*';
    
    password += lowercase[Math.floor(Math.random() * lowercase.length)];
    password += uppercase[Math.floor(Math.random() * uppercase.length)];
    password += numbers[Math.floor(Math.random() * numbers.length)];
    password += symbols[Math.floor(Math.random() * symbols.length)];
    
    // Fill the rest randomly
    for (let i = password.length; i < length; i++) {
        password += charset[Math.floor(Math.random() * charset.length)];
    }
    
    // Shuffle the password
    return password.split('').sort(() => Math.random() - 0.5).join('');
}

// Function to copy text to clipboard
function copyToClipboard(text) {
    if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(text).then(() => {
            showAlert('Copied to clipboard!', 'success', 2000);
        }).catch(err => {
            console.error('Failed to copy: ', err);
            fallbackCopyTextToClipboard(text);
        });
    } else {
        fallbackCopyTextToClipboard(text);
    }
}

// Fallback copy function for older browsers
function fallbackCopyTextToClipboard(text) {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.top = '0';
    textArea.style.left = '0';
    textArea.style.position = 'fixed';
    
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    
    try {
        const successful = document.execCommand('copy');
        if (successful) {
            showAlert('Copied to clipboard!', 'success', 2000);
        } else {
            showAlert('Failed to copy to clipboard', 'warning');
        }
    } catch (err) {
        console.error('Fallback: Oops, unable to copy', err);
        showAlert('Failed to copy to clipboard', 'warning');
    }
    
    document.body.removeChild(textArea);
}

// Export functions for use in other scripts
window.UserManagement = {
    showAlert,
    submitFormAjax,
    getCSRFToken,
    generatePassword,
    copyToClipboard
};