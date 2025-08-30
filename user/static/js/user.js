// User Module JavaScript

// Password Management Functions
function generateTemporaryPassword() {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*';
    let password = '';
    for (let i = 0; i < 12; i++) {
        password += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return password;
}

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

    // Password Management
    const generateBtn = document.getElementById('generatePassword');
    const tempPasswordInput = document.getElementById('temporary_password');
    
    if (generateBtn && tempPasswordInput) {
        generateBtn.addEventListener('click', function() {
            tempPasswordInput.value = generateTemporaryPassword();
        });
        
        // Generate initial password
        tempPasswordInput.value = generateTemporaryPassword();
    }
    
    // Password change form validation
    const changePasswordForm = document.getElementById('changePasswordForm');
    if (changePasswordForm) {
        changePasswordForm.addEventListener('submit', function(e) {
            const newPassword1 = document.getElementById('new_password1').value;
            const newPassword2 = document.getElementById('new_password2').value;
            
            if (newPassword1 !== newPassword2) {
                e.preventDefault();
                alert('New passwords do not match!');
                return false;
            }
            
            if (newPassword1.length < 8) {
                e.preventDefault();
                alert('Password must be at least 8 characters long!');
                return false;
            }
        });
    }
    
    // Reset password form validation
    const resetPasswordForm = document.getElementById('resetPasswordForm');
    if (resetPasswordForm) {
        resetPasswordForm.addEventListener('submit', function(e) {
            const adminPassword = document.getElementById('admin_password').value;
            const tempPassword = document.getElementById('temporary_password').value;
            
            if (!adminPassword) {
                e.preventDefault();
                alert('Please enter your admin password!');
                return false;
            }
            
            if (!tempPassword) {
                e.preventDefault();
                alert('Please generate a temporary password!');
                return false;
            }
            
            if (!confirm('Are you sure you want to reset this user\'s password? This action cannot be undone.')) {
                e.preventDefault();
                return false;
            }
        });
    }

    // Tab functionality
    const tabButtons = document.querySelectorAll('[data-bs-toggle="tab"]');
    tabButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const target = this.getAttribute('data-bs-target');
            const tab = new bootstrap.Tab(this);
            tab.show();
            
            // Update active tab indicator
            tabButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
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
            if (!confirm('Are you sure you want to delete this user? This action cannot be undone.')) {
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

    // Profile picture preview
    const profilePictureInput = document.querySelector('input[type="file"]');
    if (profilePictureInput) {
        profilePictureInput.addEventListener('change', function() {
            const file = this.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    const preview = document.querySelector('.profile-picture-preview');
                    if (preview) {
                        preview.src = e.target.result;
                    } else {
                        // Create preview if it doesn't exist
                        const newPreview = document.createElement('img');
                        newPreview.src = e.target.result;
                        newPreview.className = 'profile-picture-preview mt-2';
                        profilePictureInput.parentNode.appendChild(newPreview);
                    }
                };
                reader.readAsDataURL(file);
            }
        });
    }

    // Role change handler for permissions
    const roleSelect = document.querySelector('select[name="role"]');
    if (roleSelect) {
        roleSelect.addEventListener('change', function() {
            const roleId = this.value;
            if (roleId) {
                loadRolePermissions(roleId);
            } else {
                clearPermissions();
            }
        });
    }

    // Phone number formatting
    const phoneInput = document.querySelector('input[name="phone"]');
    if (phoneInput) {
        phoneInput.addEventListener('input', function() {
            let value = this.value.replace(/\D/g, '');
            if (value.length > 0) {
                if (value.length <= 3) {
                    value = `(${value}`;
                } else if (value.length <= 6) {
                    value = `(${value.slice(0, 3)}) ${value.slice(3)}`;
                } else {
                    value = `(${value.slice(0, 3)}) ${value.slice(3, 6)}-${value.slice(6, 10)}`;
                }
            }
            this.value = value;
        });
    }

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
            
            localStorage.setItem('user_form_draft', JSON.stringify(formObject));
        });
    });

    // Load draft on page load
    const savedDraft = localStorage.getItem('user_form_draft');
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
            localStorage.removeItem('user_form_draft');
        });
    });
});

// Load role permissions via AJAX
function loadRolePermissions(roleId) {
    fetch(`/user/api/role/${roleId}/permissions/`)
        .then(response => response.json())
        .then(data => {
            displayPermissions(data.permissions);
        })
        .catch(error => {
            console.error('Error loading permissions:', error);
        });
}

// Display permissions in the permissions container
function displayPermissions(selectedPermissions) {
    const permissionsList = document.getElementById('permissionsList');
    if (!permissionsList) return;

    // Get all available permissions from the page
    const allPermissions = Array.from(document.querySelectorAll('[data-permission-id]')).map(el => ({
        id: el.dataset.permissionId,
        name: el.dataset.permissionName,
        description: el.dataset.permissionDescription
    }));

    if (allPermissions.length === 0) {
        // If no permissions found in DOM, create some default ones
        allPermissions.push(
            { id: 1, name: 'View Users', description: 'Can view user list and details' },
            { id: 2, name: 'Create Users', description: 'Can create new users' },
            { id: 3, name: 'Edit Users', description: 'Can edit existing users' },
            { id: 4, name: 'Delete Users', description: 'Can delete users' },
            { id: 5, name: 'Manage Roles', description: 'Can manage user roles' },
            { id: 6, name: 'Manage Permissions', description: 'Can manage system permissions' }
        );
    }

    permissionsList.innerHTML = '';
    
    allPermissions.forEach(permission => {
        const isSelected = selectedPermissions.includes(parseInt(permission.id));
        const permissionElement = document.createElement('div');
        permissionElement.className = `col-md-6 col-lg-4 mb-2`;
        permissionElement.innerHTML = `
            <div class="permission-item ${isSelected ? 'selected' : ''}" 
                 data-permission-id="${permission.id}">
                <div class="form-check">
                    <input class="form-check-input" type="checkbox" 
                           id="permission_${permission.id}" 
                           value="${permission.id}"
                           ${isSelected ? 'checked' : ''}>
                    <label class="form-check-label" for="permission_${permission.id}">
                        <strong>${permission.name}</strong>
                        <br>
                        <small class="text-muted">${permission.description}</small>
                    </label>
                </div>
            </div>
        `;
        permissionsList.appendChild(permissionElement);
    });

    // Add event listeners to checkboxes
    const checkboxes = permissionsList.querySelectorAll('input[type="checkbox"]');
    checkboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            const permissionItem = this.closest('.permission-item');
            if (this.checked) {
                permissionItem.classList.add('selected');
            } else {
                permissionItem.classList.remove('selected');
            }
        });
    });
}

// Clear permissions display
function clearPermissions() {
    const permissionsList = document.getElementById('permissionsList');
    if (permissionsList) {
        permissionsList.innerHTML = '<div class="col-12 text-center text-muted">Select a role to view permissions</div>';
    }
}

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