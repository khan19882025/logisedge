/**
 * Recruitment Management System JavaScript
 */

// Global variables
let currentApplicationId = null;
let currentInterviewId = null;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeRecruitmentSystem();
});

/**
 * Initialize all recruitment system functionality
 */
function initializeRecruitmentSystem() {
    initializeTooltips();
    initializeDatePickers();
    initializeFormValidation();
    initializeAJAXHandlers();
    initializePipelineDragDrop();
    initializeSearchFilters();
    initializeStatusUpdates();
    initializeFileUploads();
    initializeCharts();
}

/**
 * Initialize Bootstrap tooltips
 */
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Initialize date pickers using Flatpickr
 */
function initializeDatePickers() {
    // Date inputs
    const dateInputs = document.querySelectorAll('input[type="date"]');
    dateInputs.forEach(input => {
        flatpickr(input, {
            dateFormat: "Y-m-d",
            allowInput: true,
            clickOpens: true,
            locale: "en"
        });
    });

    // DateTime inputs
    const dateTimeInputs = document.querySelectorAll('input[type="datetime-local"]');
    dateTimeInputs.forEach(input => {
        flatpickr(input, {
            enableTime: true,
            dateFormat: "Y-m-d H:i",
            allowInput: true,
            clickOpens: true,
            locale: "en"
        });
    });
}

/**
 * Initialize form validation
 */
function initializeFormValidation() {
    const forms = document.querySelectorAll('.needs-validation');
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });

    // Custom validation for salary ranges
    const salaryMinInputs = document.querySelectorAll('input[name="salary_range_min"]');
    const salaryMaxInputs = document.querySelectorAll('input[name="salary_range_max"]');

    salaryMinInputs.forEach((minInput, index) => {
        const maxInput = salaryMaxInputs[index];
        if (minInput && maxInput) {
            minInput.addEventListener('change', () => validateSalaryRange(minInput, maxInput));
            maxInput.addEventListener('change', () => validateSalaryRange(minInput, maxInput));
        }
    });
}

/**
 * Validate salary range
 */
function validateSalaryRange(minInput, maxInput) {
    const minValue = parseFloat(minInput.value);
    const maxValue = parseFloat(maxInput.value);

    if (minValue && maxValue && minValue > maxValue) {
        minInput.setCustomValidity('Minimum salary cannot be greater than maximum salary');
        maxInput.setCustomValidity('Maximum salary cannot be less than minimum salary');
    } else {
        minInput.setCustomValidity('');
        maxInput.setCustomValidity('');
    }
}

/**
 * Initialize AJAX handlers
 */
function initializeAJAXHandlers() {
    // Application status updates
    const statusSelects = document.querySelectorAll('.application-status-select');
    statusSelects.forEach(select => {
        select.addEventListener('change', function() {
            updateApplicationStatus(this.dataset.applicationId, this.value);
        });
    });

    // Interview status updates
    const interviewStatusSelects = document.querySelectorAll('.interview-status-select');
    interviewStatusSelects.forEach(select => {
        select.addEventListener('change', function() {
            updateInterviewStatus(this.dataset.interviewId, this.value);
        });
    });

    // Dynamic form loading
    const dynamicForms = document.querySelectorAll('[data-dynamic-form]');
    dynamicForms.forEach(form => {
        form.addEventListener('change', function() {
            loadDynamicFormData(this);
        });
    });
}

/**
 * Update application status via AJAX
 */
function updateApplicationStatus(applicationId, newStatus) {
    const csrfToken = getCSRFToken();
    
    fetch(`/hr/recruitment/api/applications/${applicationId}/status/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': csrfToken
        },
        body: `status=${newStatus}`
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Status updated successfully!', 'success');
            updatePipelineDisplay();
        } else {
            showNotification('Failed to update status: ' + data.message, 'error');
        }
    })
    .catch(error => {
        console.error('Error updating application status:', error);
        showNotification('An error occurred while updating status', 'error');
    });
}

/**
 * Update interview status via AJAX
 */
function updateInterviewStatus(interviewId, newStatus) {
    const csrfToken = getCSRFToken();
    
    fetch(`/hr/recruitment/api/interviews/${interviewId}/status/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': csrfToken
        },
        body: `status=${newStatus}`
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Interview status updated successfully!', 'success');
        } else {
            showNotification('Failed to update interview status: ' + data.message, 'error');
        }
    })
    .catch(error => {
        console.error('Error updating interview status:', error);
        showNotification('An error occurred while updating interview status', 'error');
    });
}

