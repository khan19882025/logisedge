/**
 * Bulk Email Sender - Main JavaScript File
 * Handles form interactions, validation, and dynamic functionality
 */

class BulkEmailSender {
    constructor() {
        this.init();
    }

    init() {
        this.bindEvents();
        this.initializeComponents();
        this.setupFormValidation();
        this.setupCharacterCounters();
        this.setupTemplatePreview();
        this.setupFileUpload();
        this.setupCampaignActions();
        this.setupRealTimeUpdates();
    }

    /**
     * Bind event listeners
     */
    bindEvents() {
        // Form submission events
        document.addEventListener('submit', this.handleFormSubmit.bind(this));
        
        // Dynamic form field changes
        document.addEventListener('change', this.handleFormChange.bind(this));
        
        // Real-time input events
        document.addEventListener('input', this.handleInputChange.bind(this));
        
        // Modal events
        document.addEventListener('show.bs.modal', this.handleModalShow.bind(this));
        document.addEventListener('hidden.bs.modal', this.handleModalHidden.bind(this));
        
        // Tab events
        document.addEventListener('shown.bs.tab', this.handleTabShow.bind(this));
    }

    /**
     * Initialize UI components
     */
    initializeComponents() {
        // Initialize tooltips
        this.initTooltips();
        
        // Initialize popovers
        this.initPopovers();
        
        // Initialize select2 if available
        this.initSelect2();
        
        // Initialize date/time pickers
        this.initDateTimePickers();
        
        // Initialize rich text editors
        this.initRichTextEditors();
    }

    /**
     * Setup form validation
     */
    setupFormValidation() {
        const forms = document.querySelectorAll('form[data-validate]');
        forms.forEach(form => {
            this.setupFormValidationForForm(form);
        });
    }

    /**
     * Setup validation for a specific form
     */
    setupFormValidationForForm(form) {
        const submitButton = form.querySelector('button[type="submit"]');
        const requiredFields = form.querySelectorAll('[required]');
        
        // Real-time validation
        requiredFields.forEach(field => {
            field.addEventListener('blur', () => {
                this.validateField(field);
            });
            
            field.addEventListener('input', () => {
                this.clearFieldError(field);
            });
        });
        
        // Form submission validation
        form.addEventListener('submit', (e) => {
            if (!this.validateForm(form)) {
                e.preventDefault();
                this.showFormErrors(form);
            }
        });
    }

    /**
     * Validate a single field
     */
    validateField(field) {
        const value = field.value.trim();
        let isValid = true;
        let errorMessage = '';

        // Required field validation
        if (field.hasAttribute('required') && !value) {
            isValid = false;
            errorMessage = 'This field is required';
        }

        // Email validation
        if (field.type === 'email' && value) {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(value)) {
                isValid = false;
                errorMessage = 'Please enter a valid email address';
            }
        }

        // URL validation
        if (field.type === 'url' && value) {
            try {
                new URL(value);
            } catch {
                isValid = false;
                errorMessage = 'Please enter a valid URL';
            }
        }

        // Custom validation attributes
        if (field.hasAttribute('data-min-length')) {
            const minLength = parseInt(field.getAttribute('data-min-length'));
            if (value.length < minLength) {
                isValid = false;
                errorMessage = `Minimum length is ${minLength} characters`;
            }
        }

        if (field.hasAttribute('data-max-length')) {
            const maxLength = parseInt(field.getAttribute('data-max-length'));
            if (value.length > maxLength) {
                isValid = false;
                errorMessage = `Maximum length is ${maxLength} characters`;
            }
        }

        // Apply validation result
        if (!isValid) {
            this.showFieldError(field, errorMessage);
        } else {
            this.clearFieldError(field);
        }

