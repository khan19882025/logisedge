/**
 * Employee Management JavaScript
 * Handles all interactive functionality for the Employee Management module
 */

class EmployeeManager {
    constructor() {
        this.init();
    }

    init() {
        this.bindEvents();
        this.initializeComponents();
        this.setupAjaxHandlers();
    }

    bindEvents() {
        // Search and filter functionality
        this.bindSearchEvents();
        
        // Form validation
        this.bindFormValidation();
        
        // Modal events
        this.bindModalEvents();
        
        // Table interactions
        this.bindTableEvents();
        
        // File upload preview
        this.bindFileUploadEvents();
    }

    bindSearchEvents() {
        // Real-time search
        const searchInput = document.querySelector('input[name="search"]');
        if (searchInput) {
            let searchTimeout;
            searchInput.addEventListener('input', (e) => {
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(() => {
                    this.performSearch(e.target.value);
                }, 500);
            });
        }

        // Filter changes
        const filterSelects = document.querySelectorAll('select[name="department"], select[name="status"], select[name="employment_type"]');
        filterSelects.forEach(select => {
            select.addEventListener('change', () => {
                this.applyFilters();
            });
        });
    }

    bindFormValidation() {
        const forms = document.querySelectorAll('form');
        forms.forEach(form => {
            form.addEventListener('submit', (e) => {
                if (!this.validateForm(form)) {
                    e.preventDefault();
                }
            });

            // Real-time validation
            const inputs = form.querySelectorAll('input, select, textarea');
            inputs.forEach(input => {
                input.addEventListener('blur', () => {
                    this.validateField(input);
                });
            });
        });
    }

    bindModalEvents() {
        // Delete confirmation modal
        const deleteModal = document.getElementById('deleteModal');
        if (deleteModal) {
            deleteModal.addEventListener('show.bs.modal', (event) => {
                const button = event.relatedTarget;
                const employeeId = button.getAttribute('data-employee-id');
                const employeeName = button.getAttribute('data-employee-name');
                
                const modalBody = deleteModal.querySelector('.modal-body');
                modalBody.innerHTML = `Are you sure you want to delete <strong>${employeeName}</strong>? This action cannot be undone.`;
                
                const deleteForm = deleteModal.querySelector('#deleteForm');
                deleteForm.action = `/employees/employees/${employeeId}/delete/`;
            });
        }
    }

    bindTableEvents() {
        // Row selection
        const tableRows = document.querySelectorAll('#employeeTable tbody tr');
        tableRows.forEach(row => {
            row.addEventListener('click', (e) => {
                if (!e.target.closest('.btn-group')) {
                    this.selectRow(row);
                }
            });
        });

        // Bulk actions
        const selectAllCheckbox = document.querySelector('#selectAll');
        if (selectAllCheckbox) {
            selectAllCheckbox.addEventListener('change', (e) => {
                this.toggleSelectAll(e.target.checked);
            });
        }
    }

    bindFileUploadEvents() {
        const fileInputs = document.querySelectorAll('input[type="file"]');
        fileInputs.forEach(input => {
            input.addEventListener('change', (e) => {
                this.handleFileUpload(e.target);
            });
        });
    }

    initializeComponents() {
        // Initialize tooltips
        this.initializeTooltips();
        
        // Initialize date pickers
        this.initializeDatePickers();
        
        // Initialize select2 (if available)
        this.initializeSelect2();
        
        // Initialize data tables (if available)
        this.initializeDataTables();
    }

    initializeTooltips() {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }

    initializeDatePickers() {
        const dateInputs = document.querySelectorAll('input[type="date"]');
        dateInputs.forEach(input => {
            // Set max date to today for date of birth and join date
            if (input.name === 'date_of_birth' || input.name === 'join_date') {
                input.max = new Date().toISOString().split('T')[0];
            }
        });
    }

    initializeSelect2() {
        // Initialize select2 if the library is loaded
        if (typeof $.fn.select2 !== 'undefined') {
            $('.form-select').select2({
                theme: 'bootstrap-5',
                width: '100%'
            });
        }
    }

