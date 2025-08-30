// Customer Module JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize customer functionality
    initCustomerForm();
    initPasswordGeneration();
    initFormValidation();
    initTabNavigation();
    initSearchFunctionality();
});

// Initialize customer form functionality
function initCustomerForm() {
    const form = document.getElementById('customerForm');
    if (!form) return;

    // Auto-generate customer code if empty
    const customerCodeField = document.getElementById('id_customer_code');
    if (customerCodeField && !customerCodeField.value) {
        customerCodeField.addEventListener('blur', function() {
            if (!this.value) {
                generateCustomerCode();
            }
        });
    }

    // Auto-generate portal username if empty
    const portalUsernameField = document.getElementById('id_portal_username');
    if (portalUsernameField) {
        portalUsernameField.addEventListener('blur', function() {
            if (!this.value && customerCodeField && customerCodeField.value) {
                this.value = 'cust_' + customerCodeField.value.toLowerCase();
            }
        });
    }
}

// Generate customer code
function generateCustomerCode() {
    const customerCodeField = document.getElementById('id_customer_code');
    if (!customerCodeField) return;

    // Generate a simple customer code (you can customize this logic)
    const timestamp = Date.now().toString().slice(-6);
    const random = Math.random().toString(36).substring(2, 5).toUpperCase();
    customerCodeField.value = 'CUST' + timestamp + random;
}

// Initialize password generation functionality
function initPasswordGeneration() {
    const generatePasswordBtn = document.getElementById('generatePassword');
    const passwordField = document.getElementById('id_portal_password');
    const togglePasswordBtn = document.getElementById('togglePassword');

    if (generatePasswordBtn && passwordField) {
        generatePasswordBtn.addEventListener('click', function() {
            const password = generateSecurePassword();
            passwordField.value = password;
            passwordField.type = 'text';
            
            // Show success message
            showToast('Password generated successfully!', 'success');
        });
    }

    if (togglePasswordBtn && passwordField) {
        togglePasswordBtn.addEventListener('click', function() {
            const icon = this.querySelector('i');
            if (passwordField.type === 'password') {
                passwordField.type = 'text';
                icon.className = 'bi bi-eye-slash';
            } else {
                passwordField.type = 'password';
                icon.className = 'bi bi-eye';
            }
        });
    }
}

// Generate secure password
function generateSecurePassword(length = 12) {
    const charset = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*';
    let password = '';
    
    // Ensure at least one character from each category
    password += 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'[Math.floor(Math.random() * 26)];
    password += 'abcdefghijklmnopqrstuvwxyz'[Math.floor(Math.random() * 26)];
    password += '0123456789'[Math.floor(Math.random() * 10)];
    password += '!@#$%^&*'[Math.floor(Math.random() * 8)];
    
    // Fill the rest randomly
    for (let i = 4; i < length; i++) {
        password += charset[Math.floor(Math.random() * charset.length)];
    }
    
    // Shuffle the password
    return password.split('').sort(() => Math.random() - 0.5).join('');
}

// Initialize form validation
function initFormValidation() {
    const form = document.getElementById('customerForm');
    if (!form) return;

    // Real-time validation
    const requiredFields = form.querySelectorAll('[required]');
    requiredFields.forEach(field => {
        field.addEventListener('blur', function() {
            validateField(this);
        });
        
        field.addEventListener('input', function() {
            if (this.classList.contains('is-invalid')) {
                validateField(this);
            }
        });
    });

    // Form submission validation
    form.addEventListener('submit', function(e) {
        if (!validateForm()) {
            e.preventDefault();
            showToast('Please correct the errors before submitting.', 'error');
        }
    });
}

// Validate individual field
function validateField(field) {
    const value = field.value.trim();
    const fieldName = field.name;
    
    // Remove existing validation classes
    field.classList.remove('is-valid', 'is-invalid');
    
    // Check if required field is empty
    if (field.hasAttribute('required') && !value) {
        field.classList.add('is-invalid');
        return false;
    }
    
    // Email validation
    if (fieldName === 'email' && value) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(value)) {
            field.classList.add('is-invalid');
            return false;
        }
    }
    
    // Phone validation
    if ((fieldName === 'phone' || fieldName === 'mobile') && value) {
        const phoneRegex = /^[\d\s\-\+\(\)]+$/;
        if (!phoneRegex.test(value)) {
            field.classList.add('is-invalid');
            return false;
        }
    }
    
    // URL validation
    if (fieldName === 'website' && value) {
        try {
            new URL(value);
        } catch {
            field.classList.add('is-invalid');
            return false;
        }
    }
    
    // Portal username validation
    if (fieldName === 'portal_username' && value) {
        const usernameRegex = /^[a-zA-Z0-9_]+$/;
        if (!usernameRegex.test(value)) {
            field.classList.add('is-invalid');
            return false;
        }
    }
    
    field.classList.add('is-valid');
    return true;
}

