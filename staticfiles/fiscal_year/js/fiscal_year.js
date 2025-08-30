// Fiscal Year Settings JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize date pickers
    initializeDatePickers();
    
    // Initialize form validation
    initializeFormValidation();
    
    // Initialize AJAX functionality
    initializeAjaxHandlers();
    
    // Initialize search functionality
    initializeSearchFunctionality();
    
    // Initialize table sorting
    initializeTableSorting();
});

// Date Picker Initialization
function initializeDatePickers() {
    const dateInputs = document.querySelectorAll('input[type="date"]');
    dateInputs.forEach(input => {
        // Set default date to today if no value
        if (!input.value) {
            const today = new Date().toISOString().split('T')[0];
            input.value = today;
        }
        
        // Add change event listener for date validation
        input.addEventListener('change', function() {
            validateDateRange(this);
        });
    });
}

// Date Range Validation
function validateDateRange(dateInput) {
    const form = dateInput.closest('form');
    const startDateInput = form.querySelector('input[name="start_date"]');
    const endDateInput = form.querySelector('input[name="end_date"]');
    
    if (startDateInput && endDateInput && startDateInput.value && endDateInput.value) {
        const startDate = new Date(startDateInput.value);
        const endDate = new Date(endDateInput.value);
        
        if (startDate >= endDate) {
            showAlert('End date must be after start date', 'error');
            endDateInput.value = '';
            endDateInput.focus();
        }
    }
}

// Form Validation
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
}

// AJAX Handlers
function initializeAjaxHandlers() {
    // Toggle fiscal year status
    const toggleButtons = document.querySelectorAll('.toggle-fiscal-year-status');
    toggleButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const fiscalYearId = this.dataset.fiscalYearId;
            toggleFiscalYearStatus(fiscalYearId, this);
        });
    });
    
    // Toggle period status
    const togglePeriodButtons = document.querySelectorAll('.toggle-period-status');
    togglePeriodButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const periodId = this.dataset.periodId;
            togglePeriodStatus(periodId, this);
        });
    });
}

// Toggle Fiscal Year Status
function toggleFiscalYearStatus(fiscalYearId, button) {
    const originalText = button.innerHTML;
    button.innerHTML = '<i class="bi bi-hourglass-split"></i> Updating...';
    button.disabled = true;
    
    fetch(`/fiscal-year/fiscal-years/${fiscalYearId}/toggle-status/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json',
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update button appearance
            if (data.is_current) {
                button.classList.remove('btn-outline-secondary');
                button.classList.add('btn-outline-success');
                button.innerHTML = '<i class="bi bi-check-circle"></i>';
            } else {
                button.classList.remove('btn-outline-success');
                button.classList.add('btn-outline-secondary');
                button.innerHTML = '<i class="bi bi-x-circle"></i>';
            }
            
            showAlert(data.message, 'success');
            
            // Update any current fiscal year indicators on the page
            updateCurrentFiscalYearIndicators(fiscalYearId, data.is_current);
        } else {
            showAlert('Failed to update fiscal year status', 'error');
            button.innerHTML = originalText;
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('An error occurred while updating fiscal year status', 'error');
        button.innerHTML = originalText;
    })
    .finally(() => {
        button.disabled = false;
    });
}

// Toggle Period Status
function togglePeriodStatus(periodId, button) {
    const originalText = button.innerHTML;
    button.innerHTML = '<i class="bi bi-hourglass-split"></i> Updating...';
    button.disabled = true;
    
    fetch(`/fiscal-year/periods/${periodId}/toggle-status/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json',
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update button appearance
            if (data.is_current) {
                button.classList.remove('btn-outline-secondary');
                button.classList.add('btn-outline-success');
                button.innerHTML = '<i class="bi bi-check-circle"></i>';
            } else {
                button.classList.remove('btn-outline-success');
                button.classList.add('btn-outline-secondary');
                button.innerHTML = '<i class="bi bi-x-circle"></i>';
            }
            
            showAlert(data.message, 'success');
        } else {
            showAlert('Failed to update period status', 'error');
            button.innerHTML = originalText;
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('An error occurred while updating period status', 'error');
        button.innerHTML = originalText;
    })
    .finally(() => {
        button.disabled = false;
    });
}

