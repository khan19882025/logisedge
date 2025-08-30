/**
 * Auto Task Scheduler Dashboard JavaScript
 * Handles all dashboard functionality, API calls, and UI interactions
 */

class TaskSchedulerDashboard {
    constructor() {
        this.initializeElements();
        this.bindEvents();
        this.chart = null;
        this.refreshInterval = null;
    }

    initializeElements() {
        // Dashboard elements
        this.statsElements = {
            totalTasks: document.getElementById('total-tasks'),
            activeTasks: document.getElementById('active-tasks'),
            pausedTasks: document.getElementById('paused-tasks'),
            failedTasks: document.getElementById('failed-tasks')
        };

        this.statusElements = {
            systemStatus: document.getElementById('system-status'),
            dbStatus: document.getElementById('db-status'),
            celeryStatus: document.getElementById('celery-status'),
            redisStatus: document.getElementById('redis-status'),
            lastCheck: document.getElementById('last-check')
        };

        this.lists = {
            upcomingTasks: document.getElementById('upcoming-tasks-list'),
            recentExecutions: document.getElementById('recent-executions-list')
        };

        // Modal elements
        this.createTaskModal = document.getElementById('create-task-modal');
        this.createTaskForm = document.getElementById('create-task-form');

        // Loading overlay
        this.loadingOverlay = document.getElementById('loading-overlay');
    }

