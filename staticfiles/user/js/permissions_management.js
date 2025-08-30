// Permissions Management JavaScript

class PermissionsManager {
    constructor() {
        this.selectedUser = null;
        this.selectedModule = null;
        this.menuStructure = {};
        this.permissionTypes = [];
        this.userPermissions = {};
        this.csrfToken = '';
        
        this.init();
    }
    
    init() {
        this.loadData();
        this.bindEvents();
        this.getCsrfToken();
    }
    
    loadData() {
        // Load menu structure from hidden script tag
        const menuScript = document.getElementById('menuStructure');
        if (menuScript) {
            this.menuStructure = JSON.parse(menuScript.textContent);
        }
        
        // Load permission types
        const permScript = document.getElementById('permissionTypes');
        if (permScript) {
            this.permissionTypes = JSON.parse(permScript.textContent);
        }
    }
    
    getCsrfToken() {
        const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
        if (csrfInput) {
            this.csrfToken = csrfInput.value;
        } else {
            // Try to get from cookie
            const cookies = document.cookie.split(';');
            for (let cookie of cookies) {
                const [name, value] = cookie.trim().split('=');
                if (name === 'csrftoken') {
                    this.csrfToken = value;
                    break;
                }
            }
        }
    }
    
    bindEvents() {
        // User selection
        document.querySelectorAll('.user-item').forEach(item => {
            item.addEventListener('click', (e) => this.selectUser(e));
        });
        
        // Module selection
        document.querySelectorAll('.menu-card').forEach(card => {
            card.addEventListener('click', (e) => this.selectModule(e));
        });
        
        // User search
        const userSearch = document.getElementById('userSearch');
        if (userSearch) {
            userSearch.addEventListener('input', (e) => this.filterUsers(e.target.value));
        }
        
        // Save permissions
        const saveBtn = document.getElementById('savePermissions');
        if (saveBtn) {
            saveBtn.addEventListener('click', () => this.savePermissions());
        }
        
        // Menu select all checkboxes
        document.querySelectorAll('.menu-select-all').forEach(checkbox => {
            checkbox.addEventListener('change', (e) => this.toggleMenuPermissions(e));
        });
    }
    
    selectUser(event) {
        const userItem = event.currentTarget;
        const userId = userItem.dataset.userId;
        
        // Remove previous selection
        document.querySelectorAll('.user-item').forEach(item => {
            item.classList.remove('selected');
        });
        
        // Add selection to clicked user
        userItem.classList.add('selected');
        
        this.selectedUser = userId;
        this.loadUserPermissions(userId);
        
        // Update UI
        const userName = userItem.querySelector('.user-name').textContent;
        document.getElementById('selectedUserName').textContent = `Managing: ${userName}`;
        
        // Enable save button if both user and module are selected
        this.updateSaveButton();
        
        // Clear module selection
        this.clearModuleSelection();
    }
    
    selectModule(event) {
        const moduleCard = event.currentTarget;
        const moduleName = moduleCard.dataset.module;
        
        // Remove previous selection
        document.querySelectorAll('.menu-card').forEach(card => {
            card.classList.remove('selected');
        });
        
        // Add selection to clicked module
        moduleCard.classList.add('selected');
        
        this.selectedModule = moduleName;
        
        // Update UI
        document.getElementById('selectedModuleName').textContent = `Module: ${moduleName}`;
        
        // Load permissions for this module
        this.loadModulePermissions(moduleName);
        
        // Enable save button if both user and module are selected
        this.updateSaveButton();
    }
    
    loadUserPermissions(userId) {
        if (!userId) return;
        
        const formData = new FormData();
        formData.append('action', 'get_user_permissions');
        formData.append('user_id', userId);
        formData.append('csrfmiddlewaretoken', this.csrfToken);
        
        fetch(window.location.href, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.userPermissions = data.permissions;
                // Refresh permissions display if module is selected
                if (this.selectedModule) {
                    this.loadModulePermissions(this.selectedModule);
                }
            } else {
                this.showError('Failed to load user permissions: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            this.showError('Failed to load user permissions');
        });
    }
    
