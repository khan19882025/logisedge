/**
 * Notification Templates JavaScript
 * Handles all interactive functionality for the notification templates system
 */

class NotificationTemplates {
    constructor() {
        this.initializeEventListeners();
        this.initializeRichEditor();
        this.initializePlaceholderHelper();
        this.initializeTemplateValidation();
        this.initializeSearchFilters();
        this.initializeTestDataForm();
        this.initializePreviewTabs();
    }

    /**
     * Initialize all event listeners
     */
    initializeEventListeners() {
        // Template type change handler
        const templateTypeSelect = document.getElementById('template_type');
        if (templateTypeSelect) {
            templateTypeSelect.addEventListener('change', (e) => this.handleTemplateTypeChange(e));
        }

        // Form submission handler
        const templateForm = document.querySelector('form[method="post"]');
        if (templateForm) {
            templateForm.addEventListener('submit', (e) => this.handleFormSubmission(e));
        }

        // Placeholder insertion
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('placeholder-item')) {
                this.insertPlaceholder(e.target.textContent);
            }
        });

        // Auto-save functionality
        this.initializeAutoSave();

        // Character counter
        this.initializeCharacterCounters();
    }

    /**
     * Handle template type change
     */
    handleTemplateTypeChange(event) {
        const templateType = event.target.value;
        const htmlContentField = document.getElementById('id_html_content');
        const htmlContentGroup = htmlContentField?.closest('.form-group');
        const subjectField = document.getElementById('id_subject');
        const subjectGroup = subjectField?.closest('.form-group');

        // Show/hide HTML content field based on template type
        if (htmlContentGroup) {
            if (templateType === 'email') {
                htmlContentGroup.style.display = 'block';
                htmlContentField.required = true;
            } else {
                htmlContentGroup.style.display = 'none';
                htmlContentField.required = false;
            }
        }

        // Show/hide subject field for non-email templates
        if (subjectGroup) {
            if (templateType === 'email') {
                subjectGroup.style.display = 'block';
                subjectField.required = true;
            } else {
                subjectGroup.style.display = 'block';
                subjectField.required = false;
            }
        }

        // Update placeholder suggestions
        this.updatePlaceholderSuggestions(templateType);

        // Update content validation
        this.updateContentValidation(templateType);
    }

    /**
     * Initialize rich text editor
     */
    initializeRichEditor() {
        const htmlContentField = document.getElementById('id_html_content');
        if (!htmlContentField) return;

        // Create rich editor container
        const richEditorContainer = document.createElement('div');
        richEditorContainer.className = 'rich-editor-container';
        richEditorContainer.innerHTML = `
            <div class="rich-editor-toolbar">
                <button type="button" data-command="bold" title="Bold"><i class="fas fa-bold"></i></button>
                <button type="button" data-command="italic" title="Italic"><i class="fas fa-italic"></i></button>
                <button type="button" data-command="underline" title="Underline"><i class="fas fa-underline"></i></button>
                <button type="button" data-command="insertUnorderedList" title="Bullet List"><i class="fas fa-list-ul"></i></button>
                <button type="button" data-command="insertOrderedList" title="Numbered List"><i class="fas fa-list-ol"></i></button>
                <button type="button" data-command="createLink" title="Insert Link"><i class="fas fa-link"></i></button>
                <button type="button" data-command="insertImage" title="Insert Image"><i class="fas fa-image"></i></button>
                <button type="button" data-command="justifyLeft" title="Align Left"><i class="fas fa-align-left"></i></button>
                <button type="button" data-command="justifyCenter" title="Align Center"><i class="fas fa-align-center"></i></button>
                <button type="button" data-command="justifyRight" title="Align Right"><i class="fas fa-align-right"></i></button>
                <button type="button" data-command="undo" title="Undo"><i class="fas fa-undo"></i></button>
                <button type="button" data-command="redo" title="Redo"><i class="fas fa-redo"></i></button>
            </div>
            <div class="rich-editor-content" contenteditable="true"></div>
        `;

        // Replace the original field
        htmlContentField.parentNode.insertBefore(richEditorContainer, htmlContentField);
        htmlContentField.style.display = 'none';

        // Initialize editor functionality
        this.setupRichEditor(richEditorContainer, htmlContentField);
    }

    /**
     * Setup rich editor functionality
     */
    setupRichEditor(container, originalField) {
        const toolbar = container.querySelector('.rich-editor-toolbar');
        const content = container.querySelector('.rich-editor-content');

        // Set initial content
        content.innerHTML = originalField.value || '';

        // Toolbar button handlers
        toolbar.addEventListener('click', (e) => {
            if (e.target.tagName === 'BUTTON') {
                e.preventDefault();
                const command = e.target.dataset.command;
                this.executeEditorCommand(command, content);
            }
        });

        // Sync content with original field
        content.addEventListener('input', () => {
            originalField.value = content.innerHTML;
        });

        // Handle paste events
        content.addEventListener('paste', (e) => {
            e.preventDefault();
            const text = e.clipboardData.getData('text/html') || e.clipboardData.getData('text/plain');
            document.execCommand('insertHTML', false, text);
        });
    }

    /**
     * Execute editor command
     */
    executeEditorCommand(command, content) {
        switch (command) {
            case 'createLink':
                const url = prompt('Enter URL:');
                if (url) {
                    document.execCommand('createLink', false, url);
                }
                break;
            case 'insertImage':
                const imageUrl = prompt('Enter image URL:');
                if (imageUrl) {
                    document.execCommand('insertImage', false, imageUrl);
                }
                break;
            default:
                document.execCommand(command, false, null);
        }
        content.focus();
    }

    /**
     * Initialize placeholder helper
     */
    initializePlaceholderHelper() {
        const placeholderHelper = document.querySelector('.placeholder-helper');
        if (!placeholderHelper) return;

        // Load available placeholders
        this.loadAvailablePlaceholders();
    }

    /**
     * Load available placeholders
     */
    async loadAvailablePlaceholders() {
        try {
            const response = await fetch('/utilities/notification-templates/api/placeholders/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: new URLSearchParams({
                    template_type: document.getElementById('template_type')?.value || 'email'
                })
            });

            if (response.ok) {
                const data = await response.json();
                this.displayPlaceholders(data.placeholders);
            }
        } catch (error) {
            console.error('Error loading placeholders:', error);
        }
    }

    /**
     * Display placeholders in helper
     */
    displayPlaceholders(placeholders) {
        const placeholderHelper = document.querySelector('.placeholder-helper');
        if (!placeholderHelper) return;

        const placeholderList = placeholderHelper.querySelector('.placeholder-list') || 
                               placeholderHelper.querySelector('div');

        if (placeholderList) {
            placeholderList.innerHTML = placeholders.map(placeholder => `
                <span class="placeholder-item" data-placeholder="${placeholder.name}">
                    {{${placeholder.name}}}
                </span>
            `).join('');
        }
    }

    /**
     * Insert placeholder into content field
     */
    insertPlaceholder(placeholder) {
        const contentField = document.getElementById('id_content');
        const htmlContentField = document.getElementById('id_html_content');
        const richEditorContent = document.querySelector('.rich-editor-content');

        if (contentField) {
            const cursorPos = contentField.selectionStart;
            const textBefore = contentField.value.substring(0, cursorPos);
            const textAfter = contentField.value.substring(cursorPos);
            contentField.value = textBefore + placeholder + textAfter;
            contentField.focus();
            contentField.setSelectionRange(cursorPos + placeholder.length, cursorPos + placeholder.length);
        }

        if (richEditorContent) {
            document.execCommand('insertText', false, placeholder);
            richEditorContent.focus();
        }
    }

    /**
     * Initialize template validation
     */
    initializeTemplateValidation() {
        const contentField = document.getElementById('id_content');
        const htmlContentField = document.getElementById('id_html_content');

        if (contentField) {
            contentField.addEventListener('input', () => this.validateTemplate());
        }

        if (htmlContentField) {
            htmlContentField.addEventListener('input', () => this.validateTemplate());
        }
    }

    /**
     * Validate template content
     */
    async validateTemplate() {
        const templateType = document.getElementById('template_type')?.value;
        const content = document.getElementById('id_content')?.value || '';
        const htmlContent = document.getElementById('id_html_content')?.value || '';

        try {
            const response = await fetch('/utilities/notification-templates/api/validate/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: new URLSearchParams({
                    template_type: templateType,
                    content: content,
                    html_content: htmlContent
                })
            });

            if (response.ok) {
                const data = await response.json();
                this.displayValidationResults(data);
            }
        } catch (error) {
            console.error('Error validating template:', error);
        }
    }

    /**
     * Display validation results
     */
    displayValidationResults(validationData) {
        const validationContainer = document.getElementById('validation-results') || 
                                   this.createValidationContainer();

        if (validationData.valid) {
            validationContainer.innerHTML = `
                <div class="alert alert-success">
                    <i class="fas fa-check-circle"></i> Template validation passed!
                </div>
            `;
        } else {
            validationContainer.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-triangle"></i> Validation errors found:
                    <ul class="mb-0 mt-2">
                        ${validationData.errors.map(error => `<li>${error}</li>`).join('')}
                    </ul>
                </div>
            `;
        }
    }

    /**
     * Create validation container
     */
    createValidationContainer() {
        const container = document.createElement('div');
        container.id = 'validation-results';
        container.className = 'mb-3';
        
        const form = document.querySelector('form');
        if (form) {
            form.insertBefore(container, form.querySelector('.form-group:last-child'));
        }
        
        return container;
    }

    /**
     * Initialize search filters
     */
    initializeSearchFilters() {
        const searchForm = document.querySelector('.search-filter-form');
        if (!searchForm) return;

        // Auto-submit on filter change
        const filterInputs = searchForm.querySelectorAll('select, input[type="date"]');
        filterInputs.forEach(input => {
            input.addEventListener('change', () => searchForm.submit());
        });

        // Clear filters button
        const clearFiltersBtn = searchForm.querySelector('.clear-filters');
        if (clearFiltersBtn) {
            clearFiltersBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.clearSearchFilters(searchForm);
            });
        }
    }

    /**
     * Clear search filters
     */
    clearSearchFilters(form) {
        const inputs = form.querySelectorAll('input, select');
        inputs.forEach(input => {
            if (input.type === 'text' || input.type === 'date') {
                input.value = '';
            } else if (input.type === 'select-one') {
                input.selectedIndex = 0;
            }
        });
        form.submit();
    }

    /**
     * Initialize test data form
     */
    initializeTestDataForm() {
        const testDataForm = document.querySelector('.test-data-form');
        if (!testDataForm) return;

        // Auto-generate test data
        const generateBtn = testDataForm.querySelector('.generate-test-data');
        if (generateBtn) {
            generateBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.generateTestData();
            });
        }

        // Test data input handlers
        const testDataInputs = testDataForm.querySelectorAll('.test-data-input input');
        testDataInputs.forEach(input => {
            input.addEventListener('input', () => this.updateTestDataPreview());
        });
    }

    /**
     * Generate test data
     */
    generateTestData() {
        const testDataInputs = document.querySelectorAll('.test-data-input input');
        testDataInputs.forEach(input => {
            const placeholder = input.dataset.placeholder;
            if (placeholder) {
                input.value = this.generateSampleValue(placeholder);
            }
        });
        this.updateTestDataPreview();
    }

    /**
     * Generate sample value for placeholder
     */
    generateSampleValue(placeholder) {
        const samples = {
            'customer_name': 'John Doe',
            'customer_email': 'john.doe@example.com',
            'order_id': 'ORD-2024-001',
            'order_total': '$99.99',
            'due_date': '2024-12-25',
            'company_name': 'Acme Corporation',
            'invoice_number': 'INV-2024-001',
            'payment_amount': '$150.00',
            'shipping_address': '123 Main St, City, State 12345'
        };

        return samples[placeholder] || `Sample ${placeholder.replace('_', ' ')}`;
    }

    /**
     * Update test data preview
     */
    updateTestDataPreview() {
        const testDataInputs = document.querySelectorAll('.test-data-input input');
        const testData = {};
        
        testDataInputs.forEach(input => {
            const placeholder = input.dataset.placeholder;
            if (placeholder) {
                testData[placeholder] = input.value;
            }
        });

        // Update hidden field
        const testDataField = document.getElementById('id_test_data');
        if (testDataField) {
            testDataField.value = JSON.stringify(testData);
        }

        // Update preview if available
        this.updateTemplatePreview(testData);
    }

    /**
     * Update template preview with test data
     */
    updateTemplatePreview(testData) {
        const previewContent = document.querySelector('.preview-content');
        if (!previewContent) return;

        // This would typically make an AJAX call to get the rendered preview
        // For now, we'll just show the test data
        previewContent.innerHTML = `
            <h4>Preview with Test Data</h4>
            <pre>${JSON.stringify(testData, null, 2)}</pre>
        `;
    }

    /**
     * Initialize preview tabs
     */
    initializePreviewTabs() {
        const previewTabs = document.querySelectorAll('.preview-tab');
        const previewContents = document.querySelectorAll('.preview-content');

        previewTabs.forEach(tab => {
            tab.addEventListener('click', () => {
                const target = tab.dataset.target;
                this.switchPreviewTab(target);
            });
        });
    }

    /**
     * Switch preview tab
     */
    switchPreviewTab(target) {
        // Update tab states
        document.querySelectorAll('.preview-tab').forEach(tab => {
            tab.classList.remove('active');
        });
        document.querySelector(`[data-target="${target}"]`).classList.add('active');

        // Update content visibility
        document.querySelectorAll('.preview-content').forEach(content => {
            content.style.display = 'none';
        });
        document.getElementById(target).style.display = 'block';
    }

    /**
     * Initialize auto-save functionality
     */
    initializeAutoSave() {
        const form = document.querySelector('form[method="post"]');
        if (!form) return;

        let autoSaveTimer;
        const autoSaveInterval = 30000; // 30 seconds

        const formInputs = form.querySelectorAll('input, textarea, select');
        formInputs.forEach(input => {
            input.addEventListener('input', () => {
                clearTimeout(autoSaveTimer);
                autoSaveTimer = setTimeout(() => {
                    this.autoSaveForm(form);
                }, autoSaveInterval);
            });
        });
    }

    /**
     * Auto-save form
     */
    async autoSaveForm(form) {
        const formData = new FormData(form);
        formData.append('auto_save', 'true');

        try {
            const response = await fetch(form.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': this.getCSRFToken()
                }
            });

            if (response.ok) {
                this.showAutoSaveNotification();
            }
        } catch (error) {
            console.error('Auto-save failed:', error);
        }
    }

    /**
     * Show auto-save notification
     */
    showAutoSaveNotification() {
        const notification = document.createElement('div');
        notification.className = 'alert alert-info alert-dismissible fade show position-fixed';
        notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        notification.innerHTML = `
            <i class="fas fa-save"></i> Template auto-saved
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        document.body.appendChild(notification);

        // Auto-remove after 3 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 3000);
    }

    /**
     * Initialize character counters
     */
    initializeCharacterCounters() {
        const contentField = document.getElementById('id_content');
        const htmlContentField = document.getElementById('id_html_content');

        if (contentField) {
            this.createCharacterCounter(contentField, 'content-counter');
        }

        if (htmlContentField) {
            this.createCharacterCounter(htmlContentField, 'html-counter');
        }
    }

    /**
     * Create character counter
     */
    createCharacterCounter(field, counterId) {
        const counter = document.createElement('div');
        counter.id = counterId;
        counter.className = 'form-text text-muted text-end';
        counter.style.marginTop = '0.25rem';

        field.parentNode.appendChild(counter);

        const updateCounter = () => {
            const count = field.value.length;
            const maxLength = field.maxLength || '∞';
            counter.textContent = `${count} characters`;
            
            if (field.maxLength && count > field.maxLength * 0.9) {
                counter.className = 'form-text text-warning text-end';
            } else {
                counter.className = 'form-text text-muted text-end';
            }
        };

        field.addEventListener('input', updateCounter);
        updateCounter();
    }

    /**
     * Handle form submission
     */
    handleFormSubmission(event) {
        const form = event.target;
        const submitBtn = form.querySelector('button[type="submit"]');
        
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';
        }

        // Validate form before submission
        if (!this.validateForm(form)) {
            event.preventDefault();
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.innerHTML = '<i class="fas fa-save"></i> Save Template';
            }
        }
    }

    /**
     * Validate form
     */
    validateForm(form) {
        let isValid = true;
        const requiredFields = form.querySelectorAll('[required]');

        requiredFields.forEach(field => {
            if (!field.value.trim()) {
                field.classList.add('is-invalid');
                isValid = false;
            } else {
                field.classList.remove('is-invalid');
            }
        });

        return isValid;
    }

    /**
     * Get CSRF token
     */
    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
    }

    /**
     * Update placeholder suggestions
     */
    updatePlaceholderSuggestions(templateType) {
        // This would typically make an AJAX call to get relevant placeholders
        // For now, we'll just show a message
        const placeholderHelper = document.querySelector('.placeholder-helper');
        if (placeholderHelper) {
            placeholderHelper.innerHTML = `
                <h6>Available Placeholders for ${templateType}</h6>
                <p>Loading placeholders...</p>
            `;
        }
    }

    /**
     * Update content validation
     */
    updateContentValidation(templateType) {
        const contentField = document.getElementById('id_content');
        const htmlContentField = document.getElementById('id_html_content');

        if (templateType === 'sms') {
            if (contentField) {
                contentField.maxLength = 160;
                contentField.placeholder = 'SMS content (max 160 characters)';
            }
        } else if (templateType === 'whatsapp') {
            if (contentField) {
                contentField.maxLength = 1000;
                contentField.placeholder = 'WhatsApp content (max 1000 characters)';
            }
        }

        // Update character counters
        this.initializeCharacterCounters();
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new NotificationTemplates();
});

// Export for use in other modules
window.NotificationTemplates = NotificationTemplates;