// Validate entire form
function validateForm() {
    const form = document.getElementById('customerForm');
    if (!form) return true;

    let isValid = true;
    const requiredFields = form.querySelectorAll('[required]');
    
    requiredFields.forEach(field => {
        if (!validateField(field)) {
            isValid = false;
        }
    });
    
    return isValid;
}

// Initialize tab navigation
function initTabNavigation() {
    const tabLinks = document.querySelectorAll('[data-bs-toggle="tab"]');
    
    tabLinks.forEach(tab => {
        tab.addEventListener('click', function(e) {
            // Save active tab to localStorage
            const tabId = this.getAttribute('data-bs-target');
            localStorage.setItem('customerActiveTab', tabId);
        });
    });
    
    // Restore active tab from localStorage
    const activeTab = localStorage.getItem('customerActiveTab');
    if (activeTab) {
        const tab = document.querySelector(`[data-bs-target="${activeTab}"]`);
        if (tab) {
            const tabInstance = new bootstrap.Tab(tab);
            tabInstance.show();
        }
    }
}

// Initialize search functionality
function initSearchFunctionality() {
    const searchForm = document.querySelector('form[method="get"]');
    if (!searchForm) return;

    const searchInput = searchForm.querySelector('input[name="search"]');
    const clearBtn = document.querySelector('a[href*="customer_list"]');
    
    if (searchInput) {
        // Debounced search
        let searchTimeout;
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                if (this.value.length >= 2 || this.value.length === 0) {
                    searchForm.submit();
                }
            }, 500);
        });
    }
    
    if (clearBtn) {
        clearBtn.addEventListener('click', function(e) {
            e.preventDefault();
            window.location.href = this.href;
        });
    }
}

// Show toast notification
function showToast(message, type = 'info') {
    // Create toast container if it doesn't exist
    let toastContainer = document.getElementById('toastContainer');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toastContainer';
        toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
        toastContainer.style.zIndex = '9999';
        document.body.appendChild(toastContainer);
    }
    
    // Create toast element
    const toastId = 'toast-' + Date.now();
    const toastHtml = `
        <div id="${toastId}" class="toast" role="alert">
            <div class="toast-header">
                <i class="bi bi-${type === 'success' ? 'check-circle text-success' : type === 'error' ? 'x-circle text-danger' : 'info-circle text-info'} me-2"></i>
                <strong class="me-auto">${type.charAt(0).toUpperCase() + type.slice(1)}</strong>
                <button type="button" class="btn-close" data-bs-dismiss="toast"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        </div>
    `;
    
    toastContainer.insertAdjacentHTML('beforeend', toastHtml);
    
    // Show toast
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement, {
        autohide: true,
        delay: 3000
    });
    toast.show();
    
    // Remove toast element after it's hidden
    toastElement.addEventListener('hidden.bs.toast', function() {
        this.remove();
    });
}

// AJAX functions for customer portal management
function generatePortalCredentials(customerId) {
    fetch(`/customer/${customerId}/generate-portal-credentials/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json',
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            document.getElementById('id_portal_username').value = data.username;
            document.getElementById('id_portal_password').value = data.password;
            showToast(data.message, 'success');
        } else {
            showToast('Failed to generate credentials.', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('An error occurred while generating credentials.', 'error');
    });
}

function togglePortalStatus(customerId) {
    fetch(`/customer/${customerId}/toggle-portal-status/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json',
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast(data.message, 'success');
            // Update UI if needed
            location.reload();
        } else {
            showToast('Failed to toggle portal status.', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('An error occurred while toggling portal status.', 'error');
    });
}

// Get CSRF token from cookies
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

// Export functions for global access
window.customerModule = {
    generatePortalCredentials,
    togglePortalStatus,
    showToast,
    generateSecurePassword
}; 