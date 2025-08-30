// Facility Module JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize form validation
    initializeFormValidation();
    
    // Initialize tab switching for validation errors
    initializeTabSwitching();
    
    // Initialize search functionality
    initializeSearch();
    
    // Initialize status toggle functionality
    initializeStatusToggle();
});

// Form validation
function initializeFormValidation() {
    const form = document.getElementById('facilityForm');
    if (form) {
        form.addEventListener('submit', function(e) {
            if (!validateForm()) {
                e.preventDefault();
                showValidationErrors();
            }
        });
    }
}

function validateForm() {
    let isValid = true;
    const requiredFields = ['facility_code', 'facility_name'];
    
    requiredFields.forEach(fieldName => {
        const field = document.getElementById(`id_${fieldName}`);
        if (field && !field.value.trim()) {
            isValid = false;
            field.classList.add('is-invalid');
        } else if (field) {
            field.classList.remove('is-invalid');
        }
    });
    
    // Validate facility code format
    const facilityCodeField = document.getElementById('id_facility_code');
    if (facilityCodeField && facilityCodeField.value) {
        const codePattern = /^[A-Z0-9-]+$/;
        if (!codePattern.test(facilityCodeField.value.toUpperCase())) {
            isValid = false;
            facilityCodeField.classList.add('is-invalid');
        }
    }
    
    // Validate area measurements
    const totalAreaField = document.getElementById('id_total_area');
    const usableAreaField = document.getElementById('id_usable_area');
    
    if (totalAreaField && usableAreaField && 
        totalAreaField.value && usableAreaField.value) {
        if (parseFloat(usableAreaField.value) > parseFloat(totalAreaField.value)) {
            isValid = false;
            usableAreaField.classList.add('is-invalid');
            showAlert('Usable area cannot be greater than total area.', 'danger');
        }
    }
    
    // Validate lease dates
    const leaseStartField = document.getElementById('id_lease_start_date');
    const leaseEndField = document.getElementById('id_lease_end_date');
    
    if (leaseStartField && leaseEndField && 
        leaseStartField.value && leaseEndField.value) {
        if (new Date(leaseStartField.value) > new Date(leaseEndField.value)) {
            isValid = false;
            leaseEndField.classList.add('is-invalid');
            showAlert('Lease start date cannot be after lease end date.', 'danger');
        }
    }
    
    return isValid;
}