    initializeDataTables() {
        // Initialize DataTables if the library is loaded
        if (typeof $.fn.DataTable !== 'undefined') {
            $('#employeeTable').DataTable({
                responsive: true,
                pageLength: 20,
                order: [[0, 'asc']],
                language: {
                    search: "Search employees:",
                    lengthMenu: "Show _MENU_ employees per page",
                    info: "Showing _START_ to _END_ of _TOTAL_ employees",
                    paginate: {
                        first: "First",
                        last: "Last",
                        next: "Next",
                        previous: "Previous"
                    }
                }
            });
        }
    }

    setupAjaxHandlers() {
        // Setup CSRF token for AJAX requests
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
        if (csrfToken) {
            this.csrfToken = csrfToken.value;
        }
    }

    performSearch(query) {
        const currentUrl = new URL(window.location);
        if (query) {
            currentUrl.searchParams.set('search', query);
        } else {
            currentUrl.searchParams.delete('search');
        }
        currentUrl.searchParams.delete('page'); // Reset to first page
        window.location.href = currentUrl.toString();
    }

    applyFilters() {
        const form = document.querySelector('form[method="get"]');
        if (form) {
            form.submit();
        }
    }

    validateForm(form) {
        let isValid = true;
        const requiredFields = form.querySelectorAll('[required]');
        
        requiredFields.forEach(field => {
            if (!this.validateField(field)) {
                isValid = false;
            }
        });

        // Custom validation rules
        const emailField = form.querySelector('input[type="email"]');
        if (emailField && emailField.value) {
            if (!this.isValidEmail(emailField.value)) {
                this.showFieldError(emailField, 'Please enter a valid email address');
                isValid = false;
            }
        }

        const phoneField = form.querySelector('input[name="mobile"]');
        if (phoneField && phoneField.value) {
            if (!this.isValidPhone(phoneField.value)) {
                this.showFieldError(phoneField, 'Please enter a valid phone number');
                isValid = false;
            }
        }

        return isValid;
    }

    validateField(field) {
        const value = field.value.trim();
        
        // Clear previous errors
        this.clearFieldError(field);
        
        // Check if required field is empty
        if (field.hasAttribute('required') && !value) {
            this.showFieldError(field, 'This field is required');
            return false;
        }

        // Email validation
        if (field.type === 'email' && value && !this.isValidEmail(value)) {
            this.showFieldError(field, 'Please enter a valid email address');
            return false;
        }

        // Phone validation
        if (field.name === 'mobile' && value && !this.isValidPhone(value)) {
            this.showFieldError(field, 'Please enter a valid phone number');
            return false;
        }

        return true;
    }

    showFieldError(field, message) {
        field.classList.add('is-invalid');
        
        // Remove existing error message
        const existingError = field.parentNode.querySelector('.invalid-feedback');
        if (existingError) {
            existingError.remove();
        }
        
        // Add new error message
        const errorDiv = document.createElement('div');
        errorDiv.className = 'invalid-feedback';
        errorDiv.textContent = message;
        field.parentNode.appendChild(errorDiv);
    }

    clearFieldError(field) {
        field.classList.remove('is-invalid');
        const errorDiv = field.parentNode.querySelector('.invalid-feedback');
        if (errorDiv) {
            errorDiv.remove();
        }
    }

    isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }

    isValidPhone(phone) {
        const phoneRegex = /^\+?1?\d{9,15}$/;
        return phoneRegex.test(phone);
    }

    selectRow(row) {
        // Remove selection from other rows
        document.querySelectorAll('#employeeTable tbody tr').forEach(r => {
            r.classList.remove('table-active');
        });
        
        // Add selection to clicked row
        row.classList.add('table-active');
    }

    toggleSelectAll(checked) {
        const checkboxes = document.querySelectorAll('#employeeTable tbody input[type="checkbox"]');
        checkboxes.forEach(checkbox => {
            checkbox.checked = checked;
        });
    }

    handleFileUpload(input) {
        const file = input.files[0];
        if (!file) return;

        // Validate file size (5MB limit)
        const maxSize = 5 * 1024 * 1024; // 5MB
        if (file.size > maxSize) {
            alert('File size must be less than 5MB');
            input.value = '';
            return;
        }

        // Validate file type
        const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif'];
        if (!allowedTypes.includes(file.type)) {
            alert('Please select a valid image file (JPG, PNG, GIF)');
            input.value = '';
            return;
        }

        // Show preview if it's an image
        if (file.type.startsWith('image/')) {
            this.showImagePreview(input, file);
        }
    }

    showImagePreview(input, file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            const previewContainer = input.parentNode.querySelector('.image-preview');
            if (!previewContainer) {
                const container = document.createElement('div');
                container.className = 'image-preview mt-2';
                input.parentNode.appendChild(container);
            }
            
            const container = input.parentNode.querySelector('.image-preview');
            container.innerHTML = `
                <img src="${e.target.result}" alt="Preview" class="img-thumbnail" style="max-width: 200px; max-height: 200px;">
                <button type="button" class="btn btn-sm btn-outline-danger mt-1" onclick="this.parentNode.remove()">
                    <i class="bi bi-x"></i> Remove
                </button>
            `;
        };
        reader.readAsDataURL(file);
    }

    // AJAX helper methods
    async makeRequest(url, options = {}) {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.csrfToken
            }
        };

        const finalOptions = { ...defaultOptions, ...options };
        
        try {
            const response = await fetch(url, finalOptions);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error('Request failed:', error);
            throw error;
        }
    }

    // Export functionality
    exportEmployees(format = 'csv') {
        const currentUrl = new URL(window.location);
        currentUrl.searchParams.set('export', format);
        window.location.href = currentUrl.toString();
    }

    // Bulk operations
    async bulkDelete(employeeIds) {
        if (!confirm(`Are you sure you want to delete ${employeeIds.length} employees?`)) {
            return;
        }

        try {
            const response = await this.makeRequest('/employees/bulk-delete/', {
                method: 'POST',
                body: JSON.stringify({ employee_ids: employeeIds })
            });

            if (response.success) {
                this.showNotification('Employees deleted successfully', 'success');
                window.location.reload();
            } else {
                this.showNotification('Failed to delete employees', 'error');
            }
        } catch (error) {
            this.showNotification('An error occurred while deleting employees', 'error');
        }
    }

    // Notification system
    showNotification(message, type = 'info') {
        const alertClass = {
            'success': 'alert-success',
            'error': 'alert-danger',
            'warning': 'alert-warning',
            'info': 'alert-info'
        }[type] || 'alert-info';

        const alertHtml = `
            <div class="alert ${alertClass} alert-dismissible fade show" role="alert">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>
        `;

        // Create notification container if it doesn't exist
        let container = document.getElementById('notification-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'notification-container';
            container.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 9999; max-width: 400px;';
            document.body.appendChild(container);
        }

        // Add notification
        container.insertAdjacentHTML('beforeend', alertHtml);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            const alerts = container.querySelectorAll('.alert');
            if (alerts.length > 0) {
                alerts[0].remove();
            }
        }, 5000);
    }

    // Utility methods
    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    }

    formatCurrency(amount) {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD'
        }).format(amount);
    }

    debounce(func, wait) {
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
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.employeeManager = new EmployeeManager();
});

// Global utility functions
window.confirmDelete = function(employeeId, employeeName) {
    const modal = document.getElementById('deleteModal');
    if (modal) {
        document.getElementById('employeeName').textContent = employeeName;
        document.getElementById('deleteForm').action = `/employees/employees/${employeeId}/delete/`;
        new bootstrap.Modal(modal).show();
    }
};

window.exportEmployees = function(format) {
    if (window.employeeManager) {
        window.employeeManager.exportEmployees(format);
    }
};

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + N for new employee
    if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
        e.preventDefault();
        window.location.href = '/employees/employees/create/';
    }
    
    // Ctrl/Cmd + F for search
    if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
        e.preventDefault();
        const searchInput = document.querySelector('input[name="search"]');
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