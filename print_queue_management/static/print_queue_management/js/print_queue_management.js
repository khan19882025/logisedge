/**
 * Print Queue Management JavaScript
 * Handles interactive functionality, real-time updates, and user interactions
 */

class PrintQueueManager {
    constructor() {
        this.refreshInterval = 30000; // 30 seconds
        this.apiEndpoints = {
            queueStats: '/utilities/print-queue-management/api/queue/stats/',
            printerStatus: '/utilities/print-queue-management/api/printer/',
        };
        this.init();
    }

    init() {
        this.bindEvents();
        this.startAutoRefresh();
        this.initializeCharts();
        this.setupRealTimeUpdates();
        this.initializeProgressBars();
    }

    bindEvents() {
        // Form validation and enhancement
        this.setupFormValidation();
        
        // Search and filter functionality
        this.setupSearchFilters();
        
        // Print job actions
        this.setupJobActions();
        
        // Printer status updates
        this.setupPrinterStatus();
        
        // Auto-print rule management
        this.setupAutoPrintRules();
        
        // Batch operations
        this.setupBatchOperations();
    }

    setupFormValidation() {
        // Auto-print rule form validation
        const autoRuleForm = document.querySelector('form[data-form="auto-print-rule"]');
        if (autoRuleForm) {
            this.setupAutoRuleValidation(autoRuleForm);
        }

        // Print job form validation
        const printJobForm = document.querySelector('form[data-form="print-job"]');
        if (printJobForm) {
            this.setupPrintJobValidation(printJobForm);
        }

        // Template form validation
        const templateForm = document.querySelector('form[data-form="print-template"]');
        if (templateForm) {
            this.setupTemplateValidation(templateForm);
        }
    }

    setupAutoRuleValidation(form) {
        const printerField = form.querySelector('[name="printer"]');
        const printerGroupField = form.querySelector('[name="printer_group"]');
        const conditionsField = form.querySelector('[name="conditions"]');

        // Toggle printer fields based on selection
        if (printerField && printerGroupField) {
            [printerField, printerGroupField].forEach(field => {
                field.addEventListener('change', () => {
                    this.togglePrinterFields(printerField, printerGroupField);
                });
            });
        }

        // Validate conditions JSON
        if (conditionsField) {
            conditionsField.addEventListener('blur', () => {
                this.validateJSONField(conditionsField);
            });
        }

        // Validate batch schedule (cron expression)
        const batchScheduleField = form.querySelector('[name="batch_schedule"]');
        if (batchScheduleField) {
            batchScheduleField.addEventListener('blur', () => {
                this.validateCronExpression(batchScheduleField);
            });
        }
    }

    togglePrinterFields(printerField, printerGroupField) {
        if (printerField.value && printerGroupField.value) {
            // Clear one field when the other is selected
            if (printerField.value) {
                printerGroupField.value = '';
                printerGroupField.classList.add('is-invalid');
                this.showFieldError(printerGroupField, 'Cannot specify both printer and printer group');
            } else {
                printerField.value = '';
                printerField.classList.add('is-invalid');
                this.showFieldError(printerField, 'Cannot specify both printer and printer group');
            }
        } else {
            // Clear validation errors
            [printerField, printerGroupField].forEach(field => {
                field.classList.remove('is-invalid');
                this.clearFieldError(field);
            });
        }
    }

    validateJSONField(field) {
        try {
            if (field.value.trim()) {
                JSON.parse(field.value);
                field.classList.remove('is-invalid');
                field.classList.add('is-valid');
                this.clearFieldError(field);
            }
        } catch (e) {
            field.classList.remove('is-valid');
            field.classList.add('is-invalid');
            this.showFieldError(field, 'Invalid JSON format');
        }
    }

    validateCronExpression(field) {
        const cronRegex = /^(\*|([0-9]|1[0-9]|2[0-9]|3[0-9]|4[0-9]|5[0-9])|\*\/([0-9]|1[0-9]|2[0-9]|3[0-9]|4[0-9]|5[0-9])) (\*|([0-9]|1[0-9]|2[0-3])|\*\/([0-9]|1[0-9]|2[0-3])) (\*|([1-9]|1[0-9]|2[0-9]|3[0-1])|\*\/([1-9]|1[0-9]|2[0-9]|3[0-1])) (\*|([1-9]|1[0-2])|\*\/([1-9]|1[0-2])) (\*|([0-6])|\*\/([0-6]))$/;
        
        if (field.value.trim() && !cronRegex.test(field.value)) {
            field.classList.add('is-invalid');
            this.showFieldError(field, 'Invalid cron expression format');
        } else {
            field.classList.remove('is-invalid');
            this.clearFieldError(field);
        }
    }

