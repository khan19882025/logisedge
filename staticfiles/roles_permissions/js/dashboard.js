// Roles & Permissions Dashboard JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize dashboard functionality
    initializeDashboard();
    
    // Add animation classes to cards
    animateCards();
    
    // Initialize tooltips
    initializeTooltips();
    
    // Initialize real-time updates
    initializeRealTimeUpdates();
});

function initializeDashboard() {
    console.log('Initializing Roles & Permissions Dashboard...');
    
    // Add loading states to buttons
    addLoadingStates();
    
    // Initialize search functionality
    initializeSearch();
    
    // Initialize quick action buttons
    initializeQuickActions();
}

function animateCards() {
    // Add fade-in animation to cards
    const cards = document.querySelectorAll('.card');
    cards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
            card.style.transition = 'all 0.5s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, index * 100);
    });
}

function initializeTooltips() {
    // Initialize Bootstrap tooltips if available
    if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
}

function addLoadingStates() {
    // Add loading states to action buttons
    const actionButtons = document.querySelectorAll('.btn-block, .btn');
    
    actionButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            // Don't add loading state for navigation links
            if (this.tagName === 'A' && this.href) {
                return;
            }
            
            const originalText = this.innerHTML;
            this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading...';
            this.classList.add('loading');
            this.disabled = true;
            
            // Reset after 3 seconds if no response
            setTimeout(() => {
                this.innerHTML = originalText;
                this.classList.remove('loading');
                this.disabled = false;
            }, 3000);
        });
    });
}

function initializeSearch() {
    // Add search functionality to tables
    const searchInputs = document.querySelectorAll('.search-input');
    
    searchInputs.forEach(input => {
        input.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            const table = this.closest('.card').querySelector('table');
            
            if (table) {
                const rows = table.querySelectorAll('tbody tr');
                
                rows.forEach(row => {
                    const text = row.textContent.toLowerCase();
                    if (text.includes(searchTerm)) {
                        row.style.display = '';
                    } else {
                        row.style.display = 'none';
                    }
                });
            }
        });
    });
}

function initializeQuickActions() {
    // Add confirmation dialogs to delete actions
    const deleteButtons = document.querySelectorAll('.btn-danger');
    
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to perform this action?')) {
                e.preventDefault();
            }
        });
    });
    
    // Add hover effects to navigation cards
    const navCards = document.querySelectorAll('.navigation-card');
    
    navCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-5px)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });
}

function initializeRealTimeUpdates() {
    // Update statistics every 30 seconds
    setInterval(updateStatistics, 30000);
    
    // Update recent activities every 60 seconds
    setInterval(updateRecentActivities, 60000);
}

function updateStatistics() {
    // Fetch updated statistics via AJAX
    fetch('/roles-permissions/api/statistics/')
        .then(response => response.json())
        .then(data => {
            updateStatisticCard('total-roles', data.total_roles);
            updateStatisticCard('active-roles', data.active_roles);
            updateStatisticCard('total-users', data.total_users);
            updateStatisticCard('total-permissions', data.total_permissions);
        })
        .catch(error => {
            console.error('Error updating statistics:', error);
        });
}

function updateStatisticCard(cardId, value) {
    const card = document.getElementById(cardId);
    if (card) {
        const valueElement = card.querySelector('.h5');
        if (valueElement) {
            // Animate the number change
            animateNumberChange(valueElement, parseInt(valueElement.textContent), value);
        }
    }
}

function animateNumberChange(element, startValue, endValue) {
    const duration = 1000;
    const startTime = performance.now();
    
    function updateNumber(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        
        const currentValue = Math.floor(startValue + (endValue - startValue) * progress);
        element.textContent = currentValue;
        
        if (progress < 1) {
            requestAnimationFrame(updateNumber);
        }
    }
    
    requestAnimationFrame(updateNumber);
}

function updateRecentActivities() {
    // Fetch updated recent activities
    fetch('/roles-permissions/api/recent-activities/')
        .then(response => response.json())
        .then(data => {
            updateAuditLogsTable(data.audit_logs);
            updateAccessLogsTable(data.access_logs);
        })
        .catch(error => {
            console.error('Error updating recent activities:', error);
        });
}

function updateAuditLogsTable(auditLogs) {
    const table = document.querySelector('.audit-logs-table tbody');
    if (table && auditLogs) {
        table.innerHTML = '';
        
        auditLogs.forEach(log => {
            const row = createAuditLogRow(log);
            table.appendChild(row);
        });
    }
}

function updateAccessLogsTable(accessLogs) {
    const table = document.querySelector('.access-logs-table tbody');
    if (table && accessLogs) {
        table.innerHTML = '';
        
        accessLogs.forEach(log => {
            const row = createAccessLogRow(log);
            table.appendChild(row);
        });
    }
}

function createAuditLogRow(log) {
    const row = document.createElement('tr');
    row.innerHTML = `
        <td><small>${log.user}</small></td>
        <td><span class="badge badge-${getActionBadgeClass(log.action)}">${log.action}</span></td>
        <td><small>${log.target || '-'}</small></td>
        <td><small>${log.timestamp}</small></td>
    `;
    return row;
}

function createAccessLogRow(log) {
    const row = document.createElement('tr');
    row.innerHTML = `
        <td><small>${log.user}</small></td>
        <td><small>${log.access_type}</small></td>
        <td><span class="badge badge-${log.success ? 'success' : 'danger'}">${log.success ? 'Success' : 'Failed'}</span></td>
        <td><small>${log.timestamp}</small></td>
    `;
    return row;
}

function getActionBadgeClass(action) {
    switch (action) {
        case 'create': return 'success';
        case 'update': return 'info';
        case 'delete': return 'danger';
        default: return 'secondary';
    }
}

// Utility functions
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 5000);
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}

function formatTimeAgo(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diffInSeconds = Math.floor((now - date) / 1000);
    
    if (diffInSeconds < 60) {
        return `${diffInSeconds} seconds ago`;
    } else if (diffInSeconds < 3600) {
        const minutes = Math.floor(diffInSeconds / 60);
        return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
    } else if (diffInSeconds < 86400) {
        const hours = Math.floor(diffInSeconds / 3600);
        return `${hours} hour${hours > 1 ? 's' : ''} ago`;
    } else {
        const days = Math.floor(diffInSeconds / 86400);
        return `${days} day${days > 1 ? 's' : ''} ago`;
    }
}

// Export functions for use in other scripts
window.RolesPermissionsDashboard = {
    showNotification,
    formatDate,
    formatTimeAgo,
    updateStatistics,
    updateRecentActivities
};
