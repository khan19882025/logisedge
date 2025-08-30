// Dispatch Note Module JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize dispatch note functionality
    initDispatchForm();
    initStatusUpdates();
    initSearchFilters();
    initItemManagement();
    initFormValidation();
    initDeleteDispatch();
    attachDispatchDetailButtonListeners();
});

// Initialize dispatch form functionality
function initDispatchForm() {
    const form = document.getElementById('dispatchForm');
    if (!form) return;

    // Auto-fill shipping address from customer
    const customerSelect = document.getElementById('id_customer');
    if (customerSelect) {
        customerSelect.addEventListener('change', function() {
            const customerId = this.value;
            if (customerId) {
                fetchCustomerAddress(customerId);
            } else {
                clearShippingAddress();
            }
        });
    }
}

// Fetch customer address and auto-fill shipping fields
function fetchCustomerAddress(customerId) {
    // This would need an API endpoint to work
    console.log('Fetching address for customer:', customerId);
}

// Clear shipping address fields
function clearShippingAddress() {
    const fields = ['id_shipping_address', 'id_shipping_city', 'id_shipping_state', 'id_shipping_country', 'id_shipping_postal_code'];
    fields.forEach(fieldId => {
        const field = document.getElementById(fieldId);
        if (field) field.value = '';
    });
}

// Initialize status update functionality
function initStatusUpdates() {
    const statusButtons = document.querySelectorAll('.status-update-btn');
    statusButtons.forEach(button => {
        button.addEventListener('click', function() {
            const dispatchId = this.dataset.dispatchId;
            const newStatus = this.dataset.status;
            updateDispatchStatus(dispatchId, newStatus);
        });
    });
}

// Update dispatch status via AJAX
function updateDispatchStatus(dispatchId, newStatus) {
    const formData = new FormData();
    formData.append('status', newStatus);
    formData.append('csrfmiddlewaretoken', getCookie('csrftoken'));

    fetch(`/dispatchnote/${dispatchId}/update-status/`, {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast(data.message, 'success');
            setTimeout(() => {
                location.reload();
            }, 1500);
        } else {
            showToast(data.message, 'error');
        }
    })
    .catch(error => {
        console.error('Error updating status:', error);
        showToast('An error occurred while updating the status.', 'error');
    });
}

// Initialize search filters
function initSearchFilters() {
    const searchForm = document.getElementById('searchForm');
    if (!searchForm) return;

    // Clear filters button
    const clearFiltersBtn = document.getElementById('clearFilters');
    if (clearFiltersBtn) {
        clearFiltersBtn.addEventListener('click', function() {
            const inputs = searchForm.querySelectorAll('input, select');
            inputs.forEach(input => {
                if (input.type === 'text' || input.type === 'date') {
                    input.value = '';
                } else if (input.tagName === 'SELECT') {
                    input.selectedIndex = 0;
                }
            });
            searchForm.submit();
        });
    }
}

// Initialize item management
function initItemManagement() {
    // Delete item confirmation
    const deleteItemButtons = document.querySelectorAll('.delete-item-btn');
    deleteItemButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to remove this item from the dispatch note?')) {
                e.preventDefault();
            }
        });
    });
}

// Initialize form validation
function initFormValidation() {
    const forms = document.querySelectorAll('.needs-validation');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            console.log('Form submission attempted');
            
            // Remove the validation prevention - allow form to submit
            // The server-side validation will handle any issues
            form.classList.add('was-validated');
            
            // Show loading state
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<i class="bi bi-hourglass-split me-2"></i>Saving...';
            }
            
            // Allow the form to submit normally
            return true;
        });
    });
}

// Show toast notification
function showToast(message, type = 'info') {
    // Create toast element
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type === 'error' ? 'danger' : type === 'success' ? 'success' : 'info'} border-0`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;
    
    // Add to toast container
    let toastContainer = document.getElementById('toastContainer');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toastContainer';
        toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
        toastContainer.style.zIndex = '9999';
        document.body.appendChild(toastContainer);
    }
    
    toastContainer.appendChild(toast);
    
    // Show toast
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    // Remove toast after it's hidden
    toast.addEventListener('hidden.bs.toast', function() {
        toast.remove();
    });
}

// Get cookie value
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

// Print dispatch note
function printDispatchNote(dispatchId) {
    // Show loading state
    showToast('Generating PDF...', 'info');
    
    // Open PDF in new window/tab
    const printUrl = `/dispatchnote/${dispatchId}/print/`;
    window.open(printUrl, '_blank');
}

// Email dispatch note
function emailDispatchNote(dispatchId) {
    // Show loading state
    showToast('Preparing email...', 'info');
    
    // For now, we'll just show a message that email functionality is coming soon
    // In a real implementation, this would open an email form or send via API
    setTimeout(() => {
        showToast('Email functionality will be implemented soon!', 'info');
    }, 1000);
    
    // Future implementation could be:
    // window.open(`/dispatchnote/${dispatchId}/email/`, '_blank');
    // or
    // fetch(`/dispatchnote/${dispatchId}/email/`, {
    //     method: 'POST',
    //     headers: {
    //         'X-Requested-With': 'XMLHttpRequest',
    //         'X-CSRFToken': getCookie('csrftoken')
    //     }
    // })
    // .then(response => response.json())
    // .then(data => {
    //     if (data.success) {
    //         showToast('Email sent successfully!', 'success');
    //     } else {
    //         showToast('Failed to send email: ' + data.message, 'error');
    //     }
    // })
    // .catch(error => {
    //     console.error('Error sending email:', error);
    //     showToast('An error occurred while sending email.', 'error');
    // });
}

// Export dispatch note to PDF
function exportDispatchNotePDF(dispatchId) {
    window.open(`/dispatchnote/${dispatchId}/export-pdf/`, '_blank');
}

// Export dispatch note to Excel
function exportDispatchNoteExcel(dispatchId) {
    window.open(`/dispatchnote/${dispatchId}/export-excel/`, '_blank');
}

// Initialize delete dispatch functionality
function initDeleteDispatch() {
    const deleteButtons = document.querySelectorAll('.delete-dispatch-btn');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function() {
            const dispatchId = this.dataset.dispatchId;
            const dispatchNumber = this.dataset.dispatchNumber;
            
            if (confirm(`Are you sure you want to delete dispatch note "${dispatchNumber}"? This action cannot be undone.`)) {
                deleteDispatchNote(dispatchId);
            }
        });
    });
}

// Delete dispatch note via AJAX
function deleteDispatchNote(dispatchId) {
    const formData = new FormData();
    formData.append('csrfmiddlewaretoken', getCookie('csrftoken'));

    fetch(`/dispatchnote/${dispatchId}/delete/`, {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast(data.message, 'success');
            setTimeout(() => {
                location.reload();
            }, 1500);
        } else {
            showToast(data.message, 'error');
        }
    })
    .catch(error => {
        console.error('Error deleting dispatch note:', error);
        showToast('An error occurred while deleting the dispatch note.', 'error');
    });
}

function attachDispatchDetailButtonListeners() {
    // Print button
    document.querySelectorAll('.btn-print-dispatch').forEach(btn => {
        btn.addEventListener('click', function() {
            const dispatchId = this.getAttribute('data-dispatch-id');
            printDispatchNote(dispatchId);
        });
    });
    // Email button
    document.querySelectorAll('.btn-email-dispatch').forEach(btn => {
        btn.addEventListener('click', function() {
            const dispatchId = this.getAttribute('data-dispatch-id');
            emailDispatchNote(dispatchId);
        });
    });
} 