/**
 * Cron Job Viewer JavaScript
 * Handles dashboard functionality, API calls, charts, and user interactions
 */

class CronJobViewer {
    constructor() {
        this.charts = {};
        this.refreshInterval = null;
        this.isRefreshing = false;
        
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.initializeCharts();
        this.loadStatistics();
        this.startAutoRefresh();
    }
    
    bindEvents() {
        // Refresh button
        const refreshBtn = document.getElementById('refreshBtn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.refreshData());
        }
        
        // Close modal buttons
        const closeLogsModal = document.getElementById('closeLogsModal');
        if (closeLogsModal) {
            closeLogsModal.addEventListener('click', () => this.closeLogsModal());
        }
        
        // Modal overlay click
        const logsModal = document.getElementById('logsModal');
        if (logsModal) {
            logsModal.addEventListener('click', (e) => {
                if (e.target === logsModal) {
                    this.closeLogsModal();
                }
            });
        }
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeLogsModal();
            }
            if (e.key === 'r' && (e.ctrlKey || e.metaKey)) {
                e.preventDefault();
                this.refreshData();
            }
        });
    }
    
    initializeCharts() {
        // Status Chart
        const statusCtx = document.getElementById('statusChart');
        if (statusCtx) {
            this.charts.status = new Chart(statusCtx, {
                type: 'doughnut',
                data: {
                    labels: ['Success', 'Failed', 'Pending', 'Running'],
                    datasets: [{
                        data: [0, 0, 0, 0],
                        backgroundColor: [
                            '#10b981', // Green
                            '#ef4444', // Red
                            '#6b7280', // Gray
                            '#3b82f6'  // Blue
                        ],
                        borderWidth: 2,
                        borderColor: '#ffffff'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: {
                                padding: 20,
                                usePointStyle: true
                            }
                        },
                        title: {
                            display: true,
                            text: 'Jobs by Status',
                            font: {
                                size: 14,
                                weight: 'bold'
                            }
                        }
                    }
                }
            });
        }
        
        // Schedule Type Chart
        const scheduleCtx = document.getElementById('scheduleChart');
        if (scheduleCtx) {
            this.charts.schedule = new Chart(scheduleCtx, {
                type: 'pie',
                data: {
                    labels: ['Cron Expression', 'Interval'],
                    datasets: [{
                        data: [0, 0],
                        backgroundColor: [
                            '#3b82f6', // Blue
                            '#10b981'  // Green
                        ],
                        borderWidth: 2,
                        borderColor: '#ffffff'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: {
                                padding: 20,
                                usePointStyle: true
                            }
                        },
                        title: {
                            display: true,
                            text: 'Jobs by Schedule Type',
                            font: {
                                size: 14,
                                weight: 'bold'
                            }
                        }
                    }
                }
            });
        }
    }
    
    async loadStatistics() {
        try {
            const response = await fetch('/utilities/cron-job-viewer/ajax/statistics/');
            const data = await response.json();
            
            if (data.success) {
                this.updateStatistics(data.data);
                this.updateCharts(data.data);
            } else {
                console.error('Failed to load statistics:', data.error);
            }
        } catch (error) {
            console.error('Error loading statistics:', error);
        }
    }
    
    updateStatistics(data) {
        // Update dashboard statistics
        const totalJobsEl = document.getElementById('totalJobs');
        const activeJobsEl = document.getElementById('activeJobs');
        const runningJobsEl = document.getElementById('runningJobs');
        const failedJobsEl = document.getElementById('failedJobs');
        
        if (totalJobsEl) totalJobsEl.textContent = data.status_counts.reduce((sum, item) => sum + item.count, 0);
        if (activeJobsEl) activeJobsEl.textContent = data.schedule_counts.cron + data.schedule_counts.interval;
        if (runningJobsEl) runningJobsEl.textContent = data.status_counts.find(item => item.last_status === 'running')?.count || 0;
        if (failedJobsEl) failedJobsEl.textContent = data.status_counts.find(item => item.last_status === 'failed')?.count || 0;
    }
    
    updateCharts(data) {
        // Update status chart
        if (this.charts.status) {
            const statusData = [0, 0, 0, 0];
            data.status_counts.forEach(item => {
                switch (item.last_status) {
                    case 'success':
                        statusData[0] = item.count;
                        break;
                    case 'failed':
                        statusData[1] = item.count;
                        break;
                    case 'pending':
                        statusData[2] = item.count;
                        break;
                    case 'running':
                        statusData[3] = item.count;
                        break;
                }
            });
            
            this.charts.status.data.datasets[0].data = statusData;
            this.charts.status.update();
        }
        
        // Update schedule chart
        if (this.charts.schedule) {
            this.charts.schedule.data.datasets[0].data = [
                data.schedule_counts.cron,
                data.schedule_counts.interval
            ];
            this.charts.schedule.update();
        }
    }
    
    async refreshData() {
        if (this.isRefreshing) return;
        
        this.isRefreshing = true;
        const refreshBtn = document.getElementById('refreshBtn');
        
        if (refreshBtn) {
            refreshBtn.disabled = true;
            refreshBtn.innerHTML = `
                <svg class="w-4 h-4 mr-2 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
                </svg>
                Refreshing...
            `;
        }
        
        try {
            await this.loadStatistics();
            this.showMessage('Data refreshed successfully', 'success');
            
            // Reload page if on dashboard
            if (window.location.pathname.endsWith('/cron-job-viewer/')) {
                setTimeout(() => location.reload(), 1000);
            }
        } catch (error) {
            this.showMessage('Failed to refresh data', 'error');
        } finally {
            this.isRefreshing = false;
            
            if (refreshBtn) {
                refreshBtn.disabled = false;
                refreshBtn.innerHTML = `
                    <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
                    </svg>
                    Refresh
                `;
            }
        }
    }
    
    startAutoRefresh() {
        // Auto-refresh every 30 seconds
        this.refreshInterval = setInterval(() => {
            this.loadStatistics();
        }, 30000);
    }
    
    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }
    
    showLogsModal(jobId) {
        this.loadJobLogs(jobId);
        const modal = document.getElementById('logsModal');
        if (modal) {
            modal.classList.remove('hidden');
            document.body.style.overflow = 'hidden';
        }
    }
    
    closeLogsModal() {
        const modal = document.getElementById('logsModal');
        if (modal) {
            modal.classList.add('hidden');
            document.body.style.overflow = '';
        }
    }
    
    async loadJobLogs(jobId) {
        try {
            const response = await fetch(`/utilities/cron-job-viewer/${jobId}/ajax/logs/`);
            const data = await response.json();
            
            if (data.success) {
                this.displayJobLogs(data.logs);
            } else {
                this.displayJobLogs([]);
                this.showMessage('Failed to load logs', 'error');
            }
        } catch (error) {
            console.error('Error loading job logs:', error);
            this.showMessage('Error loading logs', 'error');
        }
    }
    
    displayJobLogs(logs) {
        const logsContent = document.getElementById('logsContent');
        if (!logsContent) return;
        
        if (logs.length === 0) {
            logsContent.innerHTML = `
                <div class="text-center py-8">
                    <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"></path>
                    </svg>
                    <h3 class="mt-2 text-sm font-medium text-gray-900">No logs found</h3>
                    <p class="mt-1 text-sm text-gray-500">This job hasn't been executed yet.</p>
                </div>
            `;
            return;
        }
        
        const logsHTML = logs.map(log => `
            <div class="border-b border-gray-200 py-4 last:border-b-0">
                <div class="flex items-start justify-between">
                    <div class="flex-1">
                        <div class="flex items-center space-x-2 mb-2">
                            <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${log.status_badge_class}">
                                ${log.status_display}
                            </span>
                            <span class="text-sm text-gray-500">${log.duration_formatted}</span>
                        </div>
                        <div class="text-sm text-gray-900 mb-1">
                            <strong>Started:</strong> ${new Date(log.run_started_at).toLocaleString()}
                        </div>
                        ${log.run_ended_at ? `
                            <div class="text-sm text-gray-900 mb-1">
                                <strong>Ended:</strong> ${new Date(log.run_ended_at).toLocaleString()}
                            </div>
                        ` : ''}
                        ${log.worker_name ? `
                            <div class="text-sm text-gray-900 mb-2">
                                <strong>Worker:</strong> ${log.worker_name}
                            </div>
                        ` : ''}
                        ${log.output_message ? `
                            <div class="mt-2">
                                <details class="text-sm">
                                    <summary class="cursor-pointer text-gray-700 hover:text-gray-900">
                                        <strong>Output:</strong> Click to expand
                                    </summary>
                                    <pre class="mt-2 p-2 bg-gray-50 rounded text-xs text-gray-800 whitespace-pre-wrap">${log.output_message}</pre>
                                </details>
                            </div>
                        ` : ''}
                    </div>
                </div>
            </div>
        `).join('');
        
        logsContent.innerHTML = logsHTML;
    }
    
    showMessage(message, type = 'info') {
        // Create message element
        const messageEl = document.createElement('div');
        messageEl.className = `message ${type}`;
        
        const iconMap = {
            success: '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>',
            error: '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>',
            warning: '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"></path>',
            info: '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>'
        };
        
        messageEl.innerHTML = `
            <svg class="message-icon text-${type === 'success' ? 'green' : type === 'error' ? 'red' : type === 'warning' ? 'yellow' : 'blue'}-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                ${iconMap[type] || iconMap.info}
            </svg>
            <p class="message-text">${message}</p>
            <button class="message-close" onclick="this.parentElement.remove()">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                </svg>
            </button>
        `;
        
        // Add to message container
        let container = document.querySelector('.message-container');
        if (!container) {
            container = document.createElement('div');
            container.className = 'message-container';
            document.body.appendChild(container);
        }
        
        container.appendChild(messageEl);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (messageEl.parentElement) {
                messageEl.remove();
            }
        }, 5000);
    }
    
    // Utility methods
    formatDuration(seconds) {
        if (!seconds) return 'N/A';
        
        if (seconds < 60) {
            return `${seconds.toFixed(1)}s`;
        } else if (seconds < 3600) {
            const minutes = Math.floor(seconds / 60);
            const secs = Math.floor(seconds % 60);
            return `${minutes}m ${secs}s`;
        } else {
            const hours = Math.floor(seconds / 3600);
            const minutes = Math.floor((seconds % 3600) / 60);
            return `${hours}h ${minutes}m`;
        }
    }
    
    formatDateTime(dateString) {
        if (!dateString) return 'Never';
        
        const date = new Date(dateString);
        return date.toLocaleString();
    }
    
    getStatusBadgeClass(status) {
        const statusClasses = {
            'success': 'bg-green-100 text-green-800',
            'failed': 'bg-red-100 text-red-800',
            'pending': 'bg-gray-100 text-gray-800',
            'running': 'bg-blue-100 text-blue-800'
        };
        return statusClasses[status] || statusClasses.pending;
    }
    
    // API helper methods
    async apiCall(url, options = {}) {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCSRFToken()
            }
        };
        
        const finalOptions = { ...defaultOptions, ...options };
        
        try {
            const response = await fetch(url, finalOptions);
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || `HTTP ${response.status}`);
            }
            
            return data;
        } catch (error) {
            console.error('API call failed:', error);
            throw error;
        }
    }
    
    getCSRFToken() {
        const token = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
        if (token) return token;
        
        // Fallback to cookie
        const name = 'csrftoken';
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
    
    // Cleanup method
    destroy() {
        this.stopAutoRefresh();
        
        // Destroy charts
        Object.values(this.charts).forEach(chart => {
            if (chart && typeof chart.destroy === 'function') {
                chart.destroy();
            }
        });
        
        this.charts = {};
    }
}

