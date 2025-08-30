// Company Module JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl, {
            trigger: 'hover',
            placement: 'top',
            animation: true
        });
    });

    // Search functionality
    const searchInput = document.querySelector('input[name="search"]');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            // Add debouncing for search
            clearTimeout(this.searchTimeout);
            this.searchTimeout = setTimeout(() => {
                this.form.submit();
            }, 500);
        });
    }

    // Confirm delete functionality
    const deleteButtons = document.querySelectorAll('.btn-outline-danger');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to delete this company? This action cannot be undone.')) {
                e.preventDefault();
            }
        });
    });

    // Table row selection
    const tableRows = document.querySelectorAll('.table-hover tbody tr');
    tableRows.forEach(row => {
        row.addEventListener('click', function(e) {
            // Don't trigger if clicking on action buttons
            if (e.target.closest('.btn-group')) {
                return;
            }
            
            // Remove active class from all rows
            tableRows.forEach(r => r.classList.remove('table-active'));
            
            // Add active class to clicked row
            this.classList.add('table-active');
        });
    });

    // Action button hover effects
    const actionButtons = document.querySelectorAll('.btn-group .btn');
    actionButtons.forEach(button => {
        button.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-2px)';
        });
        
        button.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });

    // Form validation
    const validationForms = document.querySelectorAll('.needs-validation');
    validationForms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });

    // Auto-save draft functionality
    const formInputs = document.querySelectorAll('form input, form textarea, form select');
    formInputs.forEach(input => {
        input.addEventListener('change', function() {
            // Save form data to localStorage
            const form = this.closest('form');
            const formData = new FormData(form);
            const formObject = {};
            
            for (let [key, value] of formData.entries()) {
                formObject[key] = value;
            }
            
            localStorage.setItem('company_form_draft', JSON.stringify(formObject));
        });
    });

    // Load draft on page load
    const savedDraft = localStorage.getItem('company_form_draft');
    if (savedDraft && window.location.pathname.includes('/create/')) {
        const formObject = JSON.parse(savedDraft);
        Object.keys(formObject).forEach(key => {
            const input = document.querySelector(`[name="${key}"]`);
            if (input && !input.value) {
                input.value = formObject[key];
            }
        });
    }

    // Clear draft when form is successfully submitted
    const allForms = document.querySelectorAll('form');
    allForms.forEach(form => {
        form.addEventListener('submit', function() {
            localStorage.removeItem('company_form_draft');
        });
    });
});

// Utility functions
function showNotification(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    toast.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    toast.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(toast);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (toast.parentNode) {
            toast.remove();
        }
    }, 5000);
}

function formatPhoneNumber(input) {
    let value = input.value.replace(/\D/g, '');
    if (value.length > 0) {
        value = value.replace(/(\d{3})(\d{3})(\d{4})/, '($1) $2-$3');
    }
    input.value = value;
} 