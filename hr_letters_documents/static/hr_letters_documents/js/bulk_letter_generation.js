// HR Letters & Documents - Bulk Letter Generation JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Form elements
    const letterTypeSelect = document.getElementById('id_letter_type');
    const templateSelect = document.getElementById('id_template');
    const selectAllCheckbox = document.getElementById('selectAllEmployees');
    const employeeCheckboxes = document.querySelectorAll('.employee-checkbox');
    const previewEmployeeSelect = document.getElementById('previewEmployee');
    const previewBtn = document.getElementById('previewBtn');
    const generateBtn = document.getElementById('generateBtn');
    const form = document.getElementById('bulkLetterForm');
    
    // Content areas
    const englishSubject = document.getElementById('id_english_subject');
    const englishContent = document.getElementById('id_english_content');
    const arabicSubject = document.getElementById('id_arabic_subject');
    const arabicContent = document.getElementById('id_arabic_content');
    const templatePreview = document.getElementById('templatePreview');
    const templateContent = document.getElementById('templateContent');
    const placeholderList = document.getElementById('placeholderList');
    const letterPreview = document.getElementById('letterPreview');
    const statusMessage = document.getElementById('statusMessage');
    const progressBar = document.querySelector('.progress-bar');
    
    // Event listeners
    if (letterTypeSelect) {
        letterTypeSelect.addEventListener('change', loadTemplatesForLetterType);
    }
    
    if (templateSelect) {
        templateSelect.addEventListener('change', loadTemplateContent);
    }
    
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', toggleAllEmployees);
    }
    
    if (previewEmployeeSelect) {
        previewEmployeeSelect.addEventListener('change', loadLetterPreview);
    }
    
    if (previewBtn) {
        previewBtn.addEventListener('click', previewAllLetters);
    }
    
    if (form) {
        form.addEventListener('submit', handleFormSubmission);
    }
    
    // Initialize
    updatePreviewEmployeeOptions();
    
    // Functions
    function loadTemplatesForLetterType() {
        const letterTypeId = letterTypeSelect.value;
        if (!letterTypeId) {
            templateSelect.innerHTML = '<option value="">Select Template</option>';
            templatePreview.style.display = 'none';
            return;
        }
        
        // Show loading state
        templateSelect.innerHTML = '<option value="">Loading templates...</option>';
        
        fetch(`{% url 'hr_letters_documents:get_templates_for_letter_type' %}?letter_type=${letterTypeId}`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    templateSelect.innerHTML = '<option value="">Select Template</option>';
                    data.templates.forEach(template => {
                        const option = document.createElement('option');
                        option.value = template.id;
                        option.textContent = template.title;
                        templateSelect.appendChild(option);
                    });
                } else {
                    templateSelect.innerHTML = '<option value="">No templates found</option>';
                }
            })
            .catch(error => {
                console.error('Error loading templates:', error);
                templateSelect.innerHTML = '<option value="">Error loading templates</option>';
            });
    }
    
    function loadTemplateContent() {
        const templateId = templateSelect.value;
        if (!templateId) {
            templatePreview.style.display = 'none';
            return;
        }
        
        // Show loading state
        templateContent.innerHTML = '<p class="text-muted">Loading template...</p>';
        templatePreview.style.display = 'block';
        
        fetch(`{% url 'hr_letters_documents:get_template_details' %}?template_id=${templateId}`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Display template content
                    templateContent.innerHTML = `
                        <div class="mb-3">
                            <strong>Template Name:</strong>
                            <p>${data.template.name || 'Not specified'}</p>
                        </div>
                        <div class="mb-3">
                            <strong>English Subject:</strong>
                            <p>${data.template.english_subject || 'Not specified'}</p>
                        </div>
                        <div class="mb-3">
                            <strong>English Content:</strong>
                            <div style="white-space: pre-wrap;">${data.template.english_content || 'Not specified'}</div>
                        </div>
                        <div class="mb-3">
                            <strong>Arabic Subject:</strong>
                            <p>${data.template.arabic_subject || 'Not specified'}</p>
                        </div>
                        <div class="mb-3">
                            <strong>Arabic Content:</strong>
                            <div style="white-space: pre-wrap; direction: rtl;">${data.template.arabic_content || 'Not specified'}</div>
                        </div>
                    `;
                    
                    // Populate form fields with template content
                    englishSubject.value = data.template.english_subject || '';
                    englishContent.value = data.template.english_content || '';
                    arabicSubject.value = data.template.arabic_subject || '';
                    arabicContent.value = data.template.arabic_content || '';
                    
                    // Extract and display placeholders
                    displayPlaceholders(data.template.english_content + ' ' + data.template.arabic_content);
                } else {
                    templateContent.innerHTML = '<p class="text-danger">Error loading template</p>';
                }
            })
            .catch(error => {
                console.error('Error loading template content:', error);
                templateContent.innerHTML = '<p class="text-danger">Error loading template</p>';
            });
    }
    
    function displayPlaceholders(content) {
        const placeholders = extractPlaceholders(content);
        placeholderList.innerHTML = '';
        
        if (placeholders.length === 0) {
            placeholderList.innerHTML = '<li class="text-muted">No placeholders found</li>';
            return;
        }
        
        placeholders.forEach(placeholder => {
            const li = document.createElement('li');
            li.className = 'placeholder-item';
            li.textContent = placeholder;
            placeholderList.appendChild(li);
        });
    }
    
    function extractPlaceholders(content) {
        const placeholderRegex = /\{\{([^}]+)\}\}/g;
        const placeholders = [];
        let match;
        
        while ((match = placeholderRegex.exec(content)) !== null) {
            if (!placeholders.includes(match[1])) {
                placeholders.push(match[1]);
            }
        }
        
        return placeholders;
    }
    
    function toggleAllEmployees() {
        const isChecked = selectAllCheckbox.checked;
        employeeCheckboxes.forEach(checkbox => {
            checkbox.checked = isChecked;
        });
        updatePreviewEmployeeOptions();
    }
    
    function updatePreviewEmployeeOptions() {
        const selectedEmployees = Array.from(employeeCheckboxes)
            .filter(checkbox => checkbox.checked)
            .map(checkbox => ({
                id: checkbox.value,
                name: checkbox.closest('.employee-item').querySelector('.employee-name').textContent
            }));
        
        previewEmployeeSelect.innerHTML = '<option value="">Select Employee</option>';
        selectedEmployees.forEach(employee => {
            const option = document.createElement('option');
            option.value = employee.id;
            option.textContent = employee.name;
            previewEmployeeSelect.appendChild(option);
        });
    }
    
    function loadLetterPreview() {
        const employeeId = previewEmployeeSelect.value;
        if (!employeeId) {
            letterPreview.style.display = 'none';
            return;
        }
        
        // Show loading state
        letterPreview.innerHTML = '<p class="text-muted">Loading preview...</p>';
        letterPreview.style.display = 'block';
        
        const formData = new FormData();
        formData.append('employee_id', employeeId);
        formData.append('english_subject', englishSubject.value);
        formData.append('english_content', englishContent.value);
        formData.append('arabic_subject', arabicSubject.value);
        formData.append('arabic_content', arabicContent.value);
        
        fetch('{% url "hr_letters_documents:preview_letter" %}', {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                letterPreview.innerHTML = `
                    <div class="mb-3">
                        <strong>Subject:</strong>
                        <p>${data.preview.subject}</p>
                    </div>
                    <div class="mb-3">
                        <strong>Content:</strong>
                        <div style="white-space: pre-wrap;">${data.preview.content}</div>
                    </div>
                    ${data.preview.arabic_content ? `
                        <div class="mb-3">
                            <strong>Arabic Content:</strong>
                            <div style="white-space: pre-wrap; direction: rtl;">${data.preview.arabic_content}</div>
                        </div>
                    ` : ''}
                `;
            } else {
                letterPreview.innerHTML = '<p class="text-danger">Error generating preview</p>';
            }
        })
        .catch(error => {
            console.error('Error loading preview:', error);
            letterPreview.innerHTML = '<p class="text-danger">Error generating preview</p>';
        });
    }
    
    function previewAllLetters() {
        const selectedEmployees = Array.from(employeeCheckboxes)
            .filter(checkbox => checkbox.checked);
        
        if (selectedEmployees.length === 0) {
            showAlert('Please select at least one employee to preview letters.', 'warning');
            return;
        }
        
        if (!letterTypeSelect.value || !templateSelect.value) {
            showAlert('Please select a letter type and template.', 'warning');
            return;
        }
        
        // Show preview modal or redirect to preview page
        showAlert(`Previewing letters for ${selectedEmployees.length} employee(s)...`, 'info');
    }
    
    function handleFormSubmission(event) {
        event.preventDefault();
        
        const selectedEmployees = Array.from(employeeCheckboxes)
            .filter(checkbox => checkbox.checked);
        
        if (selectedEmployees.length === 0) {
            showAlert('Please select at least one employee to generate letters.', 'warning');
            return;
        }
        
        if (!letterTypeSelect.value || !templateSelect.value) {
            showAlert('Please select a letter type and template.', 'warning');
            return;
        }
        
        // Show confirmation dialog
        if (!confirm(`Are you sure you want to generate letters for ${selectedEmployees.length} employee(s)?`)) {
            return;
        }
        
        // Disable form and show progress
        generateBtn.disabled = true;
        generateBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Generating...';
        updateProgress(0, 'Starting generation...');
        
        // Submit form
        const formData = new FormData(form);
        
        fetch(form.action, {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateProgress(100, `Successfully generated ${data.generated_count} letters!`);
                showAlert(`Successfully generated ${data.generated_count} letters!`, 'success');
                
                // Redirect to letters list after a short delay
                setTimeout(() => {
                    window.location.href = '{% url "hr_letters_documents:letter_list" %}';
                }, 2000);
            } else {
                updateProgress(0, 'Generation failed');
                showAlert(data.message || 'Error generating letters', 'danger');
                generateBtn.disabled = false;
                generateBtn.innerHTML = '<i class="fas fa-magic me-2"></i>Generate Letters';
            }
        })
        .catch(error => {
            console.error('Error submitting form:', error);
            updateProgress(0, 'Generation failed');
            showAlert('Error generating letters. Please try again.', 'danger');
            generateBtn.disabled = false;
            generateBtn.innerHTML = '<i class="fas fa-magic me-2"></i>Generate Letters';
        });
    }
    
    function updateProgress(percentage, message) {
        progressBar.style.width = percentage + '%';
        statusMessage.textContent = message;
        
        if (percentage === 100) {
            progressBar.classList.add('bg-success');
        } else if (percentage > 0) {
            progressBar.classList.add('bg-primary');
        }
    }
    
    function showAlert(message, type) {
        // Create alert element
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        // Insert at the top of the form
        form.insertBefore(alertDiv, form.firstChild);
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    }
    
    // Add event listeners for employee checkboxes
    employeeCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', updatePreviewEmployeeOptions);
    });
    
    // Auto-save functionality
    let autoSaveTimer;
    const autoSaveElements = [englishSubject, englishContent, arabicSubject, arabicContent];
    
    autoSaveElements.forEach(element => {
        element.addEventListener('input', () => {
            clearTimeout(autoSaveTimer);
            autoSaveTimer = setTimeout(autoSaveForm, 2000);
        });
    });
    
    function autoSaveForm() {
        const formData = new FormData(form);
        formData.append('auto_save', 'true');
        
        fetch(form.action, {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                console.log('Form auto-saved successfully');
            }
        })
        .catch(error => {
            console.error('Auto-save failed:', error);
        });
    }
    
    // Keyboard shortcuts
    document.addEventListener('keydown', function(event) {
        // Ctrl/Cmd + S to save
        if ((event.ctrlKey || event.metaKey) && event.key === 's') {
            event.preventDefault();
            previewAllLetters();
        }
        
        // Ctrl/Cmd + Enter to generate
        if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
            event.preventDefault();
            if (!generateBtn.disabled) {
                generateBtn.click();
            }
        }
    });
    
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}); 