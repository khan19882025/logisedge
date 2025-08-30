// Permissions Management JavaScript

class PermissionsManager {
    constructor() {
        this.selectedUser = null;
        this.selectedModule = null;
        this.menuStructure = {};
        this.userPermissions = {};
        this.currentPermissions = {};
        
        this.init();
    }
    
    init() {
        this.loadData();
        this.bindEvents();
        this.setupSearch();
    }
    
    loadData() {
        // Load menu structure from script tag
        const menuScript = document.getElementById('menuStructure');
        if (menuScript) {
            try {
                this.menuStructure = JSON.parse(menuScript.textContent);
            } catch (e) {
                console.error('Error parsing menu structure:', e);
            }
        }
        
        // Load user permissions from script tag
        const permissionsScript = document.getElementById('userPermissions');
        if (permissionsScript) {
            try {
                this.userPermissions = JSON.parse(permissionsScript.textContent);
            } catch (e) {
                console.error('Error parsing user permissions:', e);
            }
        }
    }
    
    bindEvents() {
        // User selection
        document.querySelectorAll('.user-item').forEach(item => {
            item.addEventListener('click', (e) => this.selectUser(e.currentTarget));
        });
        
        // Module selection
        document.querySelectorAll('.menu-item').forEach(item => {
            item.addEventListener('click', (e) => this.selectModule(e.currentTarget));
        });
        
        // Permission actions
        const selectAllBtn = document.getElementById('selectAllBtn');
        const clearAllBtn = document.getElementById('clearAllBtn');
        const saveBtn = document.getElementById('savePermissionsBtn');
        
        if (selectAllBtn) {
            selectAllBtn.addEventListener('click', () => this.selectAllPermissions());
        }
        
        if (clearAllBtn) {
            clearAllBtn.addEventListener('click', () => this.clearAllPermissions());
        }
        
        if (saveBtn) {
            saveBtn.addEventListener('click', () => this.savePermissions());
        }
    }
    