    bindEvents() {
        // Form submission
        if (this.createTaskForm) {
            this.createTaskForm.addEventListener('submit', (e) => this.handleCreateTask(e));
        }

        // Modal close events
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal')) {
                this.closeModal(e.target.id);
            }
        });
    }

    async initializeDashboard() {
        try {
            this.showLoading(true);
            
            // Load all dashboard data
            await Promise.all([
                this.loadStatistics(),
                this.loadUpcomingTasks(),
                this.loadRecentExecutions(),
                this.loadSystemStatus(),
                this.initializeChart()
            ]);

            // Set up auto-refresh
            this.setupAutoRefresh();
            
        } catch (error) {
            console.error('Failed to initialize dashboard:', error);
            this.showError('Failed to load dashboard data');
        } finally {
            this.showLoading(false);
        }
    }

    async loadStatistics() {
        try {
            const response = await this.apiCall('/api/scheduled-tasks/statistics/');
            if (response.ok) {
                const stats = await response.json();
                this.updateStatistics(stats);
            }
        } catch (error) {
            console.error('Failed to load statistics:', error);
        }
    }

    updateStatistics(stats) {
        // Update stat cards
        if (this.statsElements.totalTasks) {
            this.statsElements.totalTasks.textContent = stats.total_tasks;
        }
        if (this.statsElements.activeTasks) {
            this.statsElements.activeTasks.textContent = stats.active_tasks;
        }
        if (this.statsElements.pausedTasks) {
            this.statsElements.pausedTasks.textContent = stats.paused_tasks;
        }
        if (this.statsElements.failedTasks) {
            this.statsElements.failedTasks.textContent = stats.failed_executions;
        }

        // Update chart if available
        if (this.chart && stats.tasks_by_type) {
            this.updateChart(stats.tasks_by_type);
        }
    }

    async loadUpcomingTasks() {
        try {
            const response = await this.apiCall('/api/scheduled-tasks/');
            if (response.ok) {
                const tasks = await response.json();
                const upcomingTasks = tasks.results
                    .filter(task => task.status === 'active' && task.next_run_at)
                    .sort((a, b) => new Date(a.next_run_at) - new Date(b.next_run_at))
                    .slice(0, 5);

                this.renderUpcomingTasks(upcomingTasks);
            }
        } catch (error) {
            console.error('Failed to load upcoming tasks:', error);
        }
    }

    renderUpcomingTasks(tasks) {
        if (!this.lists.upcomingTasks) return;

        if (tasks.length === 0) {
            this.lists.upcomingTasks.innerHTML = `
                <div class="empty-state">
                    <p>No upcoming tasks scheduled</p>
                </div>
            `;
            return;
        }

        const tasksHtml = tasks.map(task => `
            <div class="task-item">
                <div class="task-info">
                    <h4>${this.escapeHtml(task.name)}</h4>
                    <p>${task.schedule_summary} • Next run: ${this.formatDateTime(task.next_run_at)}</p>
                </div>
                <span class="task-status ${task.status}">${task.status}</span>
            </div>
        `).join('');

        this.lists.upcomingTasks.innerHTML = tasksHtml;
    }

    async loadRecentExecutions() {
        try {
            const response = await this.apiCall('/api/task-logs/recent/');
            if (response.ok) {
                const logs = await response.json();
                this.renderRecentExecutions(logs.logs);
            }
        } catch (error) {
            console.error('Failed to load recent executions:', error);
        }
    }

    renderRecentExecutions(logs) {
        if (!this.lists.recentExecutions) return;

        if (logs.length === 0) {
            this.lists.recentExecutions.innerHTML = `
                <div class="empty-state">
                    <p>No recent executions</p>
                </div>
            `;
            return;
        }

        const executionsHtml = logs.map(log => `
            <div class="execution-item">
                <div class="execution-info">
                    <h4>${this.escapeHtml(log.task?.name || 'Unknown Task')}</h4>
                    <p>${this.formatDateTime(log.started_at)} • Duration: ${log.duration_formatted}</p>
                </div>
                <span class="execution-status ${log.status}">${log.status}</span>
            </div>
        `).join('');

        this.lists.recentExecutions.innerHTML = executionsHtml;
    }

    async loadSystemStatus() {
        try {
            const response = await this.apiCall('/api/health-check/');
            if (response.ok) {
                const health = await response.json();
                this.updateSystemStatus(health);
            }
        } catch (error) {
            console.error('Failed to load system status:', error);
            this.updateSystemStatus({ status: 'error' });
        }
    }

    updateSystemStatus(health) {
        // Update system status indicator
        if (this.statusElements.systemStatus) {
            this.statusElements.systemStatus.textContent = health.status;
            this.statusElements.systemStatus.className = `status-indicator ${health.status}`;
        }

        // Update individual status elements
        if (this.statusElements.dbStatus) {
            this.statusElements.dbStatus.textContent = 'Connected';
            this.statusElements.dbStatus.className = 'status-value healthy';
        }

        if (this.statusElements.celeryStatus) {
            const status = health.celery || 'unknown';
            this.statusElements.celeryStatus.textContent = status;
            this.statusElements.celeryStatus.className = `status-value ${this.getStatusClass(status)}`;
        }

        if (this.statusElements.redisStatus) {
            this.statusElements.redisStatus.textContent = 'Connected';
            this.statusElements.redisStatus.className = 'status-value healthy';
        }

        if (this.statusElements.lastCheck) {
            this.statusElements.lastCheck.textContent = this.formatDateTime(health.timestamp);
        }
    }

    getStatusClass(status) {
        switch (status) {
            case 'healthy': return 'healthy';
            case 'no_workers': return 'warning';
            case 'unavailable':
            case 'error': return 'error';
            default: return 'warning';
        }
    }

    async initializeChart() {
        try {
            const canvas = document.getElementById('task-distribution-chart');
            if (!canvas) return;

            const ctx = canvas.getContext('2d');
            
            // Get initial data
            const response = await this.apiCall('/api/scheduled-tasks/statistics/');
            if (response.ok) {
                const stats = await response.json();
                this.createChart(ctx, stats.tasks_by_type || {});
            }
        } catch (error) {
            console.error('Failed to initialize chart:', error);
        }
    }

    createChart(ctx, data) {
        const labels = Object.keys(data);
        const values = Object.values(data);
        const colors = [
            '#667eea', '#764ba2', '#f093fb', '#f5576c',
            '#4facfe', '#00f2fe', '#43e97b', '#38f9d7'
        ];

        this.chart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels.map(label => this.formatTaskType(label)),
                datasets: [{
                    data: values,
                    backgroundColor: colors.slice(0, labels.length),
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
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.parsed;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((value / total) * 100).toFixed(1);
                                return `${label}: ${value} (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });
    }

    updateChart(data) {
        if (!this.chart) return;

        this.chart.data.labels = Object.keys(data).map(label => this.formatTaskType(label));
        this.chart.data.datasets[0].data = Object.values(data);
        this.chart.update();
    }

    formatTaskType(type) {
        const typeMap = {
            'backup': 'Database Backup',
            'report': 'Report Generation',
            'email': 'Email Notification',
            'sync': 'Data Sync',
            'custom': 'Custom Task'
        };
        return typeMap[type] || type;
    }

    async handleCreateTask(event) {
        event.preventDefault();
        
        try {
            this.showLoading(true);
            
            const formData = new FormData(event.target);
            const taskData = this.serializeFormData(formData);
            
            // Validate required fields
            if (!taskData.name || !taskData.task_type || !taskData.schedule_type || !taskData.schedule_time) {
                throw new Error('Please fill in all required fields');
            }

            // Validate task parameters JSON
            if (taskData.task_parameters) {
                try {
                    JSON.parse(taskData.task_parameters);
                } catch (e) {
                    throw new Error('Task parameters must be valid JSON');
                }
            }

            const response = await this.apiCall('/api/scheduled-tasks/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(taskData)
            });

            if (response.ok) {
                this.showSuccess('Task created successfully!');
                this.closeModal('create-task-modal');
                this.refreshDashboard();
            } else {
                const error = await response.json();
                throw new Error(error.error || 'Failed to create task');
            }

        } catch (error) {
            console.error('Failed to create task:', error);
            this.showError(error.message);
        } finally {
            this.showLoading(false);
        }
    }

    serializeFormData(formData) {
        const data = {};
        for (let [key, value] of formData.entries()) {
            if (value === '') continue;
            
            // Handle boolean fields
            if (['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'].includes(key)) {
                data[key] = value === 'on';
            } else {
                data[key] = value;
            }
        }
        return data;
    }

    async syncSchedules() {
        try {
            this.showLoading(true);
            
            const response = await this.apiCall('/api/scheduled-tasks/sync_schedules/', {
                method: 'POST'
            });

            if (response.ok) {
                const result = await response.json();
                this.showSuccess('Schedule synchronization started successfully');
            } else {
                const error = await response.json();
                throw new Error(error.error || 'Failed to sync schedules');
            }

        } catch (error) {
            console.error('Failed to sync schedules:', error);
            this.showError(error.message);
        } finally {
            this.showLoading(false);
        }
    }

    async runHealthCheck() {
        try {
            this.showLoading(true);
            await this.loadSystemStatus();
            this.showSuccess('Health check completed');
        } catch (error) {
            console.error('Health check failed:', error);
            this.showError('Health check failed');
        } finally {
            this.showLoading(false);
        }
    }

    viewStatistics() {
        // Navigate to statistics page or show detailed stats modal
        window.location.href = '/auto-task-scheduler/statistics/';
    }

    viewAllTasks() {
        window.location.href = '/auto-task-scheduler/list/';
    }

    viewAllLogs() {
        window.location.href = '/auto-task-scheduler/logs/';
    }

    setupAutoRefresh() {
        // Refresh dashboard every 30 seconds
        this.refreshInterval = setInterval(() => {
            this.refreshDashboard();
        }, 30000);
    }

    async refreshDashboard() {
        try {
            await Promise.all([
                this.loadStatistics(),
                this.loadUpcomingTasks(),
                this.loadRecentExecutions()
            ]);
        } catch (error) {
            console.error('Failed to refresh dashboard:', error);
        }
    }

    // Modal functions
    openCreateTaskModal() {
        if (this.createTaskModal) {
            this.createTaskModal.style.display = 'flex';
        }
    }

    closeModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.style.display = 'none';
        }
    }

    // Utility functions
    async apiCall(endpoint, options = {}) {
        const defaultOptions = {
            method: 'GET',
            headers: {
                'X-CSRFToken': this.getCSRFToken(),
                'Content-Type': 'application/json',
            },
            ...options
        };

        return fetch(endpoint, defaultOptions);
    }

    getCSRFToken() {
        const metaTag = document.querySelector('meta[name="csrf-token"]');
        return metaTag ? metaTag.getAttribute('content') : '';
    }

    showLoading(show) {
        if (this.loadingOverlay) {
            this.loadingOverlay.style.display = show ? 'flex' : 'none';
        }
    }

    showSuccess(message) {
        // You can implement a toast notification system here
        alert(message); // Placeholder
    }

    showError(message) {
        // You can implement a toast notification system here
        alert('Error: ' + message); // Placeholder
    }

    formatDateTime(dateString) {
        if (!dateString) return 'N/A';
        
        const date = new Date(dateString);
        return date.toLocaleString();
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Global functions for HTML onclick handlers
function openCreateTaskModal() {
    if (window.taskScheduler) {
        window.taskScheduler.openCreateTaskModal();
    }
}

function closeCreateTaskModal() {
    if (window.taskScheduler) {
        window.taskScheduler.closeModal('create-task-modal');
    }
}

function refreshDashboard() {
    if (window.taskScheduler) {
        window.taskScheduler.refreshDashboard();
    }
}

function syncSchedules() {
    if (window.taskScheduler) {
        window.taskScheduler.syncSchedules();
    }
}

function runHealthCheck() {
    if (window.taskScheduler) {
        window.taskScheduler.runHealthCheck();
    }
}

function viewStatistics() {
    if (window.taskScheduler) {
        window.taskScheduler.viewStatistics();
    }
}

function viewAllTasks() {
    if (window.taskScheduler) {
        window.taskScheduler.viewAllTasks();
    }
}

function viewAllLogs() {
    if (window.taskScheduler) {
        window.taskScheduler.viewAllLogs();
    }
}

// Initialize dashboard when DOM is loaded
function initializeDashboard() {
    window.taskScheduler = new TaskSchedulerDashboard();
    window.taskScheduler.initializeDashboard();
}