function showValidationErrors() {
    showAlert('Please correct the errors below.', 'danger');
    
    // Scroll to first error
    const firstError = document.querySelector('.is-invalid');
    if (firstError) {
        firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
}

// Tab switching for validation errors
function initializeTabSwitching() {
    const tabs = document.querySelectorAll('[data-bs-toggle="tab"]');
    tabs.forEach(tab => {
        tab.addEventListener('shown.bs.tab', function(e) {
            // Check if there are validation errors in the current tab
            const targetId = e.target.getAttribute('data-bs-target');
            const targetPane = document.querySelector(targetId);
            
            if (targetPane) {
                const errors = targetPane.querySelectorAll('.is-invalid');
                if (errors.length > 0) {
                    showAlert('This tab contains validation errors. Please fix them before proceeding.', 'warning');
                }
            }
        });
    });
}

// Search functionality
function initializeSearch() {
    const searchForm = document.querySelector('form[method="get"]');
    if (searchForm) {
        const searchInput = searchForm.querySelector('input[name="search_term"]');
        const searchField = searchForm.querySelector('select[name="search_field"]');
        
        // Auto-submit on search field change
        if (searchField) {
            searchField.addEventListener('change', function() {
                if (searchInput && searchInput.value.trim()) {
                    searchForm.submit();
                }
            });
        }
        
        // Debounced search
        if (searchInput) {
            let searchTimeout;
            searchInput.addEventListener('input', function() {
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(() => {
                    if (this.value.trim().length >= 2 || this.value.trim().length === 0) {
                        searchForm.submit();
                    }
                }, 500);
            });
        }
    }
}

// Status toggle functionality
function initializeStatusToggle() {
    const statusToggles = document.querySelectorAll('.status-toggle');
    statusToggles.forEach(toggle => {
        toggle.addEventListener('change', function() {
            const facilityId = this.dataset.facilityId;
            const newStatus = this.checked ? 'active' : 'inactive';
            
            toggleFacilityStatus(facilityId, newStatus);
        });
    });
}

// AJAX functions
function toggleFacilityStatus(facilityId, status) {
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    
    fetch(`/facility/${facilityId}/toggle-status/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({ status: status })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert(data.message, 'success');
            // Update UI
            updateStatusDisplay(facilityId, status);
        } else {
            showAlert(data.message, 'danger');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('An error occurred while updating status.', 'danger');
    });
}

function updateStatusDisplay(facilityId, status) {
    const statusCell = document.querySelector(`[data-facility-id="${facilityId}"] .status-badge`);
    if (statusCell) {
        statusCell.className = `badge ${status === 'active' ? 'bg-success' : 'bg-warning'}`;
        statusCell.textContent = status === 'active' ? 'Active' : 'Inactive';
    }
}

// Quick view functionality
function quickView(facilityId) {
    const modal = new bootstrap.Modal(document.getElementById('quickViewModal'));
    const content = document.getElementById('quickViewContent');
    
    // Show loading state
    content.innerHTML = '<div class="text-center"><i class="bi bi-hourglass-split fa-spin fa-2x"></i><p>Loading...</p></div>';
    modal.show();
    
    // Fetch facility data
    fetch(`/facility/${facilityId}/quick-view/`)
        .then(response => response.text())
        .then(html => {
            content.innerHTML = html;
        })
        .catch(error => {
            console.error('Error:', error);
            content.innerHTML = '<div class="text-center text-danger"><i class="bi bi-exclamation-triangle fa-2x"></i><p>Error loading facility data</p></div>';
        });
}

// Delete functionality
function deleteFacility(facilityId, facilityName) {
    const modal = new bootstrap.Modal(document.getElementById('deleteModal'));
    const deleteForm = document.getElementById('deleteForm');
    const facilityNameSpan = document.getElementById('deleteFacilityName');
    
    // Set facility name and form action
    facilityNameSpan.textContent = facilityName;
    deleteForm.action = `/facility/${facilityId}/delete/`;
    
    modal.show();
}

// Utility functions
function showAlert(message, type) {
    // Remove existing alerts
    const existingAlerts = document.querySelectorAll('.alert');
    existingAlerts.forEach(alert => alert.remove());
    
    // Create new alert
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // Insert at top of content
    const container = document.querySelector('.container-fluid');
    if (container) {
        container.insertBefore(alertDiv, container.firstChild);
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    }
}

// Form field enhancements
function initializeFormEnhancements() {
    // Auto-format facility code
    const facilityCodeField = document.getElementById('id_facility_code');
    if (facilityCodeField) {
        facilityCodeField.addEventListener('input', function() {
            this.value = this.value.toUpperCase().replace(/[^A-Z0-9-]/g, '');
        });
    }
    
    // Auto-format phone numbers
    const phoneFields = document.querySelectorAll('input[name*="phone"]');
    phoneFields.forEach(field => {
        field.addEventListener('input', function() {
            this.value = this.value.replace(/[^0-9+\-\(\)\s]/g, '');
        });
    });
    
    // Currency field enhancement
    const currencyField = document.getElementById('id_currency');
    if (currencyField) {
        currencyField.addEventListener('input', function() {
            this.value = this.value.toUpperCase().substring(0, 3);
        });
    }
}

// Data table enhancements
function initializeDataTable() {
    const table = document.getElementById('facilitiesTable');
    if (table) {
        // Add sorting functionality
        const headers = table.querySelectorAll('th[data-sortable]');
        headers.forEach(header => {
            header.addEventListener('click', function() {
                const column = this.dataset.column;
                const currentOrder = this.dataset.order || 'asc';
                const newOrder = currentOrder === 'asc' ? 'desc' : 'asc';
                
                // Update URL and reload
                const url = new URL(window.location);
                url.searchParams.set('sort', column);
                url.searchParams.set('order', newOrder);
                window.location.href = url.toString();
            });
        });
    }
}

// Export functionality
function exportFacilities(format = 'csv') {
    const searchParams = new URLSearchParams(window.location.search);
    searchParams.set('export', format);
    
    window.location.href = `/facility/export/?${searchParams.toString()}`;
}

// Print functionality
function printFacilityDetails() {
    window.print();
}

// Share functionality
function shareFacility() {
    if (navigator.share) {
        navigator.share({
            title: 'Facility Details',
            text: 'Check out this facility information',
            url: window.location.href
        });
    } else {
        // Fallback: copy URL to clipboard
        navigator.clipboard.writeText(window.location.href).then(() => {
            showAlert('URL copied to clipboard!', 'success');
        });
    }
}

// Initialize all enhancements when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeFormEnhancements();
    initializeDataTable();
    
    // Add event listeners for utility functions
    const printBtn = document.querySelector('.btn-print');
    if (printBtn) {
        printBtn.addEventListener('click', printFacilityDetails);
    }
    
    const shareBtn = document.querySelector('.btn-share');
    if (shareBtn) {
        shareBtn.addEventListener('click', shareFacility);
    }
});

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + N for new facility
    if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
        e.preventDefault();
        window.location.href = '/facility/create/';
    }
    
    // Ctrl/Cmd + F for search
    if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
        e.preventDefault();
        const searchInput = document.querySelector('input[name="search_term"]');
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