    setupSearch() {
        const searchInput = document.getElementById('userSearch');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => this.filterUsers(e.target.value));
        }
    }
    
    selectUser(userElement) {
        // Remove active class from all users
        document.querySelectorAll('.user-item').forEach(item => {
            item.classList.remove('active');
        });
        
        // Add active class to selected user
        userElement.classList.add('active');
        
        // Store selected user data
        this.selectedUser = {
            id: userElement.dataset.userId,
            username: userElement.dataset.username,
            name: userElement.querySelector('.user-name').textContent
        };
        
        // Update selected user info
        this.updateSelectedUserInfo();
        
        // Load user permissions
        this.loadUserPermissions();
        
        // Reset module selection
        this.selectedModule = null;
        this.clearModuleSelection();
        this.clearPermissionsList();
    }
    
    selectModule(moduleElement) {
        // Remove active class from all modules
        document.querySelectorAll('.menu-item').forEach(item => {
            item.classList.remove('active');
        });
        
        // Add active class to selected module
        moduleElement.classList.add('active');
        
        // Store selected module
        this.selectedModule = moduleElement.dataset.module;
        
        // Load permissions for this module
        this.loadModulePermissions();
    }
    
    updateSelectedUserInfo() {
        const userInfo = document.getElementById('selectedUserInfo');
        const userName = document.getElementById('selectedUserName');
        
        if (userInfo && userName && this.selectedUser) {
            userName.textContent = this.selectedUser.name;
            userInfo.style.display = 'block';
        }
    }
    
    loadUserPermissions() {
        if (!this.selectedUser) return;
        
        // In a real application, you would make an AJAX call here
        // For now, we'll use the data loaded from the script tag
        const userId = this.selectedUser.id;
        this.currentPermissions = this.userPermissions[userId] || {};
    }
    
    loadModulePermissions() {
        if (!this.selectedUser || !this.selectedModule) return;
        
        const permissionsList = document.getElementById('permissionsList');
        const permissionsTitle = document.getElementById('permissionsTitle');
        const permissionActions = document.getElementById('permissionActions');
        const panelFooter = document.getElementById('panelFooter');
        
        if (!permissionsList || !this.menuStructure[this.selectedModule]) return;
        
        // Update title
        if (permissionsTitle) {
            permissionsTitle.innerHTML = `<i class="bi bi-shield-check me-2"></i>${this.selectedModule} Permissions`;
        }
        
        // Show action buttons and footer
        if (permissionActions) permissionActions.style.display = 'block';
        if (panelFooter) panelFooter.style.display = 'block';
        
        // Build permissions table
        const permissions = this.menuStructure[this.selectedModule];
        const permissionTypes = ['view', 'new', 'edit', 'delete', 'print'];
        
        let html = `
            <div class="permissions-table-container">
                <table class="table table-bordered table-hover">
                    <thead class="table-dark">
                        <tr>
                            <th style="width: 30%;">Menu Item</th>
                            <th style="width: 14%;">View</th>
                            <th style="width: 14%;">New</th>
                            <th style="width: 14%;">Edit</th>
                            <th style="width: 14%;">Delete</th>
                            <th style="width: 14%;">Print</th>
                        </tr>
                    </thead>
                    <tbody>
        `;
        
        permissions.forEach(permission => {
            html += `
                <tr>
                    <td class="fw-semibold">${permission.name}</td>
            `;
            
            permissionTypes.forEach(type => {
                const permissionCode = `${permission.codename}_${type}`;
                const isChecked = this.currentPermissions[permissionCode] || false;
                
                html += `
                    <td class="text-center">
                        <div class="form-check">
                            <input class="form-check-input" type="checkbox" 
                                   id="perm_${permissionCode}" 
                                   data-codename="${permissionCode}"
                                   data-menu-item="${permission.codename}"
                                   data-permission-type="${type}"
                                   ${isChecked ? 'checked' : ''}>
                        </div>
                    </td>
                `;
            });
            
            html += '</tr>';
        });
        
        html += `
                    </tbody>
                </table>
            </div>
        `;
        
        permissionsList.innerHTML = html;
        
        // Bind permission toggle events
        this.bindPermissionToggles();
    }
    
    bindPermissionToggles() {
        document.querySelectorAll('.permission-item input[type="checkbox"]').forEach(checkbox => {
            checkbox.addEventListener('change', (e) => {
                const codename = e.target.dataset.codename;
                this.currentPermissions[codename] = e.target.checked;
            });
        });
    }
    
    selectAllPermissions() {
        const checkboxes = document.querySelectorAll('#permissionsList input[type="checkbox"]');
        checkboxes.forEach(checkbox => {
            checkbox.checked = true;
            this.currentPermissions[checkbox.dataset.codename] = true;
        });
    }
    
    clearAllPermissions() {
        const checkboxes = document.querySelectorAll('#permissionsList input[type="checkbox"]');
        checkboxes.forEach(checkbox => {
            checkbox.checked = false;
            this.currentPermissions[checkbox.dataset.codename] = false;
        });
    }
    
    clearModuleSelection() {
        document.querySelectorAll('.menu-item').forEach(item => {
            item.classList.remove('active');
        });
    }
    
    clearPermissionsList() {
        const permissionsList = document.getElementById('permissionsList');
        const permissionsTitle = document.getElementById('permissionsTitle');
        const permissionActions = document.getElementById('permissionActions');
        const panelFooter = document.getElementById('panelFooter');
        
        if (permissionsList) {
            permissionsList.innerHTML = `
                <div class="no-selection">
                    <i class="bi bi-arrow-left-circle"></i>
                    <p>Select a module to manage permissions</p>
                </div>
            `;
        }
        
        if (permissionsTitle) {
            permissionsTitle.innerHTML = '<i class="bi bi-shield-check me-2"></i>Select a Module';
        }
        
        if (permissionActions) permissionActions.style.display = 'none';
        if (panelFooter) panelFooter.style.display = 'none';
    }
    
    filterUsers(searchTerm) {
        const userItems = document.querySelectorAll('.user-item');
        const term = searchTerm.toLowerCase();
        
        userItems.forEach(item => {
            const userName = item.querySelector('.user-name').textContent.toLowerCase();
            const userEmail = item.querySelector('.user-details').textContent.toLowerCase();
            const userIdElement = item.querySelector('.user-id');
            const userId = userIdElement ? userIdElement.textContent.toLowerCase() : '';
            
            const matches = userName.includes(term) || userEmail.includes(term) || userId.includes(term);
            item.style.display = matches ? 'flex' : 'none';
        });
    }
    
    savePermissions() {
        if (!this.selectedUser) {
            this.showAlert('Please select a user first.', 'warning');
            return;
        }
        
        const saveBtn = document.getElementById('savePermissionsBtn');
        if (saveBtn) {
            saveBtn.disabled = true;
            saveBtn.innerHTML = '<i class="spinner-border spinner-border-sm me-1"></i>Saving...';
        }
        
        // Prepare data for saving
        const data = {
            user_id: this.selectedUser.id,
            permissions: this.currentPermissions,
            csrfmiddlewaretoken: this.getCSRFToken()
        };
        
        // Make AJAX request to save permissions
        fetch('/user/api/save-permissions/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCSRFToken()
            },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.showAlert('Permissions saved successfully!', 'success');
                // Update the userPermissions cache
                this.userPermissions[this.selectedUser.id] = this.currentPermissions;
            } else {
                this.showAlert('Error saving permissions: ' + (data.error || 'Unknown error'), 'danger');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            this.showAlert('Error saving permissions. Please try again.', 'danger');
        })
        .finally(() => {
            if (saveBtn) {
                saveBtn.disabled = false;
                saveBtn.innerHTML = '<i class="bi bi-check-lg me-1"></i>Save Permissions';
            }
        });
    }
    
    getCSRFToken() {
        const token = document.querySelector('[name=csrfmiddlewaretoken]');
        return token ? token.value : '';
    }
    
    showAlert(message, type = 'info') {
        // Remove existing alerts
        document.querySelectorAll('.alert-floating').forEach(alert => alert.remove());
        
        // Create new alert
        const alert = document.createElement('div');
        alert.className = `alert alert-${type} alert-dismissible fade show alert-floating`;
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(alert);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (alert.parentNode) {
                alert.remove();
            }
        }, 5000);
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    new PermissionsManager();
});