// Salesman module custom scripts

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Phone number formatting
    const phoneInputs = document.querySelectorAll('input[name="phone"]');
    phoneInputs.forEach(function(input) {
        input.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            if (value.length > 0) {
                if (value.length <= 3) {
                    value = value;
                } else if (value.length <= 6) {
                    value = value.slice(0, 3) + '-' + value.slice(3);
                } else {
                    value = value.slice(0, 3) + '-' + value.slice(3, 6) + '-' + value.slice(6, 10);
                }
            }
            e.target.value = value;
        });
    });

    // Commission rate validation
    const commissionInput = document.querySelector('input[name="commission_rate"]');
    if (commissionInput) {
        commissionInput.addEventListener('input', function(e) {
            let value = parseFloat(e.target.value);
            if (value > 100) {
                e.target.value = 100;
            } else if (value < 0) {
                e.target.value = 0;
            }
        });
    }

    // Target amount formatting
    const targetInput = document.querySelector('input[name="target_amount"]');
    if (targetInput) {
        targetInput.addEventListener('input', function(e) {
            let value = parseFloat(e.target.value);
            if (value < 0) {
                e.target.value = 0;
            }
        });
    }

    // Form validation
    const salesmanForm = document.querySelector('form');
    if (salesmanForm) {
        salesmanForm.addEventListener('submit', function(e) {
            const requiredFields = salesmanForm.querySelectorAll('[required]');
            let isValid = true;

            requiredFields.forEach(function(field) {
                if (!field.value.trim()) {
                    field.classList.add('is-invalid');
                    isValid = false;
                } else {
                    field.classList.remove('is-invalid');
                }
            });

            if (!isValid) {
                e.preventDefault();
                alert('Please fill in all required fields.');
            }
        });
    }

    // Search functionality
    const searchInput = document.querySelector('input[name="search"]');
    if (searchInput) {
        let searchTimeout;
        searchInput.addEventListener('input', function(e) {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(function() {
                e.target.form.submit();
            }, 500);
        });
    }

    // Status filter
    const statusFilter = document.querySelector('select[name="status"]');
    if (statusFilter) {
        statusFilter.addEventListener('change', function() {
            this.form.submit();
        });
    }

    // Department filter
    const departmentFilter = document.querySelector('select[name="department"]');
    if (departmentFilter) {
        departmentFilter.addEventListener('change', function() {
            this.form.submit();
        });
    }

    // Delete confirmation
    const deleteButtons = document.querySelectorAll('.btn-delete');
    deleteButtons.forEach(function(button) {
        button.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to delete this salesman? This action cannot be undone.')) {
                e.preventDefault();
            }
        });
    });

    // Auto-generate salesman code
    const codeInput = document.querySelector('input[name="salesman_code"]');
    const firstNameInput = document.querySelector('input[name="first_name"]');
    const lastNameInput = document.querySelector('input[name="last_name"]');
    
    if (codeInput && firstNameInput && lastNameInput) {
        function generateCode() {
            if (firstNameInput.value && lastNameInput.value && !codeInput.value) {
                const prefix = 'SAL';
                const timestamp = Date.now().toString().slice(-3);
                codeInput.value = prefix + timestamp;
            }
        }

        firstNameInput.addEventListener('blur', generateCode);
        lastNameInput.addEventListener('blur', generateCode);
    }
}); 