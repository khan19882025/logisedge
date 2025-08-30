document.addEventListener('DOMContentLoaded', function() {
    // Get form elements
    const form = document.getElementById('templateForm');
    const subjectField = document.getElementById('id_subject');
    const contentField = document.getElementById('id_content');
    const arabicContentField = document.getElementById('id_arabic_content');
    const previewContent = document.getElementById('previewContent');
    const previewBtn = document.getElementById('previewBtn');

    // Sample employee data for preview
    const sampleEmployeeData = {
        '{{employee_name}}': 'John Doe',
        '{{designation}}': 'Software Engineer',
        '{{department}}': 'IT',
        '{{employee_id}}': 'EMP001',
        '{{date_of_joining}}': 'January 15, 2023',
        '{{salary}}': 'AED 8,000',
        '{{issue_date}}': new Date().toLocaleDateString('en-US', { 
            year: 'numeric', 
            month: 'long', 
            day: 'numeric' 
        }),
        '{{company_name}}': 'Your Company Name'
    };

    // Function to replace placeholders in text
    function replacePlaceholders(text) {
        if (!text) return '';
        let result = text;
        for (const [placeholder, value] of Object.entries(sampleEmployeeData)) {
            result = result.replace(new RegExp(placeholder.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'g'), value);
        }
        return result;
    }

    // Function to update preview
    function updatePreview() {
        const subject = subjectField ? subjectField.value : '';
        const content = contentField ? contentField.value : '';
        
        if (!subject && !content) {
            previewContent.innerHTML = 'Select a template type and enter content to see a preview here...';
            return;
        }

        let previewText = '';
        
        if (subject) {
            previewText += `<strong>Subject:</strong> ${replacePlaceholders(subject)}\n\n`;
        }
        
        if (content) {
            previewText += replacePlaceholders(content);
        }

        previewContent.innerHTML = previewText || 'No content to preview';
    }

    // Function to insert placeholder at cursor position
    function insertPlaceholder(placeholder, textarea) {
        const start = textarea.selectionStart;
        const end = textarea.selectionEnd;
        const text = textarea.value;
        
        textarea.value = text.substring(0, start) + placeholder + text.substring(end);
        textarea.selectionStart = textarea.selectionEnd = start + placeholder.length;
        textarea.focus();
        
        // Trigger input event to update preview
        textarea.dispatchEvent(new Event('input'));
    }

    // Add click handlers to placeholder items
    document.querySelectorAll('.placeholder-item').forEach(item => {
        item.addEventListener('click', function() {
            const placeholder = this.textContent;
            const activeTab = document.querySelector('.nav-tabs .nav-link.active');
            
            if (activeTab && activeTab.getAttribute('data-bs-target') === '#english') {
                // Insert into English content
                if (contentField) {
                    insertPlaceholder(placeholder, contentField);
                }
            } else {
                // Insert into Arabic content
                if (arabicContentField) {
                    insertPlaceholder(placeholder, arabicContentField);
                }
            }
        });
        
        // Add hover effect
        item.style.cursor = 'pointer';
        item.addEventListener('mouseenter', function() {
            this.style.backgroundColor = '#e9ecef';
        });
        item.addEventListener('mouseleave', function() {
            this.style.backgroundColor = 'white';
        });
    });

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

    // Add tooltips to placeholder items
    document.querySelectorAll('.placeholder-item').forEach(item => {
        item.title = `Click to insert "${item.textContent}" at cursor position`;
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