/**
 * Master Data Import Upload JavaScript
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize upload functionality
    initializeUpload();
});

function initializeUpload() {
    // Setup drag and drop functionality
    setupDragAndDrop();
    
    // Setup file input change handler
    setupFileInput();
    
    // Setup template selection handler
    setupTemplateSelection();
    
    // Setup form validation
    setupFormValidation();
    
    // Setup form submission
    setupFormSubmission();
}

function setupDragAndDrop() {
    const uploadArea = document.getElementById('file-upload-area');
    const fileInput = document.getElementById('import-file');
    
    if (!uploadArea || !fileInput) return;
    
    // Prevent default drag behaviors
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, preventDefaults, false);
        document.body.addEventListener(eventName, preventDefaults, false);
    });
    
    // Highlight drop area when item is dragged over it
    ['dragenter', 'dragover'].forEach(eventName => {
        uploadArea.addEventListener(eventName, highlight, false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, unhighlight, false);
    });
    
    // Handle dropped files
    uploadArea.addEventListener('drop', handleDrop, false);
    
    // Handle click to browse
    uploadArea.addEventListener('click', () => fileInput.click());
}

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

function highlight(e) {
    const uploadArea = document.getElementById('file-upload-area');
    uploadArea.classList.add('dragover');
}

function unhighlight(e) {
    const uploadArea = document.getElementById('file-upload-area');
    uploadArea.classList.remove('dragover');
}

function handleDrop(e) {
    const dt = e.dataTransfer;
    const files = dt.files;
    
    if (files.length > 0) {
        const fileInput = document.getElementById('import-file');
        fileInput.files = files;
        handleFileSelect(files[0]);
    }
}

function setupFileInput() {
    const fileInput = document.getElementById('import-file');
    
    if (fileInput) {
        fileInput.addEventListener('change', function(e) {
            if (e.target.files.length > 0) {
                handleFileSelect(e.target.files[0]);
            }
        });
    }
}

function handleFileSelect(file) {
    const uploadArea = document.getElementById('file-upload-area');
    const fileInfo = createFileInfo(file);
    
    // Update upload area
    uploadArea.classList.add('has-file');
    uploadArea.innerHTML = fileInfo;
    
    // Validate file
    validateFile(file);
}

function createFileInfo(file) {
    const fileSize = formatFileSize(file.size);
    const fileType = getFileTypeIcon(file.name);
    
    return `
        <div class="file-info show">
            <div class="file-info-icon">
                <i class="fas ${fileType.icon} ${fileType.color}"></i>
            </div>
            <div class="file-info-name">${file.name}</div>
            <div class="file-info-size">${fileSize}</div>
        </div>
    `;
}

function getFileTypeIcon(filename) {
    const extension = filename.split('.').pop().toLowerCase();
    
    switch (extension) {
        case 'csv':
            return { icon: 'fa-file-csv', color: 'file-type-csv' };
        case 'xlsx':
        case 'xls':
            return { icon: 'fa-file-excel', color: 'file-type-excel' };
        default:
            return { icon: 'fa-file', color: 'text-muted' };
    }
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function validateFile(file) {
    const allowedTypes = ['.csv', '.xlsx', '.xls'];
    const maxSize = 50 * 1024 * 1024; // 50MB
    
    const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
    
    if (!allowedTypes.includes(fileExtension)) {
        showError('Invalid file type. Please upload a CSV or Excel file.');
        return false;
    }
    
    if (file.size > maxSize) {
        showError('File size too large. Maximum size is 50MB.');
        return false;
    }
    
    return true;
}

function setupTemplateSelection() {
    const templateSelect = document.getElementById('template-select');
    const templateInfo = document.getElementById('template-info');
    const templateDetails = document.getElementById('template-details');
    
    if (templateSelect) {
        templateSelect.addEventListener('change', function() {
            const selectedOption = this.options[this.selectedIndex];
            const templateId = selectedOption.value;
            
            if (templateId) {
                loadTemplateInfo(templateId, templateInfo, templateDetails);
            } else {
                templateInfo.style.display = 'none';
            }
        });
    }
}

function loadTemplateInfo(templateId, templateInfo, templateDetails) {
    // In a real implementation, you would fetch template details via AJAX
    // For now, we'll show a placeholder
    templateDetails.innerHTML = `
        <div class="row">
            <div class="col-md-6">
                <strong>Data Type:</strong> <span id="template-data-type">Loading...</span><br>
                <strong>Required Fields:</strong> <span id="template-required-fields">Loading...</span>
            </div>
            <div class="col-md-6">
                <strong>Validation Rules:</strong> <span id="template-validation-rules">Loading...</span><br>
                <strong>Sample Format:</strong> <a href="#" id="download-template">Download Template</a>
            </div>
        </div>
    `;
    
    templateInfo.style.display = 'block';
    
    // Fetch actual template data
    fetchTemplateData(templateId);
}

function fetchTemplateData(templateId) {
    // This would be an AJAX call to get template details
    // For now, we'll simulate the response
    setTimeout(() => {
        document.getElementById('template-data-type').textContent = 'Customers';
        document.getElementById('template-required-fields').textContent = 'Name, Email, Phone';
        document.getElementById('template-validation-rules').textContent = 'Email format, Phone format';
        
        const downloadLink = document.getElementById('download-template');
        downloadLink.href = `/master-data-import/templates/${templateId}/download/`;
    }, 500);
}

function setupFormValidation() {
    const form = document.getElementById('upload-form');
    
    if (form) {
        form.addEventListener('submit', function(e) {
            if (!validateForm()) {
                e.preventDefault();
            }
        });
    }
}

function validateForm() {
    const template = document.getElementById('template-select').value;
    const file = document.getElementById('import-file').files[0];
    const jobName = document.getElementById('job-name').value.trim();
    
    let isValid = true;
    
    // Clear previous errors
    clearErrors();
    
    // Validate template selection
    if (!template) {
        showFieldError('template-select', 'Please select a template');
        isValid = false;
    }
    
    // Validate file selection
    if (!file) {
        showFieldError('import-file', 'Please select a file to upload');
        isValid = false;
    } else if (!validateFile(file)) {
        isValid = false;
    }
    
    // Validate job name
    if (!jobName) {
        showFieldError('job-name', 'Please enter a job name');
        isValid = false;
    } else if (jobName.length < 3) {
        showFieldError('job-name', 'Job name must be at least 3 characters long');
        isValid = false;
    }
    
    return isValid;
}

function showFieldError(fieldId, message) {
    const field = document.getElementById(fieldId);
    if (field) {
        field.classList.add('is-invalid');
        
        // Create error message element
        const errorDiv = document.createElement('div');
        errorDiv.className = 'invalid-feedback';
        errorDiv.textContent = message;
        
        // Insert after the field
        field.parentNode.appendChild(errorDiv);
    }
}

function clearErrors() {
    // Remove all error states
    document.querySelectorAll('.is-invalid').forEach(field => {
        field.classList.remove('is-invalid');
    });
    
    // Remove all error messages
    document.querySelectorAll('.invalid-feedback').forEach(error => {
        error.remove();
    });
}

function showError(message) {
    // Create error alert
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-danger alert-dismissible fade show';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // Insert at the top of the form
    const form = document.getElementById('upload-form');
    form.insertBefore(alertDiv, form.firstChild);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}

function setupFormSubmission() {
    const form = document.getElementById('upload-form');
    const submitBtn = document.getElementById('submit-btn');
    
    if (form && submitBtn) {
        form.addEventListener('submit', function(e) {
            if (validateForm()) {
                // Show loading state
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Uploading...';
                
                // Form will submit normally
            }
        });
    }
}

// Export functions for use in other modules
window.UploadModule = {
    validateFile,
    formatFileSize,
    showError,
    clearErrors
};