    showFieldError(field, message) {
        let errorDiv = field.parentNode.querySelector('.invalid-feedback');
        if (!errorDiv) {
            errorDiv = document.createElement('div');
            errorDiv.className = 'invalid-feedback';
            field.parentNode.appendChild(errorDiv);
        }
        errorDiv.textContent = message;
    }

    clearFieldError(field) {
        const errorDiv = field.parentNode.querySelector('.invalid-feedback');
        if (errorDiv) {
            errorDiv.remove();
        }
    }

    setupSearchFilters() {
        const searchForm = document.querySelector('.search-filter-container form');
        if (searchForm) {
            // Real-time search
            const searchField = searchForm.querySelector('[name="search"]');
            if (searchField) {
                let searchTimeout;
                searchField.addEventListener('input', (e) => {
                    clearTimeout(searchTimeout);
                    searchTimeout = setTimeout(() => {
                        this.performSearch(e.target.value);
                    }, 300);
                });
            }

            // Filter form submission
            searchForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.applyFilters(searchForm);
            });

            // Clear filters
            const clearBtn = searchForm.querySelector('.btn-clear-filters');
            if (clearBtn) {
                clearBtn.addEventListener('click', () => {
                    this.clearFilters(searchForm);
                });
            }
        }
    }

    performSearch(query) {
        const tableRows = document.querySelectorAll('tbody tr');
        tableRows.forEach(row => {
            const text = row.textContent.toLowerCase();
            const matches = text.includes(query.toLowerCase());
            row.style.display = matches ? '' : 'none';
        });
    }

    applyFilters(form) {
        const formData = new FormData(form);
        const params = new URLSearchParams();
        
        for (let [key, value] of formData.entries()) {
            if (value) {
                params.append(key, value);
            }
        }

        // Reload page with filters
        window.location.search = params.toString();
    }

    clearFilters(form) {
        form.reset();
        window.location.search = '';
    }

    setupJobActions() {
        // Job action buttons
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-action]')) {
                e.preventDefault();
                const action = e.target.dataset.action;
                const jobId = e.target.dataset.jobId;
                
                if (action && jobId) {
                    this.performJobAction(action, jobId);
                }
            }
        });

        // Bulk actions
        const bulkActionForm = document.querySelector('.bulk-actions-form');
        if (bulkActionForm) {
            this.setupBulkActions(bulkActionForm);
        }
    }

    async performJobAction(action, jobId) {
        const confirmMessages = {
            'cancel': 'Are you sure you want to cancel this print job?',
            'retry': 'Are you sure you want to retry this print job?',
            'delete': 'Are you sure you want to delete this print job? This action cannot be undone.'
        };

        if (confirmMessages[action] && !confirm(confirmMessages[action])) {
            return;
        }

        try {
            const response = await fetch(`/utilities/print-queue-management/jobs/${jobId}/action/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({ action: action })
            });

            if (response.ok) {
                this.showNotification(`Job ${action} successful`, 'success');
                this.refreshJobStatus(jobId);
            } else {
                throw new Error(`Failed to ${action} job`);
            }
        } catch (error) {
            this.showNotification(`Error: ${error.message}`, 'error');
        }
    }

    setupBulkActions(form) {
        const selectAllCheckbox = form.querySelector('.select-all');
        const jobCheckboxes = form.querySelectorAll('.job-checkbox');
        const bulkActionSelect = form.querySelector('.bulk-action-select');
        const bulkActionBtn = form.querySelector('.bulk-action-btn');

        // Select all functionality
        if (selectAllCheckbox) {
            selectAllCheckbox.addEventListener('change', (e) => {
                jobCheckboxes.forEach(checkbox => {
                    checkbox.checked = e.target.checked;
                });
                this.updateBulkActionButton();
            });
        }

        // Individual checkbox changes
        jobCheckboxes.forEach(checkbox => {
            checkbox.addEventListener('change', () => {
                this.updateBulkActionButton();
                this.updateSelectAllCheckbox();
            });
        });

        // Bulk action execution
        if (bulkActionBtn) {
            bulkActionBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.executeBulkAction(form);
            });
        }
    }

    updateBulkActionButton() {
        const selectedJobs = document.querySelectorAll('.job-checkbox:checked');
        const bulkActionBtn = document.querySelector('.bulk-action-btn');
        
        if (bulkActionBtn) {
            bulkActionBtn.disabled = selectedJobs.length === 0;
            bulkActionBtn.textContent = `Execute Action (${selectedJobs.length} selected)`;
        }
    }

    updateSelectAllCheckbox() {
        const selectAllCheckbox = document.querySelector('.select-all');
        const jobCheckboxes = document.querySelectorAll('.job-checkbox');
        const checkedCheckboxes = document.querySelectorAll('.job-checkbox:checked');
        
        if (selectAllCheckbox) {
            selectAllCheckbox.checked = checkedCheckboxes.length === jobCheckboxes.length;
            selectAllCheckbox.indeterminate = checkedCheckboxes.length > 0 && checkedCheckboxes.length < jobCheckboxes.length;
        }
    }

    async executeBulkAction(form) {
        const selectedJobs = Array.from(document.querySelectorAll('.job-checkbox:checked'))
            .map(checkbox => checkbox.value);
        const action = form.querySelector('.bulk-action-select').value;

        if (!action || selectedJobs.length === 0) {
            this.showNotification('Please select an action and jobs', 'warning');
            return;
        }

        try {
            const response = await fetch('/utilities/print-queue-management/jobs/bulk-action/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    action: action,
                    job_ids: selectedJobs
                })
            });

            if (response.ok) {
                this.showNotification(`Bulk ${action} completed successfully`, 'success');
                location.reload(); // Refresh to show updated status
            } else {
                throw new Error('Bulk action failed');
            }
        } catch (error) {
            this.showNotification(`Error: ${error.message}`, 'error');
        }
    }

    setupPrinterStatus() {
        // Real-time printer status updates
        const printerStatusElements = document.querySelectorAll('[data-printer-id]');
        printerStatusElements.forEach(element => {
            const printerId = element.dataset.printerId;
            this.updatePrinterStatus(printerId, element);
        });
    }

    async updatePrinterStatus(printerId, element) {
        try {
            const response = await fetch(`${this.apiEndpoints.printerStatus}${printerId}/status/`);
            const data = await response.json();
            
            this.updatePrinterStatusUI(element, data);
        } catch (error) {
            console.error('Error updating printer status:', error);
        }
    }

    updatePrinterStatusUI(element, data) {
        const statusBadge = element.querySelector('.status-badge');
        const activeJobsSpan = element.querySelector('.active-jobs');
        const progressBar = element.querySelector('.progress-bar');

        if (statusBadge) {
            statusBadge.textContent = data.status;
            statusBadge.className = `status-badge status-${data.status}`;
        }

        if (activeJobsSpan) {
            activeJobsSpan.textContent = data.active_jobs;
        }

        if (progressBar) {
            const percentage = (data.active_jobs / data.max_job_size) * 100;
            progressBar.style.width = `${percentage}%`;
            progressBar.className = `progress-bar bg-${this.getStatusColor(data.status)}`;
        }
    }

    getStatusColor(status) {
        const colorMap = {
            'idle': 'success',
            'busy': 'warning',
            'queue_full': 'danger',
            'offline': 'secondary'
        };
        return colorMap[status] || 'secondary';
    }

    setupAutoPrintRules() {
        // Rule activation/deactivation
        const ruleToggleSwitches = document.querySelectorAll('.rule-toggle');
        ruleToggleSwitches.forEach(toggle => {
            toggle.addEventListener('change', (e) => {
                this.toggleRuleStatus(e.target.dataset.ruleId, e.target.checked);
            });
        });

        // Rule testing
        const testRuleBtns = document.querySelectorAll('.test-rule');
        testRuleBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                this.testAutoPrintRule(btn.dataset.ruleId);
            });
        });
    }

    async toggleRuleStatus(ruleId, isActive) {
        try {
            const response = await fetch(`/utilities/print-queue-management/rules/${ruleId}/toggle/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({ is_active: isActive })
            });

            if (response.ok) {
                this.showNotification(`Rule ${isActive ? 'activated' : 'deactivated'} successfully`, 'success');
            } else {
                throw new Error('Failed to update rule status');
            }
        } catch (error) {
            this.showNotification(`Error: ${error.message}`, 'error');
            // Revert toggle switch
            const toggle = document.querySelector(`[data-rule-id="${ruleId}"]`);
            if (toggle) {
                toggle.checked = !isActive;
            }
        }
    }

    async testAutoPrintRule(ruleId) {
        try {
            const response = await fetch(`/utilities/print-queue-management/rules/${ruleId}/test/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                }
            });

            if (response.ok) {
                this.showNotification('Test rule executed successfully', 'success');
            } else {
                throw new Error('Test rule execution failed');
            }
        } catch (error) {
            this.showNotification(`Error: ${error.message}`, 'error');
        }
    }

    setupBatchOperations() {
        // Batch job scheduling
        const batchScheduleForm = document.querySelector('.batch-schedule-form');
        if (batchScheduleForm) {
            batchScheduleForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.scheduleBatchJob(batchScheduleForm);
            });
        }

        // Batch job monitoring
        const batchJobElements = document.querySelectorAll('[data-batch-job-id]');
        batchJobElements.forEach(element => {
            this.monitorBatchJob(element.dataset.batchJobId, element);
        });
    }

    initializeProgressBars() {
        // Initialize progress bars for printer status
        const progressBars = document.querySelectorAll('.progress-bar[data-width-ratio]');
        progressBars.forEach(bar => {
            const widthRatio = bar.getAttribute('data-width-ratio');
            if (widthRatio && !isNaN(widthRatio)) {
                bar.style.width = widthRatio + '%';
            }
        });
    }

    async scheduleBatchJob(form) {
        const formData = new FormData(form);
        
        try {
            const response = await fetch('/utilities/print-queue-management/batch-jobs/schedule/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: formData
            });

            if (response.ok) {
                this.showNotification('Batch job scheduled successfully', 'success');
                form.reset();
            } else {
                throw new Error('Failed to schedule batch job');
            }
        } catch (error) {
            this.showNotification(`Error: ${error.message}`, 'error');
        }
    }

    monitorBatchJob(batchJobId, element) {
        const progressBar = element.querySelector('.progress-bar');
        const statusBadge = element.querySelector('.status-badge');
        
        // Update progress every 10 seconds
        setInterval(async () => {
            try {
                const response = await fetch(`/utilities/print-queue-management/batch-jobs/${batchJobId}/status/`);
                const data = await response.json();
                
                if (progressBar) {
                    progressBar.style.width = `${data.progress_percentage}%`;
                }
                
                if (statusBadge) {
                    statusBadge.textContent = data.status;
                    statusBadge.className = `status-badge status-${data.status}`;
                }
                
                // Stop monitoring if completed or failed
                if (['completed', 'failed', 'cancelled'].includes(data.status)) {
                    clearInterval(this.monitoringInterval);
                }
            } catch (error) {
                console.error('Error monitoring batch job:', error);
            }
        }, 10000);
    }

    initializeCharts() {
        // Initialize any charts if they exist
        const chartElements = document.querySelectorAll('[data-chart]');
        chartElements.forEach(element => {
            const chartType = element.dataset.chart;
            this.createChart(element, chartType);
        });
    }

    createChart(element, type) {
        // Chart.js implementation would go here
        // This is a placeholder for chart functionality
        console.log(`Creating ${type} chart for element:`, element);
    }

    setupRealTimeUpdates() {
        // WebSocket or Server-Sent Events for real-time updates
        // For now, using polling with the refresh interval
        console.log('Setting up real-time updates...');
    }

    startAutoRefresh() {
        // Auto-refresh queue statistics
        setInterval(() => {
            this.refreshQueueStats();
        }, this.refreshInterval);
    }

    async refreshQueueStats() {
        try {
            const response = await fetch(this.apiEndpoints.queueStats);
            const data = await response.json();
            
            this.updateQueueStatsUI(data);
        } catch (error) {
            console.error('Error refreshing queue stats:', error);
        }
    }

    updateQueueStatsUI(stats) {
        // Update statistics cards
        const statElements = {
            'queued': '.stat-queued .stat-value',
            'processing': '.stat-processing .stat-value',
            'printing': '.stat-printing .stat-value',
            'completed': '.stat-completed .stat-value',
            'failed': '.stat-failed .stat-value'
        };

        Object.entries(statElements).forEach(([key, selector]) => {
            const element = document.querySelector(selector);
            if (element && stats[key] !== undefined) {
                element.textContent = stats[key];
            }
        });

        // Update charts if they exist
        this.updateCharts(stats);
    }

    updateCharts(stats) {
        // Update any existing charts with new data
        const charts = window.printQueueCharts || {};
        Object.values(charts).forEach(chart => {
            if (chart && typeof chart.update === 'function') {
                // Update chart data based on stats
                chart.update();
            }
        });
    }

    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show`;
        notification.innerHTML = `
            ${message}
            <button type="button" class="close" data-dismiss="alert" aria-label="Close">
                <span aria-hidden="true">&times;</span>
            </button>
        `;

        // Add to page
        const container = document.querySelector('.notifications-container') || document.body;
        container.appendChild(notification);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            notification.remove();
        }, 5000);
    }

    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || 
               document.cookie.match(/csrftoken=([^;]+)/)?.[1] || '';
    }

    refreshJobStatus(jobId) {
        // Refresh specific job status
        const jobRow = document.querySelector(`[data-job-id="${jobId}"]`);
        if (jobRow) {
            // Update job status in the UI
            this.updateJobStatusUI(jobRow);
        }
    }

    updateJobStatusUI(jobRow) {
        // Update job status display
        const statusCell = jobRow.querySelector('.status-cell');
        if (statusCell) {
            // Fetch updated status and update UI
            // This would typically involve an API call
        }
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    window.printQueueManager = new PrintQueueManager();
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PrintQueueManager;
}