/**
 * Load dynamic form data
 */
function loadDynamicFormData(element) {
    const formType = element.dataset.dynamicForm;
    const selectedValue = element.value;
    
    if (!selectedValue) return;

    const targetContainer = document.querySelector(`[data-dynamic-target="${formType}"]`);
    if (!targetContainer) return;

    targetContainer.innerHTML = '<div class="loading-spinner"></div> Loading...';

    fetch(`/hr/recruitment/api/${formType}/${selectedValue}/`, {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        targetContainer.innerHTML = data.html || 'No data available';
    })
    .catch(error => {
        console.error('Error loading dynamic form data:', error);
        targetContainer.innerHTML = 'Error loading data';
    });
}

/**
 * Initialize pipeline drag and drop functionality
 */
function initializePipelineDragDrop() {
    const pipelineItems = document.querySelectorAll('.pipeline-item');
    const pipelineColumns = document.querySelectorAll('.pipeline-column');

    pipelineItems.forEach(item => {
        item.setAttribute('draggable', true);
        item.addEventListener('dragstart', handleDragStart);
        item.addEventListener('dragend', handleDragEnd);
    });

    pipelineColumns.forEach(column => {
        column.addEventListener('dragover', handleDragOver);
        column.addEventListener('drop', handleDrop);
    });
}

/**
 * Handle drag start
 */
function handleDragStart(e) {
    e.target.classList.add('dragging');
    e.dataTransfer.setData('text/plain', e.target.dataset.applicationId);
}

/**
 * Handle drag end
 */
function handleDragEnd(e) {
    e.target.classList.remove('dragging');
}

/**
 * Handle drag over
 */
function handleDragOver(e) {
    e.preventDefault();
    e.currentTarget.classList.add('drag-over');
}

/**
 * Handle drop
 */
function handleDrop(e) {
    e.preventDefault();
    const applicationId = e.dataTransfer.getData('text/plain');
    const newStatus = e.currentTarget.dataset.status;
    
    e.currentTarget.classList.remove('drag-over');
    
    if (applicationId && newStatus) {
        updateApplicationStatus(applicationId, newStatus);
    }
}

/**
 * Initialize search filters
 */
function initializeSearchFilters() {
    const searchForm = document.getElementById('search-form');
    if (searchForm) {
        const inputs = searchForm.querySelectorAll('input, select');
        inputs.forEach(input => {
            input.addEventListener('change', debounce(() => {
                searchForm.submit();
            }, 500));
        });
    }

    // Clear filters button
    const clearFiltersBtn = document.querySelector('.clear-filters');
    if (clearFiltersBtn) {
        clearFiltersBtn.addEventListener('click', function() {
            const form = document.getElementById('search-form');
            form.reset();
            form.submit();
        });
    }
}

/**
 * Initialize status updates
 */
function initializeStatusUpdates() {
    // Auto-refresh status badges
    setInterval(() => {
        updateStatusCounts();
    }, 30000); // Update every 30 seconds
}

/**
 * Update status counts
 */
function updateStatusCounts() {
    fetch('/hr/recruitment/api/status-counts/', {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        Object.keys(data).forEach(status => {
            const badge = document.querySelector(`[data-status-count="${status}"]`);
            if (badge) {
                badge.textContent = data[status];
            }
        });
    })
    .catch(error => {
        console.error('Error updating status counts:', error);
    });
}

/**
 * Initialize file uploads
 */
function initializeFileUploads() {
    const fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(input => {
        input.addEventListener('change', function() {
            const fileName = this.files[0]?.name;
            const label = this.parentElement.querySelector('.file-label');
            if (label && fileName) {
                label.textContent = fileName;
            }
        });
    });

    // Drag and drop file upload
    const dropZones = document.querySelectorAll('.file-drop-zone');
    dropZones.forEach(zone => {
        zone.addEventListener('dragover', function(e) {
            e.preventDefault();
            this.classList.add('drag-over');
        });

        zone.addEventListener('dragleave', function(e) {
            e.preventDefault();
            this.classList.remove('drag-over');
        });

        zone.addEventListener('drop', function(e) {
            e.preventDefault();
            this.classList.remove('drag-over');
            
            const files = e.dataTransfer.files;
            const fileInput = this.querySelector('input[type="file"]');
            
            if (files.length > 0 && fileInput) {
                fileInput.files = files;
                fileInput.dispatchEvent(new Event('change'));
            }
        });
    });
}