    loadModulePermissions(moduleName) {
        if (!this.selectedUser) {
            this.showError('Please select a user first');
            return;
        }
        
        const submenus = this.menuStructure[moduleName] || [];
        const permissionsContent = document.getElementById('permissionsContent');
        
        if (submenus.length === 0) {
            permissionsContent.innerHTML = `
                <div class="no-selection">
                    <i class="fas fa-exclamation-triangle"></i>
                    <p>No permissions available for this module</p>
                </div>
            `;
            return;
        }
        
        // Create permissions table
        let tableHTML = `
            <div class="permissions-header">
                <h4>${moduleName} Permissions</h4>
                <label class="checkbox-container">
                    <input type="checkbox" id="selectAllModule" data-module="${moduleName}">
                    <span class="checkmark"></span>
                    <span class="label-text">Select All ${moduleName}</span>
                </label>
            </div>
            <table class="permissions-table">
                <thead>
                    <tr>
                        <th>Submenu</th>
        `;
        
        // Add permission type headers
        this.permissionTypes.forEach(type => {
            tableHTML += `<th class="permission-cell">${type.charAt(0).toUpperCase() + type.slice(1)}</th>`;
        });
        
        tableHTML += `
                        <th class="permission-cell">All</th>
                    </tr>
                </thead>
                <tbody>
        `;
        
        // Add submenu rows
        submenus.forEach(submenu => {
            tableHTML += `
                <tr>
                    <td class="submenu-item">${submenu.name}</td>
            `;
            
            // Add permission checkboxes
            this.permissionTypes.forEach(type => {
                const permissionCode = `${submenu.codename}_${type}`;
                const isChecked = this.userPermissions[permissionCode] ? 'checked' : '';
                
                tableHTML += `
                    <td class="permission-cell">
                        <label class="checkbox-container">
                            <input type="checkbox" 
                                   class="permission-checkbox" 
                                   data-submenu="${submenu.codename}" 
                                   data-type="${type}" 
                                   data-permission="${permissionCode}" 
                                   ${isChecked}>
                            <span class="checkmark"></span>
                        </label>
                    </td>
                `;
            });
            
            // Add "Select All" for this submenu
            tableHTML += `
                <td class="permission-cell">
                    <label class="checkbox-container">
                        <input type="checkbox" 
                               class="submenu-select-all" 
                               data-submenu="${submenu.codename}">
                        <span class="checkmark"></span>
                    </label>
                </td>
                </tr>
            `;
        });
        
        tableHTML += `
                </tbody>
            </table>
        `;
        
        permissionsContent.innerHTML = tableHTML;
        permissionsContent.classList.add('fade-in');
        
        // Bind new events
        this.bindPermissionEvents();
        this.updateSelectAllStates();
    }
    
    bindPermissionEvents() {
        // Individual permission checkboxes
        document.querySelectorAll('.permission-checkbox').forEach(checkbox => {
            checkbox.addEventListener('change', () => this.updateSelectAllStates());
        });
        
        // Submenu select all checkboxes
        document.querySelectorAll('.submenu-select-all').forEach(checkbox => {
            checkbox.addEventListener('change', (e) => this.toggleSubmenuPermissions(e));
        });
        
        // Module select all checkbox
        const moduleSelectAll = document.getElementById('selectAllModule');
        if (moduleSelectAll) {
            moduleSelectAll.addEventListener('change', (e) => this.toggleModulePermissions(e));
        }
    }
    
    toggleSubmenuPermissions(event) {
        const checkbox = event.target;
        const submenuCode = checkbox.dataset.submenu;
        const isChecked = checkbox.checked;
        
        // Toggle all permissions for this submenu
        document.querySelectorAll(`[data-submenu="${submenuCode}"].permission-checkbox`).forEach(permCheckbox => {
            permCheckbox.checked = isChecked;
        });
        
        this.updateSelectAllStates();
    }
    
    toggleModulePermissions(event) {
        const checkbox = event.target;
        const isChecked = checkbox.checked;
        
        // Toggle all permission checkboxes in the module
        document.querySelectorAll('.permission-checkbox').forEach(permCheckbox => {
            permCheckbox.checked = isChecked;
        });
        
        // Toggle all submenu select all checkboxes
        document.querySelectorAll('.submenu-select-all').forEach(submenuCheckbox => {
            submenuCheckbox.checked = isChecked;
        });
    }
    