// Job management functions (global scope for inline onclick handlers)
function runJobNow(jobId) {
    if (confirm('Are you sure you want to run this job now?')) {
        fetch(`/utilities/cron-job-viewer/${jobId}/ajax/run-now/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/json',
            },
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showMessage(data.message, 'success');
                setTimeout(() => location.reload(), 1500);
            } else {
                showMessage(data.error || 'Failed to run job', 'error');
            }
        })
        .catch(error => {
            showMessage('Error running job: ' + error.message, 'error');
        });
    }
}

function toggleJobStatus(jobId, newStatus) {
    const action = newStatus ? 'activate' : 'deactivate';
    if (confirm(`Are you sure you want to ${action} this job?`)) {
        fetch(`/utilities/cron-job-viewer/${jobId}/ajax/update-status/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ is_active: newStatus }),
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showMessage(data.message, 'success');
                setTimeout(() => location.reload(), 1500);
            } else {
                showMessage(data.errors || 'Failed to update status', 'error');
            }
        })
        .catch(error => {
            showMessage('Error updating status: ' + error.message, 'error');
        });
    }
}

function showLogs(jobId) {
    if (window.cronJobViewer) {
        window.cronJobViewer.showLogsModal(jobId);
    }
}

// Utility functions (global scope)
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

function showMessage(message, type) {
    if (window.cronJobViewer) {
        window.cronJobViewer.showMessage(message, type);
    } else {
        // Fallback if CronJobViewer is not initialized
        alert(message);
    }
}

function hideMessage() {
    const container = document.getElementById('messageContainer');
    if (container) {
        container.classList.add('hidden');
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.cronJobViewer = new CronJobViewer();
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (window.cronJobViewer) {
        window.cronJobViewer.destroy();
    }
});
