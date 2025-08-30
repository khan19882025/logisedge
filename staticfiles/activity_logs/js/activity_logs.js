/**
 * Activity Logs - Main JavaScript File
 * Handles interactive features, AJAX requests, and UI enhancements
 */

class ActivityLogsManager {
    constructor() {
        this.init();
    }

    init() {
        this.bindEvents();
        this.initializeCharts();
        this.initializeFilters();
        this.initializeExport();
        this.initializeRealTimeUpdates();
    }

    /**
     * Bind event listeners to DOM elements
     */
    bindEvents() {
        // Search and filter form submission
        const searchForm = document.querySelector('.search-filters form');
        if (searchForm) {
            searchForm.addEventListener('submit', this.handleSearch.bind(this));
        }

        // Clear filters button
        const clearBtn = document.querySelector('.btn-secondary');
        if (clearBtn) {
            clearBtn.addEventListener('click', this.clearFilters.bind(this));
        }

        // Export buttons
        const exportBtns = document.querySelectorAll('.export-btn');
        exportBtns.forEach(btn => {
            btn.addEventListener('click', this.handleExport.bind(this));
        });

        // Table row selection
        const tableRows = document.querySelectorAll('.table tbody tr');
        tableRows.forEach(row => {
            row.addEventListener('click', this.handleRowClick.bind(this));
        });

        // Pagination links
        const paginationLinks = document.querySelectorAll('.page-link');
        paginationLinks.forEach(link => {
            link.addEventListener('click', this.handlePagination.bind(this));
        });

        // Real-time refresh toggle
        const refreshToggle = document.getElementById('real-time-toggle');
        if (refreshToggle) {
            refreshToggle.addEventListener('change', this.toggleRealTimeRefresh.bind(this));
        }
    }

