/**
 * Email Configuration Dashboard JavaScript
 * Handles interactive features and real-time updates
 */

class EmailConfigurationDashboard {
    constructor() {
        this.healthData = null;
        this.refreshInterval = null;
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadInitialData();
        this.startAutoRefresh();
    }

    bindEvents() {
        // Bind refresh button events
        const refreshButtons = document.querySelectorAll('[data-refresh]');
        refreshButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                this.refreshData(button.dataset.refresh);
            });
        });

        // Bind quick action buttons
        const quickActionButtons = document.querySelectorAll('.quick-actions .btn');
        quickActionButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                this.handleQuickAction(e, button);
            });
        });

        // Bind health monitor refresh
        const healthRefreshBtn = document.querySelector('[onclick="refreshHealthData()"]');
        if (healthRefreshBtn) {
            healthRefreshBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.refreshHealthData();
            });
        }
    }

    loadInitialData() {
        // Load health data on page load
        this.loadHealthData();
        
        // Load any other initial data
        this.loadStatistics();
    }

    startAutoRefresh() {
        // Auto-refresh health data every 30 seconds
        this.refreshInterval = setInterval(() => {
            this.refreshHealthData();
        }, 30000);
    }

    async loadHealthData() {
        try {
            const response = await fetch('/utilities/email-configuration/api/health/');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            this.healthData = data.health_data;
            this.displayHealthData(this.healthData);
            
        } catch (error) {
            console.error('Error loading health data:', error);
            this.showError('Failed to load configuration health data', error.message);
        }
    }

    async loadStatistics() {
        try {
            // Load additional statistics if needed
            const response = await fetch('/utilities/email-configuration/api/statistics/');
            if (response.ok) {
                const data = await response.json();
                this.updateStatistics(data);
            }
        } catch (error) {
            console.error('Error loading statistics:', error);
        }
    }

    refreshHealthData() {
        const healthMonitor = document.getElementById('health-monitor');
        if (healthMonitor) {
            healthMonitor.innerHTML = `
                <div class="text-center">
                    <div class="spinner-border" role="status">
                        <span class="visually-hidden">Refreshing...</span>
                    </div>
                    <p>Refreshing configuration health data...</p>
                </div>
            `;
        }
        
        this.loadHealthData();
    }

    displayHealthData(healthData) {
        const healthMonitor = document.getElementById('health-monitor');
        if (!healthMonitor) return;

        if (!healthData || healthData.length === 0) {
            healthMonitor.innerHTML = `
                <div class="alert alert-info">
                    <i class="bi bi-info-circle"></i>
                    No configuration data available
                </div>
            `;
            return;
        }

        let html = '<div class="health-grid">';
        healthData.forEach(config => {
            const statusClass = this.getStatusClass(config.status);
            const statusIcon = this.getStatusIcon(config.status);
            const lastTestTime = config.last_tested ? 
                this.formatDateTime(config.last_tested) : 'Never tested';
            
            html += `
                <div class="health-item status-${statusClass}">
                    <div class="health-header">
                        <i class="bi bi-${statusIcon}"></i>
                        <span class="health-name">${this.escapeHtml(config.name)}</span>
                        <span class="health-protocol">${config.protocol.toUpperCase()}</span>
                    </div>
                    <div class="health-status">
                        <span class="status-badge status-${config.status}">${config.status}</span>
                    </div>
                    <div class="health-details">
                        <small class="health-message">${this.escapeHtml(config.message || 'No message')}</small>
                        <small class="health-time">Last tested: ${lastTestTime}</small>
                    </div>
                    <div class="health-actions">
                        <button class="btn btn-sm btn-outline-primary" onclick="testConfiguration(${config.id})">
                            <i class="bi bi-play-circle"></i> Test
                        </button>
                        <button class="btn btn-sm btn-outline-secondary" onclick="viewConfiguration(${config.id})">
                            <i class="bi bi-eye"></i> View
                        </button>
                    </div>
                </div>
            `;
        });
        html += '</div>';
        
        healthMonitor.innerHTML = html;
    }

    getStatusClass(status) {
        const statusMap = {
            'success': 'success',
            'failed': 'danger',
            'partial': 'warning',
            'timeout': 'danger',
            'error': 'danger',
            'untested': 'warning'
        };
        return statusMap[status] || 'warning';
    }

    getStatusIcon(status) {
        const iconMap = {
            'success': 'check-circle',
            'failed': 'x-circle',
            'partial': 'exclamation-circle',
            'timeout': 'clock',
            'error': 'exclamation-triangle',
            'untested': 'question-circle'
        };
        return iconMap[status] || 'question-circle';
    }

    formatDateTime(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);

        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`;
        if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
        if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
        
        return date.toLocaleDateString();
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    handleQuickAction(event, button) {
        const action = button.textContent.trim().toLowerCase();
        
        // Add loading state
        const originalText = button.innerHTML;
        button.innerHTML = '<i class="spinner-border spinner-border-sm"></i> Loading...';
        button.disabled = true;

        // Simulate action processing
        setTimeout(() => {
            button.innerHTML = originalText;
            button.disabled = false;
            
            // Show success message
            this.showSuccess(`${action} action completed successfully`);
        }, 1000);
    }

    refreshData(dataType) {
        switch (dataType) {
            case 'health':
                this.refreshHealthData();
                break;
            case 'statistics':
                this.loadStatistics();
                break;
            default:
                console.log(`Unknown data type: ${dataType}`);
        }
    }

    updateStatistics(data) {
        // Update statistics display if needed
        console.log('Statistics updated:', data);
    }

    showSuccess(message) {
        this.showNotification(message, 'success');
    }

    showError(title, message) {
        this.showNotification(`${title}: ${message}`, 'danger');
    }

    showWarning(message) {
        this.showNotification(message, 'warning');
    }

    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        // Add to page
        document.body.appendChild(notification);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
    }

    destroy() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }
    }
}

// Global functions for onclick handlers
function testConfiguration(configId) {
    if (confirm('Are you sure you want to test this configuration?')) {
        window.location.href = `/utilities/email-configuration/configurations/${configId}/test/`;
    }
}

function viewConfiguration(configId) {
    window.location.href = `/utilities/email-configuration/configurations/${configId}/`;
}

function refreshHealthData() {
    if (window.dashboard) {
        window.dashboard.refreshHealthData();
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.dashboard = new EmailConfigurationDashboard();
});

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
    if (window.dashboard) {
        window.dashboard.destroy();
    }
});

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = EmailConfigurationDashboard;
}
