/**
 * Log History Module JavaScript
 * Comprehensive functionality for log history management
 */

class LogHistoryManager {
    constructor() {
        this.charts = {};
        this.currentFilters = {};
        this.isLoading = false;
        this.init();
    }

    init() {
        this.bindEvents();
        this.initializeCharts();
        this.loadInitialData();
        this.setupAutoRefresh();
    }

    bindEvents() {
        // Date range selector
        const dateRangeSelect = document.getElementById('date-range');
        if (dateRangeSelect) {
            dateRangeSelect.addEventListener('change', (e) => {
                this.handleDateRangeChange(e.target.value);
            });
        }

        // Quick date presets
        const quickDateSelect = document.getElementById('quick-date');
        if (quickDateSelect) {
            quickDateSelect.addEventListener('change', (e) => {
                this.handleQuickDateChange(e.target.value);
            });
        }

        // Search form submission
        const searchForm = document.querySelector('.log-search-form');
        if (searchForm) {
            searchForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleSearch(e.target);
            });
        }

        // Bulk action form
        const bulkActionForm = document.querySelector('.bulk-action-form');
        if (bulkActionForm) {
            bulkActionForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleBulkAction(e.target);
            });
        }

        // Export form
        const exportForm = document.querySelector('.export-form');
        if (exportForm) {
            exportForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleExport(e.target);
            });
        }

        // Chart refresh buttons
        document.querySelectorAll('[data-action="refresh-chart"]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                this.refreshChart(btn.dataset.chart);
            });
        });

        // Save filter buttons
        document.querySelectorAll('[data-action="save-filter"]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                this.showSaveFilterModal();
            });
        });

        // Load filter buttons
        document.querySelectorAll('[data-action="load-filter"]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                this.loadFilter(btn.dataset.filterId);
            });
        });
    }

    initializeCharts() {
        // Initialize Chart.js charts if they exist
        this.initDailyActivityChart();
        this.initActionTypeChart();
        this.initSeverityChart();
        this.initUserActivityChart();
    }

    initDailyActivityChart() {
        const canvas = document.getElementById('dailyActivityChart');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        this.charts.dailyActivity = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Log Entries',
                    data: [],
                    borderColor: '#4e73df',
                    backgroundColor: 'rgba(78, 115, 223, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: '#4e73df',
                    pointBorderColor: '#ffffff',
                    pointBorderWidth: 2,
                    pointRadius: 4,
                    pointHoverRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: '#ffffff',
                        bodyColor: '#ffffff',
                        borderColor: '#4e73df',
                        borderWidth: 1
                    }
                },
                scales: {
                    x: {
                        grid: {
                            color: '#e3e6f0',
                            drawBorder: false
                        },
                        ticks: {
                            color: '#858796',
                            font: {
                                size: 11
                            }
                        }
                    },
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: '#e3e6f0',
                            drawBorder: false
                        },
                        ticks: {
                            color: '#858796',
                            font: {
                                size: 11
                            },
                            stepSize: 1
                        }
                    }
                },
                interaction: {
                    mode: 'nearest',
                    axis: 'x',
                    intersect: false
                }
            }
        });
    }

    initActionTypeChart() {
        const canvas = document.getElementById('actionTypeChart');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        this.charts.actionType = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: [],
                datasets: [{
                    data: [],
                    backgroundColor: [
                        '#4e73df', '#1cc88a', '#36b9cc', '#f6c23e', '#e74a3b',
                        '#858796', '#5a5c69', '#2e59d9', '#17a673', '#2c9faf'
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
                        display: false
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: '#ffffff',
                        bodyColor: '#ffffff',
                        borderColor: '#4e73df',
                        borderWidth: 1,
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
                },
                cutout: '60%'
            }
        });
    }

    initSeverityChart() {
        const canvas = document.getElementById('severityChart');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        this.charts.severity = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: [],
                datasets: [{
                    data: [],
                    backgroundColor: [
                        '#e74a3b', '#f6c23e', '#36b9cc', '#1cc88a'
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
                        display: false
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: '#ffffff',
                        bodyColor: '#ffffff',
                        borderColor: '#e74a3b',
                        borderWidth: 1
                    }
                },
                cutout: '60%'
            }
        });
    }

    initUserActivityChart() {
        const canvas = document.getElementById('userActivityChart');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        this.charts.userActivity = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: [],
                datasets: [{
                    label: 'Actions',
                    data: [],
                    backgroundColor: 'rgba(78, 115, 223, 0.8)',
                    borderColor: '#4e73df',
                    borderWidth: 1,
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: '#ffffff',
                        bodyColor: '#ffffff',
                        borderColor: '#4e73df',
                        borderWidth: 1
                    }
                },
                scales: {
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            color: '#858796',
                            font: {
                                size: 11
                            }
                        }
                    },
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: '#e3e6f0',
                            drawBorder: false
                        },
                        ticks: {
                            color: '#858796',
                            font: {
                                size: 11
                            },
                            stepSize: 1
                        }
                    }
                }
            }
        });
    }

    loadInitialData() {
        const days = document.getElementById('date-range')?.value || 30;
        this.loadChartData(days);
    }

    async loadChartData(days) {
        if (this.isLoading) return;

        this.isLoading = true;
        this.showLoadingState();

        try {
            const response = await fetch(`/log-history/ajax/chart-data/?days=${days}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            this.updateCharts(data);
            this.updateStatistics(data);
        } catch (error) {
            console.error('Error loading chart data:', error);
            this.showError('Failed to load chart data. Please try again.');
        } finally {
            this.isLoading = false;
            this.hideLoadingState();
        }
    }

    updateCharts(data) {
        // Update Daily Activity Chart
        if (this.charts.dailyActivity && data.daily_stats) {
            this.charts.dailyActivity.data.labels = data.daily_stats.map(item => item.date);
            this.charts.dailyActivity.data.datasets[0].data = data.daily_stats.map(item => item.count);
            this.charts.dailyActivity.update('none');
        }

        // Update Action Type Chart
        if (this.charts.actionType && data.action_stats) {
            this.charts.actionType.data.labels = data.action_stats.map(item => item.action_type);
            this.charts.actionType.data.datasets[0].data = data.action_stats.map(item => item.count);
            this.charts.actionType.update('none');
        }

        // Update Severity Chart
        if (this.charts.severity && data.severity_stats) {
            this.charts.severity.data.labels = data.severity_stats.map(item => item.severity);
            this.charts.severity.data.datasets[0].data = data.severity_stats.map(item => item.count);
            this.charts.severity.update('none');
        }

        // Update User Activity Chart
        if (this.charts.userActivity && data.user_stats) {
            this.charts.userActivity.data.labels = data.user_stats.map(item => item.user__username);
            this.charts.userActivity.data.datasets[0].data = data.user_stats.map(item => item.count);
            this.charts.userActivity.update('none');
        }
    }

    updateStatistics(data) {
        // Update statistics cards if they exist
        const totalLogsElement = document.getElementById('total-logs');
        if (totalLogsElement && data.total_logs !== undefined) {
            totalLogsElement.textContent = data.total_logs.toLocaleString();
        }

        const activeUsersElement = document.getElementById('active-users');
        if (activeUsersElement && data.user_stats) {
            activeUsersElement.textContent = data.user_stats.length;
        }

        const errorLogsElement = document.getElementById('error-logs');
        if (errorLogsElement && data.error_logs !== undefined) {
            errorLogsElement.textContent = data.error_logs;
        }

        const avgExecutionTimeElement = document.getElementById('avg-execution-time');
        if (avgExecutionTimeElement && data.avg_execution_time !== undefined) {
            avgExecutionTimeElement.textContent = `${data.avg_execution_time.toFixed(3)}s`;
        }
    }

    handleDateRangeChange(days) {
        this.loadChartData(days);
        this.updateURLParams({ days });
    }

    handleQuickDateChange(preset) {
        if (!preset) return;

        const today = new Date();
        let startDate, endDate;

        switch (preset) {
            case 'today':
                startDate = today;
                endDate = today;
                break;
            case 'yesterday':
                startDate = new Date(today.getTime() - 24 * 60 * 60 * 1000);
                endDate = startDate;
                break;
            case 'last_7_days':
                startDate = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000);
                endDate = today;
                break;
            case 'last_30_days':
                startDate = new Date(today.getTime() - 30 * 24 * 60 * 60 * 1000);
                endDate = today;
                break;
            case 'this_month':
                startDate = new Date(today.getFullYear(), today.getMonth(), 1);
                endDate = today;
                break;
            case 'last_month':
                startDate = new Date(today.getFullYear(), today.getMonth() - 1, 1);
                endDate = new Date(today.getFullYear(), today.getMonth(), 0);
                break;
            default:
                return;
        }

        // Update date inputs
        const dateFromInput = document.getElementById('date-from');
        const dateToInput = document.getElementById('id_date_to');

        if (dateFromInput) {
            dateFromInput.value = this.formatDate(startDate);
        }
        if (dateToInput) {
            dateToInput.value = this.formatDate(endDate);
        }

        // Trigger search
        this.performSearch();
    }

    async handleSearch(form) {
        const formData = new FormData(form);
        const searchParams = new URLSearchParams();

        for (let [key, value] of formData.entries()) {
            if (value) {
                searchParams.append(key, value);
            }
        }

        this.currentFilters = Object.fromEntries(searchParams);
        this.performSearch();
    }

    async performSearch() {
        if (this.isLoading) return;

        this.isLoading = true;
        this.showLoadingState();

        try {
            const queryString = new URLSearchParams(this.currentFilters).toString();
            const response = await fetch(`/log-history/search/?${queryString}`);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const html = await response.text();
            this.updateSearchResults(html);
        } catch (error) {
            console.error('Error performing search:', error);
            this.showError('Search failed. Please try again.');
        } finally {
            this.isLoading = false;
            this.hideLoadingState();
        }
    }

    updateSearchResults(html) {
        const resultsContainer = document.getElementById('search-results');
        if (resultsContainer) {
            resultsContainer.innerHTML = html;
        }
    }

    async handleBulkAction(form) {
        const formData = new FormData(form);
        const action = formData.get('action');
        const selectedLogs = formData.get('selected_logs');

        if (!action || !selectedLogs) {
            this.showError('Please select an action and logs.');
            return;
        }

        if (!confirm(`Are you sure you want to ${action} the selected logs?`)) {
            return;
        }

        try {
            const response = await fetch('/log-history/bulk-action/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': this.getCSRFToken()
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            if (result.success) {
                this.showSuccess(result.message);
                this.refreshData();
            } else {
                this.showError(result.message || 'Bulk action failed.');
            }
        } catch (error) {
            console.error('Error performing bulk action:', error);
            this.showError('Bulk action failed. Please try again.');
        }
    }

    async handleExport(form) {
        const formData = new FormData(form);
        
        // Add current search filters to export
        Object.entries(this.currentFilters).forEach(([key, value]) => {
            formData.append(key, value);
        });

        try {
            const response = await fetch('/log-history/export/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': this.getCSRFToken()
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            // Handle file download
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `log_history_${new Date().toISOString().split('T')[0]}.csv`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);

            this.showSuccess('Export completed successfully.');
        } catch (error) {
            console.error('Error exporting data:', error);
            this.showError('Export failed. Please try again.');
        }
    }

    refreshChart(chartName) {
        if (this.charts[chartName]) {
            this.charts[chartName].update();
        }
    }

    refreshData() {
        const days = document.getElementById('date-range')?.value || 30;
        this.loadChartData(days);
        
        // Refresh search results if on search page
        if (window.location.pathname.includes('/search/')) {
            this.performSearch();
        }
    }

    setupAutoRefresh() {
        // Auto-refresh every 5 minutes
        setInterval(() => {
            this.refreshData();
        }, 5 * 60 * 1000);
    }

    showSaveFilterModal() {
        // Implementation for save filter modal
        const modal = document.getElementById('saveFilterModal');
        if (modal) {
            const modalInstance = new bootstrap.Modal(modal);
            modalInstance.show();
        }
    }

    async loadFilter(filterId) {
        try {
            const response = await fetch(`/log-history/filters/${filterId}/`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const filter = await response.json();
            this.applyFilter(filter.filter_criteria);
        } catch (error) {
            console.error('Error loading filter:', error);
            this.showError('Failed to load filter.');
        }
    }

    applyFilter(criteria) {
        // Apply filter criteria to form fields
        Object.entries(criteria).forEach(([key, value]) => {
            const field = document.querySelector(`[name="${key}"]`);
            if (field) {
                field.value = value;
            }
        });

        // Trigger search
        this.performSearch();
    }

    updateURLParams(params) {
        const url = new URL(window.location);
        Object.entries(params).forEach(([key, value]) => {
            if (value) {
                url.searchParams.set(key, value);
            } else {
                url.searchParams.delete(key);
            }
        });
        window.history.replaceState({}, '', url);
    }

    formatDate(date) {
        return date.toISOString().split('T')[0];
    }

    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
    }

    showLoadingState() {
        document.body.classList.add('loading');
        document.querySelectorAll('.loading-indicator').forEach(el => {
            el.style.display = 'block';
        });
    }

    hideLoadingState() {
        document.body.classList.remove('loading');
        document.querySelectorAll('.loading-indicator').forEach(el => {
            el.style.display = 'none';
        });
    }

    showSuccess(message) {
        this.showNotification(message, 'success');
    }

    showError(message) {
        this.showNotification(message, 'error');
    }

    showWarning(message) {
        this.showNotification(message, 'warning');
    }

    showInfo(message) {
        this.showNotification(message, 'info');
    }

    showNotification(message, type = 'info') {
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
}

// Utility functions
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Initialize LogHistoryManager
    window.logHistoryManager = new LogHistoryManager();

    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Add smooth scrolling to anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Add loading states to buttons
    document.querySelectorAll('button[type="submit"]').forEach(button => {
        button.addEventListener('click', function() {
            if (!this.disabled) {
                this.disabled = true;
                const originalText = this.innerHTML;
                this.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Loading...';
                
                // Re-enable after form submission (you might need to adjust this)
                setTimeout(() => {
                    this.disabled = false;
                    this.innerHTML = originalText;
                }, 5000);
            }
        });
    });
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = LogHistoryManager;
}
