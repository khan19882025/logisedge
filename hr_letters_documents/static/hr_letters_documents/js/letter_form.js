// HR Letters & Documents - Letter Form JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Get form elements
    const form = document.getElementById('letterForm');
    const letterTypeSelect = document.getElementById('id_letter_type');
    const templateSelect = document.getElementById('id_template');
    const employeeSelect = document.getElementById('id_employee');
    const subjectField = document.getElementById('id_subject');
    const contentField = document.getElementById('id_content');
    const arabicContentField = document.getElementById('id_arabic_content');
    const previewContent = document.getElementById('previewContent');
    const employeeInfo = document.getElementById('employeeInfo');
    const previewBtn = document.getElementById('previewBtn');

    // Employee data cache
    let employeeData = {};
    let templateData = {};

    // Function to load templates for selected letter type
    function loadTemplates(letterTypeId) {
        if (!letterTypeId) {
            templateSelect.innerHTML = '<option value="">Select a letter type first</option>';
            return;
        }

        fetch(`{% url 'hr_letters_documents:get_templates_for_letter_type' %}?letter_type=${letterTypeId}`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    templateSelect.innerHTML = '<option value="">Select a template</option>';
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

    // Function to load template details
    function loadTemplateDetails(templateId) {
        if (!templateId) return;

        fetch(`{% url 'hr_letters_documents:get_template_details' %}?template_id=${templateId}`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    templateData = data.template;
                    
                    // Auto-fill subject and content if they're empty
                    if (!subjectField.value && data.template.english_subject) {
                        subjectField.value = data.template.english_subject;
                    }
                    if (!contentField.value && data.template.english_content) {
                        contentField.value = data.template.english_content;
                    }
                    if (!arabicContentField.value && data.template.arabic_content) {
                        arabicContentField.value = data.template.arabic_content;
                    }
                    
                    updatePreview();
                }
            })
            .catch(error => {
                console.error('Error loading template details:', error);
            });
    }

    // Function to load employee details
    function loadEmployeeDetails(employeeId) {
        if (!employeeId) {
            employeeInfo.innerHTML = 'Select an employee to see their information here...';
            return;
        }

        if (employeeData[employeeId]) {
            displayEmployeeInfo(employeeData[employeeId]);
            return;
        }

        fetch(`{% url 'hr_letters_documents:get_employee_details' %}?employee_id=${employeeId}`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    employeeData[employeeId] = data.employee;
                    displayEmployeeInfo(data.employee);
                } else {
                    employeeInfo.innerHTML = 'Error loading employee information';
                }
            })
            .catch(error => {
                console.error('Error loading employee details:', error);
                employeeInfo.innerHTML = 'Error loading employee information';
            });
    }

    // Function to display employee information
    function displayEmployeeInfo(employee) {
        employeeInfo.innerHTML = `
            <div><strong>Name:</strong> ${employee.first_name} ${employee.last_name}</div>
            <div><strong>Designation:</strong> ${employee.designation || 'N/A'}</div>
            <div><strong>Department:</strong> ${employee.department || 'N/A'}</div>
            <div><strong>Employee ID:</strong> ${employee.employee_id || 'N/A'}</div>
            <div><strong>Date of Joining:</strong> ${employee.date_of_joining || 'N/A'}</div>
            <div><strong>Salary:</strong> ${employee.salary ? `AED ${employee.salary.toLocaleString()}` : 'N/A'}</div>
        `;
    }

    // Function to replace placeholders in text
    function replacePlaceholders(text, employee) {
        if (!text || !employee) return text;
        
        const placeholders = {
            '{{employee_name}}': `${employee.first_name} ${employee.last_name}`,
            '{{designation}}': employee.designation || 'N/A',
            '{{department}}': employee.department || 'N/A',
            '{{employee_id}}': employee.employee_id || 'N/A',
            '{{date_of_joining}}': employee.date_of_joining || 'N/A',
            '{{salary}}': employee.salary ? `AED ${employee.salary.toLocaleString()}` : 'N/A',
            '{{issue_date}}': new Date().toLocaleDateString('en-US', { 
                year: 'numeric', 
                month: 'long', 
                day: 'numeric' 
            }),
            '{{company_name}}': 'Your Company Name',
        };
        
        let result = text;
        for (const [placeholder, value] of Object.entries(placeholders)) {
            result = result.replace(new RegExp(placeholder.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'g'), value);
        }
        return result;
    }

    // Function to update preview
    function updatePreview() {
        const subject = subjectField ? subjectField.value : '';
        const content = contentField ? contentField.value : '';
        const employeeId = employeeSelect ? employeeSelect.value : '';
        const employee = employeeData[employeeId];
        
        if (!subject && !content) {
            previewContent.innerHTML = 'Select a template and enter content to see a preview here...';
            return;
        }

        let previewText = '';
        
        if (subject) {
            const processedSubject = employee ? replacePlaceholders(subject, employee) : subject;
            previewText += `<strong>Subject:</strong> ${processedSubject}\n\n`;
        }
        
        if (content) {
            const processedContent = employee ? replacePlaceholders(content, employee) : content;
            previewText += processedContent;
        }

        previewContent.innerHTML = previewText || 'No content to preview';
    }

    // Event listeners
    if (letterTypeSelect) {
        letterTypeSelect.addEventListener('change', function() {
            loadTemplates(this.value);
            // Clear template selection when letter type changes
            templateSelect.value = '';
            updatePreview();
        });
    }

    if (templateSelect) {
        templateSelect.addEventListener('change', function() {
            loadTemplateDetails(this.value);
        });
    }

    if (employeeSelect) {
        employeeSelect.addEventListener('change', function() {
            loadEmployeeDetails(this.value);
            updatePreview();
        });
    }

    // Add input event listeners for real-time preview
    if (subjectField) {
        subjectField.addEventListener('input', updatePreview);
    }
    if (contentField) {
        contentField.addEventListener('input', updatePreview);
    }

    // Tab switching functionality
    const tabButtons = document.querySelectorAll('.nav-tabs .nav-link');
    tabButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Remove active class from all tabs
            tabButtons.forEach(btn => btn.classList.remove('active'));
            document.querySelectorAll('.tab-pane').forEach(pane => {
                pane.classList.remove('show', 'active');
            });
            
            // Add active class to clicked tab
            this.classList.add('active');
            const targetId = this.getAttribute('data-bs-target');
            const targetPane = document.querySelector(targetId);
            if (targetPane) {
                targetPane.classList.add('show', 'active');
            }
        });
    });

    // Preview button functionality
    if (previewBtn) {
        previewBtn.addEventListener('click', function() {
            updatePreview();
            
            // Scroll to preview section
            document.querySelector('.preview-section').scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        });
    }

    // Form validation
    if (form) {
        form.addEventListener('submit', function(e) {
            const requiredFields = form.querySelectorAll('[required]');
            let isValid = true;
            
            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    isValid = false;
                    field.classList.add('is-invalid');
                    
                    // Show error message
                    let errorDiv = field.parentNode.querySelector('.text-danger');
                    if (!errorDiv) {
                        errorDiv = document.createElement('div');
                        errorDiv.className = 'text-danger small';
                        field.parentNode.appendChild(errorDiv);
                    }
                    errorDiv.textContent = 'This field is required.';
                } else {
                    field.classList.remove('is-invalid');
                    const errorDiv = field.parentNode.querySelector('.text-danger');
                    if (errorDiv) {
                        errorDiv.remove();
                    }
                }
            });
            
            if (!isValid) {
                e.preventDefault();
                
                // Show alert
                const alertDiv = document.createElement('div');
                alertDiv.className = 'alert alert-danger alert-dismissible fade show';
                alertDiv.innerHTML = `
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    Please fill in all required fields.
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                `;
                
                const formHeader = form.querySelector('.form-section:first-child');
                if (formHeader) {
                    formHeader.parentNode.insertBefore(alertDiv, formHeader);
                }
                
                // Auto-remove alert after 5 seconds
                setTimeout(() => {
                    if (alertDiv.parentNode) {
                        alertDiv.remove();
                    }
                }, 5000);
            }
        });
    }

    // Auto-save functionality (every 30 seconds)
    let autoSaveTimer;
    function startAutoSave() {
        autoSaveTimer = setInterval(() => {
            if (form && form.checkValidity()) {
                // Create form data
                const formData = new FormData(form);
                formData.append('auto_save', 'true');
                
                // Send auto-save request
                fetch(window.location.href, {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Show subtle auto-save indicator
                        showAutoSaveIndicator();
                    }
                })
                .catch(error => {
                    console.log('Auto-save failed:', error);
                });
            }
        }, 30000); // 30 seconds
    }

    function showAutoSaveIndicator() {
        // Create or update auto-save indicator
        let indicator = document.getElementById('autoSaveIndicator');
        if (!indicator) {
            indicator = document.createElement('div');
            indicator.id = 'autoSaveIndicator';
            indicator.className = 'position-fixed bottom-0 end-0 m-3';
            indicator.style.zIndex = '1050';
            document.body.appendChild(indicator);
        }
        
        indicator.innerHTML = `
            <div class="alert alert-success alert-dismissible fade show" style="min-width: 200px;">
                <i class="fas fa-save me-2"></i>
                Auto-saved
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        // Auto-remove after 3 seconds
        setTimeout(() => {
            if (indicator.parentNode) {
                indicator.remove();
            }
        }, 3000);
    }

    // Start auto-save when form is loaded
    if (form) {
        startAutoSave();
        
        // Stop auto-save when form is submitted
        form.addEventListener('submit', () => {
            clearInterval(autoSaveTimer);
        });
    }

    // Character counter for text areas
    function addCharacterCounter(textarea, maxLength = 5000) {
        const counter = document.createElement('div');
        counter.className = 'form-text text-end';
        counter.id = textarea.id + '_counter';
        
        function updateCounter() {
            const count = textarea.value.length;
            counter.textContent = `${count}/${maxLength} characters`;
            
            if (count > maxLength * 0.9) {
                counter.className = 'form-text text-end text-warning';
            } else if (count > maxLength) {
                counter.className = 'form-text text-end text-danger';
            } else {
                counter.className = 'form-text text-end';
            }
        }
        
        textarea.addEventListener('input', updateCounter);
        textarea.parentNode.appendChild(counter);
        updateCounter();
    }

    // Add character counters to text areas
    if (contentField) {
        addCharacterCounter(contentField, 10000);
    }
    if (arabicContentField) {
        addCharacterCounter(arabicContentField, 10000);
    }

    // Initialize preview on page load
    updatePreview();

    // Add keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + S to save
        if ((e.ctrlKey || e.metaKey) && e.key === 's') {
            e.preventDefault();
            if (form) {
                form.dispatchEvent(new Event('submit'));
            }
        }
        
        // Ctrl/Cmd + Enter to submit
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            e.preventDefault();
            if (form) {
                form.dispatchEvent(new Event('submit'));
            }
        }
    });

    // Add loading state to submit button
    if (form) {
        form.addEventListener('submit', function() {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Saving...';
            }
        });
    }
}); 