    /**
     * Initialize Chart.js charts
     */
    initializeCharts() {
        // Activity Chart
        const activityCtx = document.getElementById('activityChart');
        if (activityCtx) {
            this.activityChart = new Chart(activityCtx.getContext('2d'), {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Activity Logs',
                        data: [],
                        borderColor: '#667eea',
                        backgroundColor: 'rgba(102, 126, 234, 0.1)',
                        tension: 0.4,
                        fill: true
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
                            titleColor: '#fff',
                            bodyColor: '#fff',
                            borderColor: '#667eea',
                            borderWidth: 1
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                stepSize: 1,
                                color: '#6c757d'
                            },
                            grid: {
                                color: '#e9ecef'
                            }
                        },
                        x: {
                            ticks: {
                                color: '#6c757d'
                            },
                            grid: {
                                color: '#e9ecef'
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

        // Security Chart
        const securityCtx = document.getElementById('securityChart');
        if (securityCtx) {
            this.securityChart = new Chart(securityCtx.getContext('2d'), {
                type: 'doughnut',
                data: {
                    labels: [],
                    datasets: [{
                        data: [],
                        backgroundColor: [
                            '#dc3545',
                            '#ffc107',
                            '#28a745',
                            '#17a2b8',
                            '#6c757d'
                        ],
                        borderWidth: 2,
                        borderColor: '#fff'
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
                                usePointStyle: true,
                                font: {
                                    size: 12
                                }
                            }
                        },
                        tooltip: {
                            backgroundColor: 'rgba(0, 0, 0, 0.8)',
                            titleColor: '#fff',
                            bodyColor: '#fff',
                            borderColor: '#667eea',
                            borderWidth: 1
                        }
                    }
                }
            });
        }
    }

    /**
     * Initialize search and filter functionality
     */
    initializeFilters() {
        // Auto-submit on filter change
        const filterInputs = document.querySelectorAll('.search-filters select, .search-filters input[type="date"]');
        filterInputs.forEach(input => {
            input.addEventListener('change', () => {
                if (input.type === 'date') {
                    this.handleDateFilterChange(input);
                }
            });
        });

        // Search input with debouncing
        const searchInput = document.querySelector('.search-filters input[name="search"]');
        if (searchInput) {
            let searchTimeout;
            searchInput.addEventListener('input', (e) => {
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(() => {
                    this.performSearch(e.target.value);
                }, 500);
            });
        }
    }

    /**
     * Initialize export functionality
     */
    initializeExport() {
        // Add loading states to export buttons
        const exportBtns = document.querySelectorAll('.export-btn');
        exportBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.showLoadingState(btn);
            });
        });
    }

    /**
     * Initialize real-time updates
     */
    initializeRealTimeUpdates() {
        // Check if real-time updates are enabled
        if (localStorage.getItem('activity_logs_real_time') === 'true') {
            this.startRealTimeUpdates();
        }
    }

    /**
     * Handle search form submission
     */
    handleSearch(e) {
        e.preventDefault();
        const formData = new FormData(e.target);
        const searchParams = new URLSearchParams();
        
        for (let [key, value] of formData.entries()) {
            if (value) {
                searchParams.append(key, value);
            }
        }

        // Update URL without page reload
        const newUrl = `${window.location.pathname}?${searchParams.toString()}`;
        window.history.pushState({}, '', newUrl);
        
        // Perform AJAX search
        this.performAJAXSearch(searchParams);
    }

    /**
     * Perform AJAX search
     */
    async performAJAXSearch(searchParams) {
        try {
            const response = await fetch(`${window.location.pathname}?${searchParams.toString()}&ajax=1`, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.updateTableContent(data);
                this.updatePagination(data.pagination);
            }
        } catch (error) {
            console.error('Search error:', error);
            this.showNotification('Search failed. Please try again.', 'error');
        }
    }

    /**
     * Update table content with new data
     */
    updateTableContent(data) {
        const tbody = document.querySelector('.table tbody');
        if (!tbody || !data.results) return;

        tbody.innerHTML = '';
        
        if (data.results.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="7" class="text-center py-5">
                        <div class="text-muted">
                            <i class="fas fa-inbox fa-3x mb-3"></i>
                            <p>No activity logs found matching your criteria.</p>
                        </div>
                    </td>
                </tr>
            `;
            return;
        }

        data.results.forEach(log => {
            const row = this.createTableRow(log);
            tbody.appendChild(row);
        });

        // Rebind row events
        this.bindRowEvents();
    }

    /**
     * Create a table row for an activity log
     */
    createTableRow(log) {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>
                <div class="d-flex align-items-center">
                    <div class="avatar-sm bg-primary text-white rounded-circle d-flex align-items-center justify-content-center mr-2" 
                         style="width: 32px; height: 32px;">
                        ${log.user.username.charAt(0).toUpperCase()}
                    </div>
                    <div>
                        <div class="font-weight-bold">${log.user.full_name || log.user.username}</div>
                        <small class="text-muted">${log.user.email}</small>
                    </div>
                </div>
            </td>
            <td>
                <span class="action-badge action-${log.action_type.toLowerCase()}">
                    ${log.action_type_display}
                </span>
            </td>
            <td>
                <div class="text-truncate" style="max-width: 300px;" title="${log.description}">
                    ${log.description}
                </div>
            </td>
            <td>
                <span class="severity-badge severity-${log.severity.toLowerCase()}">
                    ${log.severity_display}
                </span>
            </td>
            <td>
                <code>${log.ip_address || 'N/A'}</code>
            </td>
            <td>
                <div>${this.formatDate(log.timestamp)}</div>
                <small class="text-muted">${this.formatTime(log.timestamp)}</small>
            </td>
            <td>
                <div class="btn-group" role="group">
                    <a href="/activity-logs/${log.id}/" class="btn btn-sm btn-outline-primary" title="View Details">
                        <i class="fas fa-eye"></i>
                    </a>
                    <a href="/activity-logs/${log.id}/update/" class="btn btn-sm btn-outline-warning" title="Edit">
                        <i class="fas fa-edit"></i>
                    </a>
                    <a href="/activity-logs/${log.id}/delete/" class="btn btn-sm btn-outline-danger" title="Delete">
                        <i class="fas fa-trash"></i>
                    </a>
                </div>
            </td>
        `;
        return row;
    }

    /**
     * Handle export button clicks
     */
    async handleExport(e) {
        e.preventDefault();
        const btn = e.currentTarget;
        const format = btn.classList.contains('export-csv') ? 'csv' : 
                      btn.classList.contains('export-json') ? 'json' : 'xml';
        
        try {
            this.showLoadingState(btn);
            
            // Get current search parameters
            const searchParams = new URLSearchParams(window.location.search);
            searchParams.append('format', format);
            
            const response = await fetch(`/activity-logs/export/?${searchParams.toString()}`);
            
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `activity_logs_${new Date().toISOString().split('T')[0]}.${format}`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
                
                this.showNotification(`Export completed successfully!`, 'success');
            } else {
                throw new Error('Export failed');
            }
        } catch (error) {
            console.error('Export error:', error);
            this.showNotification('Export failed. Please try again.', 'error');
        } finally {
            this.hideLoadingState(btn);
        }
    }

    /**
     * Show loading state on button
     */
    showLoadingState(btn) {
        btn.classList.add('loading');
        btn.disabled = true;
        const originalText = btn.innerHTML;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Processing...';
        btn.dataset.originalText = originalText;
    }

    /**
     * Hide loading state on button
     */
    hideLoadingState(btn) {
        btn.classList.remove('loading');
        btn.disabled = false;
        if (btn.dataset.originalText) {
            btn.innerHTML = btn.dataset.originalText;
            delete btn.dataset.originalText;
        }
    }

    /**
     * Handle date filter changes
     */
    handleDateFilterChange(input) {
        const dateFrom = document.querySelector('input[name="date_from"]').value;
        const dateTo = document.querySelector('input[name="date_to"]').value;
        
        if (dateFrom && dateTo && dateFrom > dateTo) {
            this.showNotification('Start date cannot be after end date', 'warning');
            input.value = '';
            return;
        }
    }

    /**
     * Clear all filters
     */
    clearFilters() {
        const form = document.querySelector('.search-filters form');
        if (form) {
            form.reset();
            window.location.href = window.location.pathname;
        }
    }

    /**
     * Handle table row clicks
     */
    handleRowClick(e) {
        // Don't trigger if clicking on action buttons
        if (e.target.closest('.btn-group')) {
            return;
        }
        
        // Add visual feedback
        const row = e.currentTarget;
        row.style.backgroundColor = 'rgba(102, 126, 234, 0.1)';
        setTimeout(() => {
            row.style.backgroundColor = '';
        }, 200);
    }

    /**
     * Handle pagination clicks
     */
    handlePagination(e) {
        e.preventDefault();
        const link = e.currentTarget;
        const url = link.href;
        
        // Update URL and perform AJAX request
        window.history.pushState({}, '', url);
        this.loadPage(url);
    }

    /**
     * Load page content via AJAX
     */
    async loadPage(url) {
        try {
            const response = await fetch(url + '&ajax=1', {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.updateTableContent(data);
                this.updatePagination(data.pagination);
                this.scrollToTop();
            }
        } catch (error) {
            console.error('Page load error:', error);
            this.showNotification('Failed to load page. Please refresh.', 'error');
        }
    }

    /**
     * Update pagination controls
     */
    updatePagination(paginationData) {
        const paginationContainer = document.querySelector('.pagination-container');
        if (!paginationContainer || !paginationData) return;

        // Update pagination HTML
        paginationContainer.innerHTML = paginationData.html;
        
        // Rebind pagination events
        this.bindPaginationEvents();
    }

    /**
     * Bind pagination events
     */
    bindPaginationEvents() {
        const paginationLinks = document.querySelectorAll('.pagination-container .page-link');
        paginationLinks.forEach(link => {
            link.addEventListener('click', this.handlePagination.bind(this));
        });
    }

    /**
     * Bind row events
     */
    bindRowEvents() {
        const tableRows = document.querySelectorAll('.table tbody tr');
        tableRows.forEach(row => {
            row.addEventListener('click', this.handleRowClick.bind(this));
        });
    }

    /**
     * Start real-time updates
     */
    startRealTimeUpdates() {
        this.realTimeInterval = setInterval(() => {
            this.refreshData();
        }, 30000); // Refresh every 30 seconds
    }

    /**
     * Stop real-time updates
     */
    stopRealTimeUpdates() {
        if (this.realTimeInterval) {
            clearInterval(this.realTimeInterval);
            this.realTimeInterval = null;
        }
    }

    /**
     * Toggle real-time refresh
     */
    toggleRealTimeRefresh(e) {
        if (e.target.checked) {
            this.startRealTimeUpdates();
            localStorage.setItem('activity_logs_real_time', 'true');
            this.showNotification('Real-time updates enabled', 'success');
        } else {
            this.stopRealTimeUpdates();
            localStorage.setItem('activity_logs_real_time', 'false');
            this.showNotification('Real-time updates disabled', 'info');
        }
    }

    /**
     * Refresh data from server
     */
    async refreshData() {
        try {
            const response = await fetch(window.location.href + '&ajax=1', {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.updateTableContent(data);
                this.updateCharts(data.charts);
            }
        } catch (error) {
            console.error('Refresh error:', error);
        }
    }

    /**
     * Update charts with new data
     */
    updateCharts(chartsData) {
        if (!chartsData) return;

        // Update activity chart
        if (this.activityChart && chartsData.activity) {
            this.activityChart.data.labels = chartsData.activity.labels;
            this.activityChart.data.datasets[0].data = chartsData.activity.data;
            this.activityChart.update('none');
        }

        // Update security chart
        if (this.securityChart && chartsData.security) {
            this.securityChart.data.labels = chartsData.security.labels;
            this.securityChart.data.datasets[0].data = chartsData.security.data;
            this.securityChart.update('none');
        }
    }

    /**
     * Show notification message
     */
    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        notification.innerHTML = `
            ${message}
            <button type="button" class="close" data-dismiss="alert">
                <span>&times;</span>
            </button>
        `;

        // Add to page
        document.body.appendChild(notification);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            notification.remove();
        }, 5000);

        // Handle close button
        const closeBtn = notification.querySelector('.close');
        closeBtn.addEventListener('click', () => {
            notification.remove();
        });
    }

    /**
     * Format date for display
     */
    formatDate(timestamp) {
        const date = new Date(timestamp);
        return date.toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
            year: 'numeric'
        });
    }

    /**
     * Format time for display
     */
    formatTime(timestamp) {
        const date = new Date(timestamp);
        return date.toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    /**
     * Scroll to top of page
     */
    scrollToTop() {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    }

    /**
     * Perform search with debouncing
     */
    performSearch(query) {
        if (query.length < 2) return;
        
        const searchParams = new URLSearchParams(window.location.search);
        searchParams.set('search', query);
        
        this.performAJAXSearch(searchParams);
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new ActivityLogsManager();
});

// Export for use in other modules
window.ActivityLogsManager = ActivityLogsManager;