    updateSelectAllStates() {
        // Update submenu select all states
        document.querySelectorAll('.submenu-select-all').forEach(submenuCheckbox => {
            const submenuCode = submenuCheckbox.dataset.submenu;
            const submenuPermissions = document.querySelectorAll(`[data-submenu="${submenuCode}"].permission-checkbox`);
            const checkedCount = Array.from(submenuPermissions).filter(cb => cb.checked).length;
            
            submenuCheckbox.checked = checkedCount === submenuPermissions.length;
            submenuCheckbox.indeterminate = checkedCount > 0 && checkedCount < submenuPermissions.length;
        });
        
        // Update module select all state
        const moduleSelectAll = document.getElementById('selectAllModule');
        if (moduleSelectAll) {
            const allPermissions = document.querySelectorAll('.permission-checkbox');
            const checkedCount = Array.from(allPermissions).filter(cb => cb.checked).length;
            
            moduleSelectAll.checked = checkedCount === allPermissions.length;
            moduleSelectAll.indeterminate = checkedCount > 0 && checkedCount < allPermissions.length;
        }
    }
    
    filterUsers(searchTerm) {
        const userItems = document.querySelectorAll('.user-item');
        const term = searchTerm.toLowerCase();
        
        userItems.forEach(item => {
            const userName = item.querySelector('.user-name').textContent.toLowerCase();
            const username = item.querySelector('.username').textContent.toLowerCase();
            const department = item.querySelector('.department');
            const departmentText = department ? department.textContent.toLowerCase() : '';
            
            const matches = userName.includes(term) || 
                          username.includes(term) || 
                          departmentText.includes(term);
            
            item.style.display = matches ? 'flex' : 'none';
        });
    }
    
    savePermissions() {
        if (!this.selectedUser) {
            this.showError('Please select a user');
            return;
        }
        
        // Collect all checked permissions
        const checkedPermissions = [];
        document.querySelectorAll('.permission-checkbox:checked').forEach(checkbox => {
            checkedPermissions.push(checkbox.dataset.permission);
        });
        
        // Show loading state
        const saveBtn = document.getElementById('savePermissions');
        const originalText = saveBtn.innerHTML;
        saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';
        saveBtn.disabled = true;
        
        // Prepare form data
        const formData = new FormData();
        formData.append('action', 'save_permissions');
        formData.append('user_id', this.selectedUser);
        formData.append('csrfmiddlewaretoken', this.csrfToken);
        
        checkedPermissions.forEach(permission => {
            formData.append('permissions[]', permission);
        });
        
        // Send request
        fetch(window.location.href, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.showSuccess(data.message);
                // Reload user permissions
                this.loadUserPermissions(this.selectedUser);
            } else {
                this.showError('Failed to save permissions: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            this.showError('Failed to save permissions');
        })
        .finally(() => {
            // Restore button state
            saveBtn.innerHTML = originalText;
            saveBtn.disabled = false;
        });
    }
    
    updateSaveButton() {
        const saveBtn = document.getElementById('savePermissions');
        const hasUser = this.selectedUser !== null;
        const hasModule = this.selectedModule !== null;
        
        saveBtn.disabled = !(hasUser && hasModule);
    }
    
    clearModuleSelection() {
        document.querySelectorAll('.menu-card').forEach(card => {
            card.classList.remove('selected');
        });
        
        this.selectedModule = null;
        document.getElementById('selectedModuleName').textContent = 'Select a module to view permissions';
        
        // Clear permissions content
        const permissionsContent = document.getElementById('permissionsContent');
        permissionsContent.innerHTML = `
            <div class="no-selection">
                <i class="fas fa-hand-pointer"></i>
                <p>Select a module to manage permissions</p>
            </div>
        `;
        
        this.updateSaveButton();
    }
    
    showSuccess(message) {
        const statusDiv = document.getElementById('saveStatus');
        statusDiv.textContent = message;
        statusDiv.className = 'save-status success';
        
        setTimeout(() => {
            statusDiv.textContent = '';
            statusDiv.className = 'save-status';
        }, 5000);
    }
    
    showError(message) {
        const statusDiv = document.getElementById('saveStatus');
        statusDiv.textContent = message;
        statusDiv.className = 'save-status error';
        
        setTimeout(() => {
            statusDiv.textContent = '';
            statusDiv.className = 'save-status';
        }, 5000);
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    new PermissionsManager();
});

// Add CSRF token to all AJAX requests
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

// Set up CSRF token for all AJAX requests
const csrftoken = getCookie('csrftoken');
if (csrftoken) {
    // Add to all fetch requests
    const originalFetch = window.fetch;
    window.fetch = function(url, options = {}) {
        if (options.method && options.method.toUpperCase() !== 'GET') {
            options.headers = options.headers || {};
            options.headers['X-CSRFToken'] = csrftoken;
        }
        return originalFetch(url, options);
    };
}