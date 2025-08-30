// Dunning Letters JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Auto-refresh dashboard data every 5 minutes
    if (window.location.pathname.includes('dashboard')) {
        setInterval(refreshDashboardData, 300000); // 5 minutes
    }

    // Handle customer selection in form
    const customerSelect = document.getElementById('customer');
    const invoiceSelect = document.getElementById('invoice');
    const invoiceDetails = document.getElementById('invoiceDetails');

    if (customerSelect && invoiceSelect) {
        customerSelect.addEventListener('change', function() {
            const customerId = this.value;
            if (customerId) {
                loadOverdueInvoices(customerId);
            } else {
                resetInvoiceSelection();
            }
        });

        invoiceSelect.addEventListener('change', function() {
            const selectedOption = this.options[this.selectedIndex];
            if (selectedOption.value) {
                showInvoiceDetails(JSON.parse(selectedOption.dataset.invoice));
            } else {
                hideInvoiceDetails();
            }
        });
    }

    // Handle status updates
    const statusForms = document.querySelectorAll('.status-update-form');
    statusForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            updateLetterStatus(this);
        });
    });

    // Handle email sending
    const emailForms = document.querySelectorAll('.email-send-form');
    emailForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            sendDunningEmail(this);
        });
    });

    // Handle bulk actions
    const bulkActionForm = document.getElementById('bulkActionForm');
    if (bulkActionForm) {
        bulkActionForm.addEventListener('submit', function(e) {
            e.preventDefault();
            performBulkAction(this);
        });
    }

    // Initialize filters
    initializeFilters();
});

// Load overdue invoices for selected customer
function loadOverdueInvoices(customerId) {
    fetch(`/accounting/dunning-letters/ajax/overdue-invoices/?customer_id=${customerId}`)
        .then(response => response.json())
        .then(data => {
            const invoiceSelect = document.getElementById('invoice');
            invoiceSelect.innerHTML = '<option value="">Select Invoice</option>';
            
            data.invoices.forEach(invoice => {
                const option = document.createElement('option');
                option.value = invoice.id;
                option.textContent = `${invoice.invoice_number} - AED ${invoice.total_amount}`;
                option.dataset.invoice = JSON.stringify(invoice);
                invoiceSelect.appendChild(option);
            });
        })
        .catch(error => {
            console.error('Error loading overdue invoices:', error);
            showAlert('Error loading overdue invoices', 'danger');
        });
}

// Reset invoice selection
function resetInvoiceSelection() {
    const invoiceSelect = document.getElementById('invoice');
    const invoiceDetails = document.getElementById('invoiceDetails');
    
    invoiceSelect.innerHTML = '<option value="">Select Invoice</option>';
    if (invoiceDetails) {
        invoiceDetails.style.display = 'none';
    }
}

// Show invoice details
function showInvoiceDetails(invoice) {
    const invoiceDetails = document.getElementById('invoiceDetails');
    if (!invoiceDetails) return;

    const dueDate = new Date(invoice.due_date);
    const today = new Date();
    const overdueDays = Math.floor((today - dueDate) / (1000 * 60 * 60 * 24));
    
    document.getElementById('invoiceNumber').textContent = invoice.invoice_number;
    document.getElementById('dueDate').textContent = dueDate.toLocaleDateString();
    document.getElementById('amount').textContent = `AED ${invoice.total_amount}`;
    document.getElementById('overdueDays').textContent = `${overdueDays} days`;
    
    invoiceDetails.style.display = 'block';
}

// Hide invoice details
function hideInvoiceDetails() {
    const invoiceDetails = document.getElementById('invoiceDetails');
    if (invoiceDetails) {
        invoiceDetails.style.display = 'none';
    }
}

// Update letter status
function updateLetterStatus(form) {
    const formData = new FormData(form);
    const letterId = form.getAttribute('data-letter-id');
    
    fetch(`/accounting/dunning-letters/${letterId}/update-status/`, {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('Status updated successfully', 'success');
            setTimeout(() => {
                window.location.reload();
            }, 1500);
        } else {
            showAlert('Error updating status', 'danger');
        }
    })
    .catch(error => {
        console.error('Error updating status:', error);
        showAlert('Error updating status', 'danger');
    });
}

