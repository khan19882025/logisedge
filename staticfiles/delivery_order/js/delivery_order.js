// Delivery Order JavaScript

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

    // Auto-fill email fields based on delivery order data
    initializeEmailFields();
    
    // Initialize print functionality
    initializePrintFunctionality();
    
    // Initialize email functionality
    initializeEmailFunctionality();
});

function initializeEmailFields() {
    const recipientEmail = document.getElementById('recipient_email');
    const emailSubject = document.getElementById('email_subject');
    const emailMessage = document.getElementById('email_message');
    
    if (recipientEmail && !recipientEmail.value) {
        // Try to get email from customer or delivery contact
        const customerEmail = document.querySelector('[data-customer-email]')?.dataset.customerEmail;
        const deliveryEmail = document.querySelector('[data-delivery-email]')?.dataset.deliveryEmail;
        
        if (deliveryEmail) {
            recipientEmail.value = deliveryEmail;
        } else if (customerEmail) {
            recipientEmail.value = customerEmail;
        }
    }
    
    // Update subject line with current date
    if (emailSubject) {
        const currentDate = new Date().toLocaleDateString();
        const doNumber = document.querySelector('[data-do-number]')?.dataset.doNumber;
        const customerName = document.querySelector('[data-customer-name]')?.dataset.customerName;
        
        if (doNumber && customerName) {
            emailSubject.value = `Delivery Order ${doNumber} - ${customerName} (${currentDate})`;
        }
    }
}

function initializePrintFunctionality() {
    // Add print button event listeners
    const printButtons = document.querySelectorAll('[onclick*="printDeliveryOrder"]');
    printButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            printDeliveryOrder();
        });
    });
}

function initializeEmailFunctionality() {
    // Add email button event listeners
    const emailButtons = document.querySelectorAll('[onclick*="emailDeliveryOrder"]');
    emailButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            emailDeliveryOrder();
        });
    });
    
    // Initialize email form submission
    const emailForm = document.getElementById('emailForm');
    if (emailForm) {
        emailForm.addEventListener('submit', handleEmailSubmission);
    }
}

// Print functionality
function printDeliveryOrder() {
    // Show loading indicator
    const printBtn = event.target.closest('button');
    const originalText = printBtn.innerHTML;
    printBtn.innerHTML = '<i class="bi bi-hourglass-split me-1"></i> Preparing...';
    printBtn.disabled = true;
    
    // Small delay to show loading state
    setTimeout(() => {
        window.print();
        
        // Restore button state
        printBtn.innerHTML = originalText;
        printBtn.disabled = false;
    }, 500);
}

// Email functionality
function emailDeliveryOrder() {
    const emailModal = new bootstrap.Modal(document.getElementById('emailModal'));
    emailModal.show();
}

// Email form submission handler
function handleEmailSubmission(e) {
    e.preventDefault();
    
    const submitBtn = this.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML = '<i class="bi bi-hourglass-split me-1"></i> Sending...';
    submitBtn.disabled = true;
    
    // Get form data
    const formData = new FormData(this);
    
    // Validate form
    if (!validateEmailForm(formData)) {
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
        return;
    }
    
    // Send AJAX request
    fetch(this.action, {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': formData.get('csrfmiddlewaretoken')
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Show success message
            showAlert('success', 'Email sent successfully!');
            bootstrap.Modal.getInstance(document.getElementById('emailModal')).hide();
        } else {
            // Show error message
            showAlert('danger', data.error || 'Failed to send email. Please try again.');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('danger', 'An error occurred while sending the email.');
    })
    .finally(() => {
        // Restore button state
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
    });
}

// Validate email form
function validateEmailForm(formData) {
    const recipientEmail = formData.get('recipient_email');
    const emailSubject = formData.get('email_subject');
    
    if (!recipientEmail || !recipientEmail.trim()) {
        showAlert('danger', 'Recipient email is required.');
        return false;
    }
    
    if (!emailSubject || !emailSubject.trim()) {
        showAlert('danger', 'Email subject is required.');
        return false;
    }
    
    // Basic email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(recipientEmail)) {
        showAlert('danger', 'Please enter a valid email address.');
        return false;
    }
    
    const ccEmail = formData.get('cc_email');
    if (ccEmail && !emailRegex.test(ccEmail)) {
        showAlert('danger', 'Please enter a valid CC email address.');
        return false;
    }
    
    return true;
}

// Alert function
function showAlert(type, message) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // Insert at the top of the container
    const container = document.querySelector('.delivery-order-detail-container');
    if (container) {
        container.insertBefore(alertDiv, container.firstChild);
    } else {
        // Fallback to body if container not found
        document.body.insertBefore(alertDiv, document.body.firstChild);
    }
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}

// Utility function to format currency
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}

// Utility function to format date
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

// Export functions for global access
window.deliveryOrderUtils = {
    printDeliveryOrder,
    emailDeliveryOrder,
    showAlert,
    formatCurrency,
    formatDate
}; 