// Search Functionality
function initializeSearchFunctionality() {
    const searchForm = document.querySelector('.search-form');
    if (searchForm) {
        const searchInput = searchForm.querySelector('input[name="search"]');
        const clearButton = searchForm.querySelector('.btn-outline-secondary');
        
        // Auto-submit search on input change (with debounce)
        let searchTimeout;
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                searchForm.submit();
            }, 500);
        });
        
        // Clear search
        if (clearButton) {
            clearButton.addEventListener('click', function(e) {
                e.preventDefault();
                searchInput.value = '';
                searchForm.submit();
            });
        }
    }
}

// Table Sorting
function initializeTableSorting() {
    const sortableHeaders = document.querySelectorAll('th[data-sortable]');
    sortableHeaders.forEach(header => {
        header.addEventListener('click', function() {
            const column = this.dataset.column || this.textContent.trim();
            const currentOrder = this.dataset.order || 'asc';
            const newOrder = currentOrder === 'asc' ? 'desc' : 'asc';
            
            // Update URL with sort parameters
            const url = new URL(window.location);
            url.searchParams.set('sort', column);
            url.searchParams.set('order', newOrder);
            window.location.href = url.toString();
        });
        
        // Add visual indicator for sortable columns
        header.style.cursor = 'pointer';
        header.classList.add('sortable-header');
    });
}

// Update Current Fiscal Year Indicators
function updateCurrentFiscalYearIndicators(fiscalYearId, isCurrent) {
    // Remove current indicators from all fiscal years
    document.querySelectorAll('.current-badge').forEach(badge => {
        badge.style.display = 'none';
    });
    
    // Add current indicator to the selected fiscal year
    if (isCurrent) {
        const fiscalYearRow = document.querySelector(`[data-fiscal-year-id="${fiscalYearId}"]`);
        if (fiscalYearRow) {
            const currentBadge = fiscalYearRow.querySelector('.current-badge');
            if (currentBadge) {
                currentBadge.style.display = 'inline-flex';
            }
        }
    }
}

// Export to CSV
function exportToCSV(tableId, filename) {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    let csv = [];
    const rows = table.querySelectorAll('tr');
    
    rows.forEach(row => {
        const cols = row.querySelectorAll('td, th');
        const rowData = [];
        
        cols.forEach(col => {
            // Get text content, excluding action buttons
            const text = col.textContent.trim();
            if (text && !col.querySelector('.action-buttons')) {
                rowData.push(`"${text}"`);
            }
        });
        
        if (rowData.length > 0) {
            csv.push(rowData.join(','));
        }
    });
    
    const csvContent = csv.join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    
    if (link.download !== undefined) {
        const url = URL.createObjectURL(blob);
        link.setAttribute('href', url);
        link.setAttribute('download', filename);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
}

// Show Alert
function showAlert(message, type = 'info') {
    const alertContainer = document.getElementById('alert-container') || createAlertContainer();
    
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    alertContainer.appendChild(alertDiv);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}

// Create Alert Container
function createAlertContainer() {
    const container = document.createElement('div');
    container.id = 'alert-container';
    container.style.position = 'fixed';
    container.style.top = '20px';
    container.style.right = '20px';
    container.style.zIndex = '9999';
    container.style.maxWidth = '400px';
    
    document.body.appendChild(container);
    return container;
}

// Get CSRF Token
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

// Form Auto-save
function initializeAutoSave() {
    const forms = document.querySelectorAll('.fiscal-year-form');
    forms.forEach(form => {
        const inputs = form.querySelectorAll('input, select, textarea');
        let autoSaveTimeout;
        
        inputs.forEach(input => {
            input.addEventListener('input', function() {
                clearTimeout(autoSaveTimeout);
                autoSaveTimeout = setTimeout(() => {
                    autoSaveForm(form);
                }, 2000);
            });
        });
    });
}

// Auto-save Form
function autoSaveForm(form) {
    const formData = new FormData(form);
    const url = form.action || window.location.href;
    
    fetch(url, {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('Form auto-saved successfully', 'success');
        }
    })
    .catch(error => {
        console.error('Auto-save error:', error);
    });
}

// Initialize additional features when page loads
window.addEventListener('load', function() {
    // Add loading states to buttons
    const buttons = document.querySelectorAll('.btn');
    buttons.forEach(button => {
        button.addEventListener('click', function() {
            if (!this.disabled) {
                this.classList.add('loading');
            }
        });
    });
    
    // Initialize auto-save for forms
    initializeAutoSave();
    
    // Add fade-in animation to cards
    const cards = document.querySelectorAll('.fiscal-year-card');
    cards.forEach((card, index) => {
        card.style.animationDelay = `${index * 0.1}s`;
        card.classList.add('fade-in');
    });
}); 