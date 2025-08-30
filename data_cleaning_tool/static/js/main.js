// Data Cleaning Tool - Main JavaScript File

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

    // Auto-hide alerts after 10 seconds (increased from 5 seconds)
    var alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        // Only auto-hide if the alert doesn't have a manual close button or if it's a success message
        if (alert.classList.contains('alert-success') || !alert.querySelector('.btn-close')) {
            setTimeout(function() {
                if (alert.parentNode) {
                    // Use Bootstrap's proper alert dismissal with fade effect
                    var bsAlert = new bootstrap.Alert(alert);
                    bsAlert.close();
                }
            }, 10000); // 10 seconds instead of 5
        }
    });

    // Form validation enhancement
    var forms = document.querySelectorAll('.needs-validation');
    forms.forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });

    // Confirm delete actions
    var deleteButtons = document.querySelectorAll('[data-confirm]');
    deleteButtons.forEach(function(button) {
        button.addEventListener('click', function(event) {
            var message = this.getAttribute('data-confirm') || 'Are you sure you want to delete this item?';
            if (!confirm(message)) {
                event.preventDefault();
            }
        });
    });
});

// Utility functions
function showLoading(element) {
    if (element) {
        element.disabled = true;
        element.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Loading...';
    }
}

function hideLoading(element, originalText) {
    if (element) {
        element.disabled = false;
        element.innerHTML = originalText || 'Submit';
    }
}

function showAlert(message, type = 'info') {
    var alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    var container = document.querySelector('.container-fluid') || document.querySelector('.container');
    if (container) {
        container.insertBefore(alertDiv, container.firstChild);
        
        // Auto-hide after 10 seconds
        setTimeout(function() {
            if (alertDiv.parentNode) {
                var bsAlert = new bootstrap.Alert(alertDiv);
                bsAlert.close();
            }
        }, 10000);
    }
}
