// GRN Module JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize GRN functionality
    initGRNModule();
});

function initGRNModule() {
    // Initialize search functionality
    initSearch();
    
    // Initialize filters
    initFilters();
    
    // Initialize table interactions
    initTableInteractions();
    
    // Initialize form enhancements
    initFormEnhancements();
    
    // Initialize responsive sidebar
    initResponsiveSidebar();
}

// Search functionality
function initSearch() {
    const searchInput = document.querySelector('input[name="search"]');
    if (searchInput) {
        let searchTimeout;
        
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                this.closest('form').submit();
            }, 500);
        });
    }
}

// Filter functionality
function initFilters() {
    const filterSelects = document.querySelectorAll('select[name="status"], select[name="priority"], select[name="facility"]');
    
    filterSelects.forEach(select => {
        select.addEventListener('change', function() {
            this.closest('form').submit();
        });
    });
}

// Table interactions
function initTableInteractions() {
    const tableRows = document.querySelectorAll('.grn-table tbody tr');
    
    tableRows.forEach(row => {
        row.addEventListener('click', function(e) {
            // Don't trigger if clicking on action buttons
            if (e.target.closest('.btn-group')) {
                return;
            }
            
            // Find the detail link and navigate to it
            const detailLink = this.querySelector('a[href*="detail"]');
            if (detailLink) {
                window.location.href = detailLink.href;
            }
        });
        
        // Add hover effect
        row.style.cursor = 'pointer';
    });
}

// Form enhancements
function initFormEnhancements() {
    const form = document.querySelector('.grn-form');
    if (!form) return;
    
    // Initialize form validation
    initFormValidation();
    
    // Initialize item selection
    initItemSelection();
    
    // Initialize responsive sidebar
    initResponsiveSidebar();
    
    // Auto-save functionality (disabled for now)
    // initAutoSave(form);
}

// Auto-save functionality (disabled for now)
/*
function initAutoSave(form) {
    let autoSaveTimeout;
    const formData = new FormData(form);
    
    form.addEventListener('input', function() {
        clearTimeout(autoSaveTimeout);
        autoSaveTimeout = setTimeout(() => {
            saveFormDraft(form);
        }, 2000);
    });
}

function saveFormDraft(form) {
    const formData = new FormData(form);
    formData.append('is_draft', 'true');
    
    fetch(form.action, {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Draft saved automatically', 'success');
        }
    })
    .catch(error => {
        console.error('Auto-save error:', error);
    });
}
*/

// Form validation
function initFormValidation() {
    const requiredFields = document.querySelectorAll('[required]');
    
    requiredFields.forEach(field => {
        field.addEventListener('blur', function() {
            validateField(this);
        });
        
        field.addEventListener('input', function() {
            clearFieldError(this);
        });
    });
}

function validateField(field) {
    const value = field.value.trim();
    const isValid = field.checkValidity();
    
    if (!isValid) {
        showFieldError(field, field.validationMessage);
    } else {
        clearFieldError(field);
    }
    
    return isValid;
}

function showFieldError(field, message) {
    clearFieldError(field);
    
    const errorDiv = document.createElement('div');
    errorDiv.className = 'invalid-feedback';
    errorDiv.textContent = message;
    
    field.classList.add('is-invalid');
    field.parentNode.appendChild(errorDiv);
}

function clearFieldError(field) {
    field.classList.remove('is-invalid');
    const errorDiv = field.parentNode.querySelector('.invalid-feedback');
    if (errorDiv) {
        errorDiv.remove();
    }
}

// Item selection enhancement
function initItemSelection() {
    const itemSelects = document.querySelectorAll('.item-select');
    
    itemSelects.forEach(select => {
        select.addEventListener('change', function() {
            const itemId = this.value;
            if (itemId) {
                loadItemDetails(itemId, this);
            }
        });
    });
}

function loadItemDetails(itemId, selectElement) {
    fetch(`/grn/get-items/?search=${itemId}`)
        .then(response => response.json())
        .then(data => {
            if (data.items && data.items.length > 0) {
                const item = data.items[0];
                populateItemFields(item, selectElement);
            }
        })
        .catch(error => {
            console.error('Error loading item details:', error);
        });
}

function populateItemFields(item, selectElement) {
    const row = selectElement.closest('tr');
    
    // Populate item fields
    const itemCodeField = row.querySelector('input[name*="item_code"]');
    const itemNameField = row.querySelector('input[name*="item_name"]');
    const hsCodeField = row.querySelector('input[name*="hs_code"]');
    const unitField = row.querySelector('input[name*="unit"]');
    
    if (itemCodeField) itemCodeField.value = item.item_code || '';
    if (itemNameField) itemNameField.value = item.item_name || '';
    if (hsCodeField) hsCodeField.value = item.hs_code || '';
    if (unitField) unitField.value = item.unit || '';
}

// Responsive sidebar
function initResponsiveSidebar() {
    const sidebarToggle = document.querySelector('.sidebar-toggle');
    const sidebar = document.querySelector('.sidebar');
    
    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', function() {
            sidebar.classList.toggle('show');
        });
        
        // Close sidebar when clicking outside on mobile
        document.addEventListener('click', function(e) {
            if (window.innerWidth <= 768) {
                if (!sidebar.contains(e.target) && !sidebarToggle.contains(e.target)) {
                    sidebar.classList.remove('show');
                }
            }
        });
    }
}

// Notification system
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 5000);
}

// Utility functions
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

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'AED'
    }).format(amount);
}

// Export functions for use in other scripts
window.GRNModule = {
    showNotification,
    formatDate,
    formatCurrency,
    validateField,
    loadItemDetails
}; 