        return isValid;
    }

    /**
     * Validate entire form
     */
    validateForm(form) {
        const fields = form.querySelectorAll('input, textarea, select');
        let isValid = true;

        fields.forEach(field => {
            if (!this.validateField(field)) {
                isValid = false;
            }
        });

        return isValid;
    }

    /**
     * Show field error
     */
    showFieldError(field, message) {
        this.clearFieldError(field);
        
        field.classList.add('is-invalid');
        
        const errorDiv = document.createElement('div');
        errorDiv.className = 'invalid-feedback';
        errorDiv.textContent = message;
        
        field.parentNode.appendChild(errorDiv);
    }

    /**
     * Clear field error
     */
    clearFieldError(field) {
        field.classList.remove('is-invalid');
        
        const errorDiv = field.parentNode.querySelector('.invalid-feedback');
        if (errorDiv) {
            errorDiv.remove();
        }
    }

    /**
     * Show form errors summary
     */
    showFormErrors(form) {
        const errors = form.querySelectorAll('.is-invalid');
        if (errors.length > 0) {
            this.showNotification(`Please fix ${errors.length} error(s) in the form`, 'error');
        }
    }

    /**
     * Setup character counters
     */
    setupCharacterCounters() {
        const textareas = document.querySelectorAll('textarea[data-max-length]');
        textareas.forEach(textarea => {
            this.setupCharacterCounter(textarea);
        });
    }

    /**
     * Setup character counter for a specific textarea
     */
    setupCharacterCounter(textarea) {
        const maxLength = parseInt(textarea.getAttribute('data-max-length'));
        const counter = document.createElement('div');
        counter.className = 'character-counter';
        counter.innerHTML = `<small class="text-muted">0 / ${maxLength} characters</small>`;
        
        textarea.parentNode.appendChild(counter);
        
        const updateCounter = () => {
            const currentLength = textarea.value.length;
            const remaining = maxLength - currentLength;
            
            counter.innerHTML = `<small class="text-muted">${currentLength} / ${maxLength} characters</small>`;
            
            if (remaining < 0) {
                counter.classList.add('text-danger');
                textarea.classList.add('is-invalid');
            } else if (remaining < 50) {
                counter.classList.add('text-warning');
                textarea.classList.remove('is-invalid');
            } else {
                counter.classList.remove('text-danger', 'text-warning');
                textarea.classList.remove('is-invalid');
            }
        };
        
        textarea.addEventListener('input', updateCounter);
        updateCounter(); // Initial count
    }

    /**
     * Setup template preview functionality
     */
    setupTemplatePreview() {
        const previewButtons = document.querySelectorAll('[data-action="preview-template"]');
        previewButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                this.showTemplatePreview(button);
            });
        });
    }

    /**
     * Show template preview
     */
    showTemplatePreview(button) {
        const templateId = button.getAttribute('data-template-id');
        const modal = document.getElementById('templatePreviewModal');
        
        if (modal) {
            // Load template content via AJAX
            this.loadTemplateContent(templateId).then(content => {
                const previewArea = modal.querySelector('.template-preview-content');
                if (previewArea) {
                    previewArea.innerHTML = content;
                }
                
                // Show modal
                const bsModal = new bootstrap.Modal(modal);
                bsModal.show();
            });
        }
    }

    /**
     * Load template content via AJAX
     */
    async loadTemplateContent(templateId) {
        try {
            const response = await fetch(`/bulk-email-sender/templates/${templateId}/preview/`);
            const data = await response.json();
            return data.html_content || 'Template content not available';
        } catch (error) {
            console.error('Error loading template:', error);
            return 'Error loading template content';
        }
    }

    /**
     * Setup file upload functionality
     */
    setupFileUpload() {
        const fileInputs = document.querySelectorAll('input[type="file"]');
        fileInputs.forEach(input => {
            input.addEventListener('change', (e) => {
                this.handleFileUpload(e.target);
            });
        });
    }

    /**
     * Handle file upload
     */
    handleFileUpload(input) {
        const file = input.files[0];
        if (!file) return;

        // File size validation
        const maxSize = parseInt(input.getAttribute('data-max-size')) || 10 * 1024 * 1024; // 10MB default
        if (file.size > maxSize) {
            this.showNotification(`File size exceeds ${this.formatFileSize(maxSize)}`, 'error');
            input.value = '';
            return;
        }

        // File type validation
        const allowedTypes = input.getAttribute('data-allowed-types');
        if (allowedTypes) {
            const types = allowedTypes.split(',').map(t => t.trim());
            const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
            if (!types.includes(fileExtension)) {
                this.showNotification(`File type not allowed. Allowed types: ${types.join(', ')}`, 'error');
                input.value = '';
                return;
            }
        }

        // Show file info
        this.showFileInfo(input, file);
    }

    /**
     * Show file information
     */
    showFileInfo(input, file) {
        const fileInfo = document.createElement('div');
        fileInfo.className = 'file-info mt-2';
        fileInfo.innerHTML = `
            <div class="alert alert-info">
                <i class="fas fa-file"></i>
                <strong>${file.name}</strong> (${this.formatFileSize(file.size)})
                <button type="button" class="btn btn-sm btn-outline-danger ml-2" onclick="this.parentElement.parentElement.remove()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;

        // Remove existing file info
        const existingInfo = input.parentNode.querySelector('.file-info');
        if (existingInfo) {
            existingInfo.remove();
        }

        input.parentNode.appendChild(fileInfo);
    }

    /**
     * Setup campaign action buttons
     */
    setupCampaignActions() {
        const actionButtons = document.querySelectorAll('[data-action]');
        actionButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                this.handleCampaignAction(button);
            });
        });
    }

    /**
     * Handle campaign actions
     */
    handleCampaignAction(button) {
        const action = button.getAttribute('data-action');
        const campaignId = button.getAttribute('data-campaign-id');
        const confirmMessage = button.getAttribute('data-confirm');

        if (confirmMessage && !confirm(confirmMessage)) {
            return;
        }

        // Show loading state
        button.disabled = true;
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';

        // Perform action
        this.performCampaignAction(action, campaignId).then(result => {
            if (result.success) {
                this.showNotification(result.message, 'success');
                // Reload page or update UI
                setTimeout(() => {
                    location.reload();
                }, 1000);
            } else {
                this.showNotification(result.message || 'Action failed', 'error');
                button.disabled = false;
                button.innerHTML = button.getAttribute('data-original-text') || 'Action';
            }
        }).catch(error => {
            console.error('Campaign action error:', error);
            this.showNotification('An error occurred while performing the action', 'error');
            button.disabled = false;
            button.innerHTML = button.getAttribute('data-original-text') || 'Action';
        });
    }

    /**
     * Perform campaign action via AJAX
     */
    async performCampaignAction(action, campaignId) {
        try {
            const response = await fetch(`/bulk-email-sender/campaigns/${campaignId}/${action}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCSRFToken(),
                    'Content-Type': 'application/json',
                },
            });
            
            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Error performing campaign action:', error);
            throw error;
        }
    }

    /**
     * Setup real-time updates
     */
    setupRealTimeUpdates() {
        // Auto-refresh dashboard data
        if (document.querySelector('.dashboard-stats')) {
            setInterval(() => {
                this.refreshDashboardStats();
            }, 30000); // Refresh every 30 seconds
        }

        // Real-time campaign progress updates
        if (document.querySelector('.campaign-progress')) {
            setInterval(() => {
                this.updateCampaignProgress();
            }, 10000); // Update every 10 seconds
        }
    }

    /**
     * Refresh dashboard statistics
     */
    async refreshDashboardStats() {
        try {
            const response = await fetch('/bulk-email-sender/dashboard/stats/');
            const data = await response.json();
            
            // Update statistics
            Object.keys(data).forEach(key => {
                const element = document.querySelector(`[data-stat="${key}"]`);
                if (element) {
                    element.textContent = data[key];
                }
            });
        } catch (error) {
            console.error('Error refreshing dashboard stats:', error);
        }
    }

    /**
     * Update campaign progress
     */
    async updateCampaignProgress() {
        const progressBars = document.querySelectorAll('.campaign-progress-bar');
        progressBars.forEach(async (bar) => {
            const campaignId = bar.getAttribute('data-campaign-id');
            try {
                const response = await fetch(`/bulk-email-sender/campaigns/${campaignId}/progress/`);
                const data = await response.json();
                
                // Update progress bar
                const progressFill = bar.querySelector('.progress-fill');
                if (progressFill) {
                    progressFill.style.width = `${data.progress}%`;
                }
                
                // Update status text
                const statusText = bar.parentNode.querySelector('.progress-status');
                if (statusText) {
                    statusText.textContent = data.status;
                }
            } catch (error) {
                console.error('Error updating campaign progress:', error);
            }
        });
    }

    /**
     * Handle form submission
     */
    handleFormSubmit(e) {
        const form = e.target;
        
        // Show loading state
        const submitButton = form.querySelector('button[type="submit"]');
        if (submitButton) {
            submitButton.disabled = true;
            submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
        }
    }

    /**
     * Handle form field changes
     */
    handleFormChange(e) {
        const field = e.target;
        
        // Auto-save form data
        if (field.form && field.form.hasAttribute('data-auto-save')) {
            this.autoSaveForm(field.form);
        }
        
        // Dynamic form field dependencies
        if (field.hasAttribute('data-dependents')) {
            this.updateDependentFields(field);
        }
    }

    /**
     * Handle input changes
     */
    handleInputChange(e) {
        const field = e.target;
        
        // Real-time validation
        if (field.hasAttribute('data-validate-on-input')) {
            this.validateField(field);
        }
        
        // Auto-complete suggestions
        if (field.hasAttribute('data-autocomplete')) {
            this.showAutocompleteSuggestions(field);
        }
    }

    /**
     * Handle modal show event
     */
    handleModalShow(e) {
        const modal = e.target;
        
        // Initialize components in modal
        this.initializeModalComponents(modal);
        
        // Load modal content if needed
        if (modal.hasAttribute('data-load-content')) {
            this.loadModalContent(modal);
        }
    }

    /**
     * Handle modal hidden event
     */
    handleModalHidden(e) {
        const modal = e.target;
        
        // Clean up modal resources
        this.cleanupModal(modal);
    }

    /**
     * Handle tab show event
     */
    handleTabShow(e) {
        const tab = e.target;
        
        // Initialize components in tab content
        this.initializeTabComponents(tab);
    }

    /**
     * Initialize tooltips
     */
    initTooltips() {
        const tooltipElements = document.querySelectorAll('[data-bs-toggle="tooltip"]');
        tooltipElements.forEach(element => {
            new bootstrap.Tooltip(element);
        });
    }

    /**
     * Initialize popovers
     */
    initPopovers() {
        const popoverElements = document.querySelectorAll('[data-bs-toggle="popover"]');
        popoverElements.forEach(element => {
            new bootstrap.Popover(element);
        });
    }

    /**
     * Initialize Select2 if available
     */
    initSelect2() {
        if (typeof $ !== 'undefined' && $.fn.select2) {
            $('.select2').select2({
                theme: 'bootstrap-5',
                width: '100%'
            });
        }
    }

    /**
     * Initialize date/time pickers
     */
    initDateTimePickers() {
        // Initialize flatpickr if available
        if (typeof flatpickr !== 'undefined') {
            flatpickr('.datetime-picker', {
                enableTime: true,
                dateFormat: 'Y-m-d H:i',
                time_24hr: true
            });
            
            flatpickr('.date-picker', {
                dateFormat: 'Y-m-d'
            });
            
            flatpickr('.time-picker', {
                enableTime: true,
                noCalendar: true,
                dateFormat: 'H:i',
                time_24hr: true
            });
        }
    }

    /**
     * Initialize rich text editors
     */
    initRichTextEditors() {
        // Initialize TinyMCE if available
        if (typeof tinymce !== 'undefined') {
            const editors = document.querySelectorAll('.rich-text-editor');
            editors.forEach(editor => {
                tinymce.init({
                    selector: `#${editor.id}`,
                    height: 400,
                    plugins: 'link image code table lists',
                    toolbar: 'undo redo | formatselect | bold italic | alignleft aligncenter alignright | link image | code | table | bullist numlist',
                    menubar: false,
                    branding: false,
                    content_css: '/static/bulk_email_sender/css/editor.css'
                });
            });
        }
    }

    /**
     * Show notification
     */
    showNotification(message, type = 'info', duration = 5000) {
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

        // Auto-remove after duration
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, duration);
    }

    /**
     * Get CSRF token
     */
    getCSRFToken() {
        const token = document.querySelector('[name=csrfmiddlewaretoken]');
        return token ? token.value : '';
    }

    /**
     * Format file size
     */
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    /**
     * Auto-save form data
     */
    autoSaveForm(form) {
        const formData = new FormData(form);
        const data = {};
        
        for (let [key, value] of formData.entries()) {
            data[key] = value;
        }
        
        // Save to localStorage
        const formId = form.id || 'auto-save-form';
        localStorage.setItem(`form_${formId}`, JSON.stringify(data));
        
        // Show auto-save indicator
        this.showAutoSaveIndicator(form);
    }

    /**
     * Show auto-save indicator
     */
    showAutoSaveIndicator(form) {
        let indicator = form.querySelector('.auto-save-indicator');
        
        if (!indicator) {
            indicator = document.createElement('div');
            indicator.className = 'auto-save-indicator text-muted small mt-2';
            form.appendChild(indicator);
        }
        
        indicator.textContent = 'Auto-saved';
        indicator.style.opacity = '1';
        
        setTimeout(() => {
            indicator.style.opacity = '0.5';
        }, 2000);
    }

    /**
     * Update dependent fields
     */
    updateDependentFields(field) {
        const dependents = field.getAttribute('data-dependents').split(',');
        const value = field.value;
        
        dependents.forEach(dependentSelector => {
            const dependent = document.querySelector(dependentSelector.trim());
            if (dependent) {
                // Show/hide based on value
                if (value) {
                    dependent.style.display = 'block';
                } else {
                    dependent.style.display = 'none';
                }
            }
        });
    }

    /**
     * Show autocomplete suggestions
     */
    showAutocompleteSuggestions(field) {
        const query = field.value;
        const suggestionsContainer = field.parentNode.querySelector('.autocomplete-suggestions');
        
        if (query.length < 2) {
            if (suggestionsContainer) {
                suggestionsContainer.style.display = 'none';
            }
            return;
        }
        
        // Get suggestions (this would typically be an AJAX call)
        this.getAutocompleteSuggestions(query).then(suggestions => {
            if (suggestions.length > 0) {
                this.displayAutocompleteSuggestions(field, suggestions);
            }
        });
    }

    /**
     * Get autocomplete suggestions
     */
    async getAutocompleteSuggestions(query) {
        // This would typically make an AJAX call to get suggestions
        // For now, return mock data
        return [
            'suggestion1',
            'suggestion2',
            'suggestion3'
        ].filter(s => s.toLowerCase().includes(query.toLowerCase()));
    }

    /**
     * Display autocomplete suggestions
     */
    displayAutocompleteSuggestions(field, suggestions) {
        let container = field.parentNode.querySelector('.autocomplete-suggestions');
        
        if (!container) {
            container = document.createElement('div');
            container.className = 'autocomplete-suggestions';
            container.style.cssText = 'position: absolute; top: 100%; left: 0; right: 0; background: white; border: 1px solid #ddd; border-top: none; z-index: 1000; max-height: 200px; overflow-y: auto;';
            field.parentNode.style.position = 'relative';
            field.parentNode.appendChild(container);
        }
        
        container.innerHTML = suggestions.map(suggestion => 
            `<div class="suggestion-item p-2 border-bottom cursor-pointer" data-value="${suggestion}">${suggestion}</div>`
        ).join('');
        
        container.style.display = 'block';
        
        // Handle suggestion selection
        container.querySelectorAll('.suggestion-item').forEach(item => {
            item.addEventListener('click', () => {
                field.value = item.getAttribute('data-value');
                container.style.display = 'none';
                field.focus();
            });
        });
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.bulkEmailSender = new BulkEmailSender();
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = BulkEmailSender;
}