// Send dunning email
function sendDunningEmail(form) {
    const formData = new FormData(form);
    const letterId = form.getAttribute('data-letter-id');
    
    // Show loading state
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML = '<i class="bi bi-hourglass-split me-1"></i>Sending...';
    submitBtn.disabled = true;
    
    fetch(`/accounting/dunning-letters/${letterId}/send-email/`, {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => {
        if (response.ok) {
            showAlert('Email sent successfully', 'success');
            setTimeout(() => {
                window.location.reload();
            }, 1500);
        } else {
            throw new Error('Failed to send email');
        }
    })
    .catch(error => {
        console.error('Error sending email:', error);
        showAlert('Error sending email', 'danger');
    })
    .finally(() => {
        // Reset button state
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
    });
}

// Perform bulk action
function performBulkAction(form) {
    const formData = new FormData(form);
    const action = formData.get('bulk_action');
    const selectedLetters = formData.getAll('selected_letters');
    
    if (selectedLetters.length === 0) {
        showAlert('Please select at least one letter', 'warning');
        return;
    }
    
    if (!action) {
        showAlert('Please select an action', 'warning');
        return;
    }
    
    // Show confirmation dialog
    if (confirm(`Are you sure you want to ${action} ${selectedLetters.length} letter(s)?`)) {
        fetch('/accounting/dunning-letters/bulk-action/', {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showAlert(`Bulk action completed: ${data.message}`, 'success');
                setTimeout(() => {
                    window.location.reload();
                }, 1500);
            } else {
                showAlert('Error performing bulk action', 'danger');
            }
        })
        .catch(error => {
            console.error('Error performing bulk action:', error);
            showAlert('Error performing bulk action', 'danger');
        });
    }
}

// Initialize filters
function initializeFilters() {
    const filterForm = document.getElementById('filterForm');
    if (!filterForm) return;

    // Auto-submit on filter change
    const filterInputs = filterForm.querySelectorAll('select, input[type="date"], input[type="number"]');
    filterInputs.forEach(input => {
        input.addEventListener('change', function() {
            filterForm.submit();
        });
    });

    // Clear filters button
    const clearFiltersBtn = document.getElementById('clearFilters');
    if (clearFiltersBtn) {
        clearFiltersBtn.addEventListener('click', function(e) {
            e.preventDefault();
            clearFilters();
        });
    }
}

// Clear filters
function clearFilters() {
    const filterForm = document.getElementById('filterForm');
    if (!filterForm) return;

    const filterInputs = filterForm.querySelectorAll('input, select');
    filterInputs.forEach(input => {
        if (input.type === 'text' || input.type === 'number') {
            input.value = '';
        } else if (input.type === 'date') {
            input.value = '';
        } else if (input.tagName === 'SELECT') {
            input.selectedIndex = 0;
        }
    });

    filterForm.submit();
}

// Refresh dashboard data
function refreshDashboardData() {
    fetch('/accounting/dunning-letters/dashboard/ajax/')
        .then(response => response.json())
        .then(data => {
            updateDashboardStats(data);
        })
        .catch(error => {
            console.error('Error refreshing dashboard data:', error);
        });
}

// Update dashboard statistics
function updateDashboardStats(data) {
    // Update statistics cards
    if (data.total_letters !== undefined) {
        document.getElementById('totalLetters').textContent = data.total_letters;
    }
    if (data.sent_letters !== undefined) {
        document.getElementById('sentLetters').textContent = data.sent_letters;
    }
    if (data.total_overdue_amount !== undefined) {
        document.getElementById('totalOverdueAmount').textContent = `AED ${data.total_overdue_amount}`;
    }
    if (data.paid_letters !== undefined) {
        document.getElementById('paidLetters').textContent = data.paid_letters;
    }
}

// Show alert message
function showAlert(message, type) {
    const alertContainer = document.getElementById('alertContainer');
    if (!alertContainer) return;

    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
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

// Get CSRF token from cookies
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

// Export functions for global use
window.DunningLetters = {
    loadOverdueInvoices,
    updateLetterStatus,
    sendDunningEmail,
    performBulkAction,
    clearFilters,
    showAlert
}; 