// Cross Stuffing JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize cross stuffing functionality
    initializeCrossStuffing();
});

function initializeCrossStuffing() {
    // Status update functionality
    initializeStatusUpdates();
    
    // Form validation
    initializeFormValidation();
    
    // Search and filter functionality
    initializeSearchFilters();
    
    // Quick actions
    initializeQuickActions();
}

function initializeStatusUpdates() {
    // Handle status update buttons
    const statusButtons = document.querySelectorAll('.status-update-btn');
    
    statusButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            
            const csId = this.dataset.csId;
            const newStatus = this.dataset.status;
            const buttonText = this.textContent;
            
            if (confirm(`Are you sure you want to change the status to "${buttonText}"?`)) {
                updateCrossStuffingStatus(csId, newStatus);
            }
        });
    });
}

function updateCrossStuffingStatus(csId, newStatus) {
    const formData = new FormData();
    formData.append('status', newStatus);
    formData.append('csrfmiddlewaretoken', getCookie('csrftoken'));
    
    fetch(`/crossstuffing/${csId}/status-update/`, {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update the status badge
            const statusBadge = document.querySelector(`[data-cs-id="${csId}"] .status-badge`);
            if (statusBadge) {
                statusBadge.textContent = data.status;
                statusBadge.className = `status-badge status-${data.status}`;
            }
            
            // Show success message
            showMessage('Status updated successfully!', 'success');
            
            // Reload page after a short delay to reflect changes
            setTimeout(() => {
                location.reload();
            }, 1000);
        } else {
            showMessage('Failed to update status. Please try again.', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showMessage('An error occurred while updating status.', 'error');
    });
}

function initializeFormValidation() {
    const form = document.querySelector('.crossstuffing-form');
    if (!form) return;
    
    // Validate scheduled date
    const scheduledDateInput = form.querySelector('input[name="scheduled_date"]');
    const csDateInput = form.querySelector('input[name="cs_date"]');
    
    if (scheduledDateInput && csDateInput) {
        scheduledDateInput.addEventListener('change', function() {
            const scheduledDate = new Date(this.value);
            const csDate = new Date(csDateInput.value);
            
            if (scheduledDate < csDate) {
                this.setCustomValidity('Scheduled date cannot be before CS date.');
                this.reportValidity();
            } else {
                this.setCustomValidity('');
            }
        });
    }
    
    // Validate numeric fields
    const numericInputs = form.querySelectorAll('input[type="number"]');
    numericInputs.forEach(input => {
        input.addEventListener('input', function() {
            const value = parseFloat(this.value);
            const min = parseFloat(this.min);
            
            if (this.value && value < min) {
                this.setCustomValidity(`Value must be at least ${min}.`);
                this.reportValidity();
            } else {
                this.setCustomValidity('');
            }
        });
    });
    
    // Auto-calculate totals if needed
    const totalPackagesInput = form.querySelector('input[name="total_packages"]');
    const totalWeightInput = form.querySelector('input[name="total_weight"]');
    const totalVolumeInput = form.querySelector('input[name="total_volume"]');
    
    if (totalPackagesInput && totalWeightInput && totalVolumeInput) {
        // Add event listeners for auto-calculation if needed
        totalPackagesInput.addEventListener('input', validateNumericInput);
        totalWeightInput.addEventListener('input', validateNumericInput);
        totalVolumeInput.addEventListener('input', validateNumericInput);
    }
}

function validateNumericInput() {
    const value = parseFloat(this.value);
    const min = parseFloat(this.min);
    
    if (this.value && (isNaN(value) || value < min)) {
        this.setCustomValidity(`Please enter a valid number (minimum: ${min}).`);
        this.reportValidity();
    } else {
        this.setCustomValidity('');
    }
}

function initializeSearchFilters() {
    const searchForm = document.querySelector('.search-filters form');
    if (!searchForm) return;
    
    // Clear filters button
    const clearFiltersBtn = document.querySelector('.clear-filters-btn');
    if (clearFiltersBtn) {
        clearFiltersBtn.addEventListener('click', function(e) {
            e.preventDefault();
            clearAllFilters();
        });
    }
    
    // Auto-submit on filter change
    const filterSelects = searchForm.querySelectorAll('select');
    filterSelects.forEach(select => {
        select.addEventListener('change', function() {
            searchForm.submit();
        });
    });
}

function clearAllFilters() {
    const searchForm = document.querySelector('.search-filters form');
    if (!searchForm) return;
    
    // Clear all input fields
    const inputs = searchForm.querySelectorAll('input[type="text"], input[type="date"]');
    inputs.forEach(input => {
        input.value = '';
    });
    
    // Reset all select fields
    const selects = searchForm.querySelectorAll('select');
    selects.forEach(select => {
        select.selectedIndex = 0;
    });
    
    // Submit the form
    searchForm.submit();
}

function initializeQuickActions() {
    // Quick view buttons
    const quickViewButtons = document.querySelectorAll('.quick-view-btn');
    quickViewButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const csId = this.dataset.csId;
            openQuickView(csId);
        });
    });
    
    // Delete confirmation
    const deleteButtons = document.querySelectorAll('.delete-btn');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const csNumber = this.dataset.csNumber;
            
            if (confirm(`Are you sure you want to delete cross stuffing "${csNumber}"? This action cannot be undone.`)) {
                this.closest('form').submit();
            }
        });
    });
}

function openQuickView(csId) {
    // Open quick view in a modal or new window
    const url = `/crossstuffing/${csId}/quick-view/`;
    
    // Create modal
    const modal = document.createElement('div');
    modal.className = 'modal fade';
    modal.id = 'quickViewModal';
    modal.innerHTML = `
        <div class="modal-dialog modal-lg">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Cross Stuffing Quick View</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <div class="text-center">
                        <div class="spinner-border" role="status">
                            <span class="visually-hidden">Loading...</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Load content
    fetch(url)
        .then(response => response.text())
        .then(html => {
            const modalBody = modal.querySelector('.modal-body');
            modalBody.innerHTML = html;
            
            // Show modal
            const bootstrapModal = new bootstrap.Modal(modal);
            bootstrapModal.show();
            
            // Remove modal from DOM when hidden
            modal.addEventListener('hidden.bs.modal', function() {
                document.body.removeChild(modal);
            });
        })
        .catch(error => {
            console.error('Error loading quick view:', error);
            const modalBody = modal.querySelector('.modal-body');
            modalBody.innerHTML = '<div class="alert alert-danger">Error loading quick view.</div>';
        });
}

function showMessage(message, type = 'info') {
    // Create message element
    const messageDiv = document.createElement('div');
    messageDiv.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show`;
    messageDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // Insert at the top of the container
    const container = document.querySelector('.crossstuffing-container');
    if (container) {
        container.insertBefore(messageDiv, container.firstChild);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (messageDiv.parentNode) {
                messageDiv.remove();
            }
        }, 5000);
    }
}

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

// Export functions for use in other scripts
window.CrossStuffing = {
    updateStatus: updateCrossStuffingStatus,
    openQuickView: openQuickView,
    showMessage: showMessage,
    clearFilters: clearAllFilters
}; 