/**
 * Initialize charts
 */
function initializeCharts() {
    // Pipeline chart
    const pipelineCtx = document.getElementById('pipeline-chart');
    if (pipelineCtx) {
        const pipelineData = JSON.parse(pipelineCtx.dataset.chartData);
        new Chart(pipelineCtx, {
            type: 'doughnut',
            data: {
                labels: pipelineData.labels,
                datasets: [{
                    data: pipelineData.values,
                    backgroundColor: [
                        '#36b9cc',
                        '#f6c23e',
                        '#1cc88a',
                        '#4e73df',
                        '#e74a3b',
                        '#858796'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }

    // Source analytics chart
    const sourceCtx = document.getElementById('source-chart');
    if (sourceCtx) {
        const sourceData = JSON.parse(sourceCtx.dataset.chartData);
        new Chart(sourceCtx, {
            type: 'bar',
            data: {
                labels: sourceData.labels,
                datasets: [{
                    label: 'Applications',
                    data: sourceData.values,
                    backgroundColor: '#4e73df'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }
}

/**
 * Update pipeline display
 */
function updatePipelineDisplay() {
    // Refresh pipeline data
    fetch('/hr/recruitment/api/pipeline-data/', {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        Object.keys(data).forEach(status => {
            const column = document.querySelector(`[data-pipeline-column="${status}"]`);
            if (column) {
                const content = column.querySelector('.pipeline-content');
                content.innerHTML = data[status].html;
            }
        });
    })
    .catch(error => {
        console.error('Error updating pipeline display:', error);
    });
}

/**
 * Show notification
 */
function showNotification(message, type = 'info') {
    const alertClass = type === 'success' ? 'alert-success' : 
                      type === 'error' ? 'alert-danger' : 
                      type === 'warning' ? 'alert-warning' : 'alert-info';
    
    const alertHtml = `
        <div class="alert ${alertClass} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    const container = document.querySelector('.notifications-container') || document.body;
    const alertElement = document.createElement('div');
    alertElement.innerHTML = alertHtml;
    container.appendChild(alertElement.firstElementChild);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        const alert = container.querySelector('.alert');
        if (alert) {
            alert.remove();
        }
    }, 5000);
}

/**
 * Get CSRF token
 */
function getCSRFToken() {
    const token = document.querySelector('meta[name="csrf-token"]');
    return token ? token.getAttribute('content') : '';
}

/**
 * Debounce function
 */
function debounce(func, wait) {
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

/**
 * Format currency
 */
function formatCurrency(amount, currency = 'AED') {
    return new Intl.NumberFormat('en-AE', {
        style: 'currency',
        currency: currency
    }).format(amount);
}

/**
 * Format date
 */
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-AE', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

/**
 * Format datetime
 */
function formatDateTime(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString('en-AE', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

/**
 * Export data to CSV
 */
function exportToCSV(data, filename) {
    const csvContent = "data:text/csv;charset=utf-8," + data;
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", filename);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

/**
 * Print element
 */
function printElement(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        const printWindow = window.open('', '_blank');
        printWindow.document.write(`
            <html>
                <head>
                    <title>Print</title>
                    <link rel="stylesheet" href="/static/css/recruitment/recruitment.css">
                </head>
                <body>
                    ${element.outerHTML}
                </body>
            </html>
        `);
        printWindow.document.close();
        printWindow.print();
    }
}

/**
 * Confirm action
 */
function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

/**
 * Show loading spinner
 */
function showLoading(element) {
    element.innerHTML = '<div class="loading-spinner"></div> Loading...';
    element.disabled = true;
}

/**
 * Hide loading spinner
 */
function hideLoading(element, originalContent) {
    element.innerHTML = originalContent;
    element.disabled = false;
}

// Export functions for global use
window.RecruitmentSystem = {
    updateApplicationStatus,
    updateInterviewStatus,
    showNotification,
    formatCurrency,
    formatDate,
    formatDateTime,
    exportToCSV,
    printElement,
    confirmAction,
    showLoading,
    hideLoading
}; 