/**
 * Bank Reconciliation JavaScript
 * Handles all interactive functionality for the bank reconciliation module
 */

class BankReconciliation {
    constructor() {
        this.init();
    }

    init() {
        this.bindEvents();
        this.initializeComponents();
        this.setupAutoRefresh();
    }

    bindEvents() {
        // Dashboard events
        $(document).on('click', '.stat-card', this.handleStatCardClick.bind(this));
        $(document).on('click', '.bank-account-card', this.handleBankAccountClick.bind(this));
        
        // Form events
        $(document).on('submit', '.reconciliation-form', this.handleFormSubmit.bind(this));
        $(document).on('change', '.form-control, .form-select', this.handleFormChange.bind(this));
        
        // Table events
        $(document).on('click', '.table-row', this.handleTableRowClick.bind(this));
        $(document).on('change', '.bulk-select', this.handleBulkSelect.bind(this));
        
        // Modal events
        $(document).on('show.bs.modal', '.modal', this.handleModalShow.bind(this));
        $(document).on('hidden.bs.modal', '.modal', this.handleModalHide.bind(this));
        
        // Search and filter events
        $(document).on('input', '.search-input', this.handleSearch.bind(this));
        $(document).on('change', '.filter-select', this.handleFilter.bind(this));
        
        // Export events
        $(document).on('click', '.export-btn', this.handleExport.bind(this));
        
        // Keyboard shortcuts
        $(document).on('keydown', this.handleKeyboardShortcuts.bind(this));
    }

    initializeComponents() {
        // Initialize tooltips
        $('[data-bs-toggle="tooltip"]').tooltip();
        
        // Initialize popovers
        $('[data-bs-toggle="popover"]').popover();
        
        // Initialize date pickers
        $('.date-picker').datepicker({
            format: 'yyyy-mm-dd',
            autoclose: true,
            todayHighlight: true
        });
        
        // Initialize select2 for enhanced dropdowns
        $('.select2').select2({
            theme: 'bootstrap-5',
            width: '100%'
        });
        
        // Initialize data tables
        this.initializeDataTables();
        
        // Initialize charts if Chart.js is available
        if (typeof Chart !== 'undefined') {
            this.initializeCharts();
        }
    }

    initializeDataTables() {
        $('.data-table').each(function() {
            $(this).DataTable({
                responsive: true,
                pageLength: 25,
                order: [[0, 'desc']],
                language: {
                    search: "Search:",
                    lengthMenu: "Show _MENU_ entries",
                    info: "Showing _START_ to _END_ of _TOTAL_ entries",
                    paginate: {
                        first: "First",
                        last: "Last",
                        next: "Next",
                        previous: "Previous"
                    }
                }
            });
        });
    }

    initializeCharts() {
        // Balance comparison chart
        const balanceCtx = document.getElementById('balanceChart');
        if (balanceCtx) {
            new Chart(balanceCtx, {
                type: 'bar',
                data: {
                    labels: ['Opening Balance', 'Total Credits', 'Total Debits', 'Closing Balance'],
                    datasets: [{
                        label: 'ERP',
                        data: [0, 0, 0, 0],
                        backgroundColor: 'rgba(102, 126, 234, 0.8)',
                        borderColor: 'rgba(102, 126, 234, 1)',
                        borderWidth: 1
                    }, {
                        label: 'Bank',
                        data: [0, 0, 0, 0],
                        backgroundColor: 'rgba(118, 75, 162, 0.8)',
                        borderColor: 'rgba(118, 75, 162, 1)',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        }

        // Reconciliation status chart
        const statusCtx = document.getElementById('statusChart');
        if (statusCtx) {
            new Chart(statusCtx, {
                type: 'doughnut',
                data: {
                    labels: ['Completed', 'In Progress', 'Open'],
                    datasets: [{
                        data: [0, 0, 0],
                        backgroundColor: [
                            'rgba(16, 185, 129, 0.8)',
                            'rgba(245, 158, 11, 0.8)',
                            'rgba(102, 126, 234, 0.8)'
                        ],
                        borderWidth: 2
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            position: 'bottom'
                        }
                    }
                }
            });
        }
    }

    setupAutoRefresh() {
        // Auto-refresh dashboard data every 5 minutes
        setInterval(() => {
            this.refreshDashboardData();
        }, 300000);
    }

    // Event Handlers
    handleStatCardClick(event) {
        const card = $(event.currentTarget);
        const type = card.data('type');
        
        if (type === 'sessions') {
            window.location.href = '/accounting/bank-reconciliation/sessions/';
        } else if (type === 'accounts') {
            window.location.href = '/accounting/bank-accounts/';
        }
    }

    handleBankAccountClick(event) {
        const card = $(event.currentTarget);
        const accountId = card.data('account-id');
        
        if (accountId) {
            window.location.href = `/accounting/bank-accounts/${accountId}/`;
        }
    }

    handleFormSubmit(event) {
        const form = $(event.currentTarget);
        const submitBtn = form.find('button[type="submit"]');
        const originalText = submitBtn.text();
        
        // Show loading state
        submitBtn.prop('disabled', true).html('<i class="fas fa-spinner fa-spin"></i> Processing...');
        
        // Add loading class to form
        form.addClass('loading');
        
        // Form will submit normally, reset button on page load
        setTimeout(() => {
            submitBtn.prop('disabled', false).text(originalText);
            form.removeClass('loading');
        }, 5000);
    }

    handleFormChange(event) {
        const field = $(event.currentTarget);
        const form = field.closest('form');
        
        // Auto-save form data to localStorage
        this.autoSaveForm(form);
        
        // Trigger validation
        this.validateField(field);
    }

    handleTableRowClick(event) {
        const row = $(event.currentTarget);
        const id = row.data('id');
        const type = row.data('type');
        
        if (type === 'session') {
            window.location.href = `/accounting/bank-reconciliation/sessions/${id}/`;
        } else if (type === 'account') {
            window.location.href = `/accounting/bank-accounts/${id}/`;
        }
    }

    handleBulkSelect(event) {
        const checkbox = $(event.currentTarget);
        const isChecked = checkbox.is(':checked');
        const table = checkbox.closest('table');
        
        // Select/deselect all checkboxes in the table
        table.find('.row-checkbox').prop('checked', isChecked);
        
        // Update bulk actions visibility
        this.updateBulkActions(table);
    }

    handleModalShow(event) {
        const modal = $(event.currentTarget);
        const modalId = modal.attr('id');
        
        // Load modal content if needed
        if (modalId === 'importModal') {
            this.loadImportForm(modal);
        } else if (modalId === 'matchModal') {
            this.loadMatchForm(modal);
        }
    }

    handleModalHide(event) {
        const modal = $(event.currentTarget);
        
        // Reset form and clear data
        modal.find('form')[0].reset();
        modal.find('.form-control').removeClass('is-invalid');
        modal.find('.invalid-feedback').hide();
    }

    handleSearch(event) {
        const searchTerm = $(event.currentTarget).val();
        const table = $(event.currentTarget).closest('.table-container').find('.data-table');
        
        if (table.length) {
            table.DataTable().search(searchTerm).draw();
        } else {
            // Simple search for non-DataTable tables
            this.performSimpleSearch(searchTerm);
        }
    }

    handleFilter(event) {
        const filterValue = $(event.currentTarget).val();
        const filterType = $(event.currentTarget).data('filter-type');
        
        this.applyFilter(filterType, filterValue);
    }

    handleExport(event) {
        event.preventDefault();
        const exportBtn = $(event.currentTarget);
        const exportType = exportBtn.data('export-type');
        const data = exportBtn.data('export-data');
        
        this.performExport(exportType, data);
    }

    handleKeyboardShortcuts(event) {
        // Ctrl/Cmd + N: New session
        if ((event.ctrlKey || event.metaKey) && event.key === 'n') {
            event.preventDefault();
            window.location.href = '/accounting/bank-reconciliation/sessions/create/';
        }
        
        // Ctrl/Cmd + S: Save (if in form)
        if ((event.ctrlKey || event.metaKey) && event.key === 's') {
            event.preventDefault();
            const activeForm = $('form:focus');
            if (activeForm.length) {
                activeForm.submit();
            }
        }
        
        // Escape: Close modals
        if (event.key === 'Escape') {
            $('.modal').modal('hide');
        }
    }

    // Utility Methods
    autoSaveForm(form) {
        const formData = form.serialize();
        const formId = form.attr('id') || 'default-form';
        localStorage.setItem(`bank_reconciliation_${formId}`, formData);
    }

    loadAutoSavedForm(form) {
        const formId = form.attr('id') || 'default-form';
        const savedData = localStorage.getItem(`bank_reconciliation_${formId}`);
        
        if (savedData) {
            form.deserialize(savedData);
        }
    }

    validateField(field) {
        const value = field.val();
        const fieldName = field.attr('name');
        const validationRules = this.getValidationRules(fieldName);
        
        let isValid = true;
        let errorMessage = '';
        
        // Apply validation rules
        if (validationRules.required && !value) {
            isValid = false;
            errorMessage = 'This field is required.';
        } else if (validationRules.minLength && value.length < validationRules.minLength) {
            isValid = false;
            errorMessage = `Minimum length is ${validationRules.minLength} characters.`;
        } else if (validationRules.pattern && !validationRules.pattern.test(value)) {
            isValid = false;
            errorMessage = validationRules.patternMessage || 'Invalid format.';
        }
        
        // Update field validation state
        if (isValid) {
            field.removeClass('is-invalid').addClass('is-valid');
            field.siblings('.invalid-feedback').hide();
        } else {
            field.removeClass('is-valid').addClass('is-invalid');
            field.siblings('.invalid-feedback').text(errorMessage).show();
        }
        
        return isValid;
    }

    getValidationRules(fieldName) {
        const rules = {
            'session_name': {
                required: true,
                minLength: 3
            },
            'reconciliation_date': {
                required: true
            },
            'tolerance_amount': {
                required: false,
                pattern: /^\d+(\.\d{1,2})?$/,
                patternMessage: 'Please enter a valid amount.'
            }
        };
        
        return rules[fieldName] || {};
    }

    updateBulkActions(table) {
        const checkedBoxes = table.find('.row-checkbox:checked');
        const bulkActions = table.siblings('.bulk-actions');
        
        if (checkedBoxes.length > 0) {
            bulkActions.show();
            bulkActions.find('.selected-count').text(checkedBoxes.length);
        } else {
            bulkActions.hide();
        }
    }

    performSimpleSearch(searchTerm) {
        $('.table tbody tr').each(function() {
            const row = $(this);
            const text = row.text().toLowerCase();
            const matches = text.includes(searchTerm.toLowerCase());
            row.toggle(matches);
        });
    }

    applyFilter(filterType, filterValue) {
        if (filterType === 'status') {
            $('.table tbody tr').each(function() {
                const row = $(this);
                const status = row.data('status');
                const matches = !filterValue || status === filterValue;
                row.toggle(matches);
            });
        } else if (filterType === 'date') {
            // Date range filtering logic
            this.filterByDateRange(filterValue);
        }
    }

    filterByDateRange(dateRange) {
        const today = new Date();
        let startDate, endDate;
        
        switch (dateRange) {
            case 'today':
                startDate = endDate = today;
                break;
            case 'week':
                startDate = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000);
                endDate = today;
                break;
            case 'month':
                startDate = new Date(today.getFullYear(), today.getMonth(), 1);
                endDate = today;
                break;
            default:
                return;
        }
        
        $('.table tbody tr').each(function() {
            const row = $(this);
            const dateStr = row.data('date');
            if (dateStr) {
                const rowDate = new Date(dateStr);
                const matches = rowDate >= startDate && rowDate <= endDate;
                row.toggle(matches);
            }
        });
    }

    performExport(exportType, data) {
        // Show loading state
        this.showLoading('Preparing export...');
        
        // Simulate export process
        setTimeout(() => {
            this.hideLoading();
            
            // Create and download file
            const blob = new Blob([JSON.stringify(data, null, 2)], {
                type: 'application/json'
            });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `bank_reconciliation_${exportType}_${new Date().toISOString().split('T')[0]}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            
            this.showNotification('Export completed successfully!', 'success');
        }, 2000);
    }

    // AJAX Methods
    refreshDashboardData() {
        $.ajax({
            url: '/accounting/bank-reconciliation/ajax/dashboard-data/',
            method: 'GET',
            success: (data) => {
                this.updateDashboardStats(data);
            },
            error: (xhr, status, error) => {
                console.error('Failed to refresh dashboard data:', error);
            }
        });
    }

    updateDashboardStats(data) {
        // Update statistics cards
        $('.stat-number[data-stat="total_sessions"]').text(data.total_sessions);
        $('.stat-number[data-stat="completed_sessions"]').text(data.completed_sessions);
        $('.stat-number[data-stat="open_sessions"]').text(data.open_sessions);
        
        // Update charts if they exist
        if (window.balanceChart) {
            window.balanceChart.data.datasets[0].data = data.balance_data.erp;
            window.balanceChart.data.datasets[1].data = data.balance_data.bank;
            window.balanceChart.update();
        }
        
        if (window.statusChart) {
            window.statusChart.data.datasets[0].data = [
                data.status_data.completed,
                data.status_data.in_progress,
                data.status_data.open
            ];
            window.statusChart.update();
        }
    }

    // UI Helper Methods
    showLoading(message = 'Loading...') {
        const loadingHtml = `
            <div class="loading-overlay">
                <div class="loading-spinner">
                    <i class="fas fa-spinner fa-spin"></i>
                    <p>${message}</p>
                </div>
            </div>
        `;
        
        $('body').append(loadingHtml);
    }

    hideLoading() {
        $('.loading-overlay').remove();
    }

    showNotification(message, type = 'info') {
        const notificationHtml = `
            <div class="alert alert-${type} alert-dismissible fade show" role="alert">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        $('.notifications-container').append(notificationHtml);
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            $('.alert').alert('close');
        }, 5000);
    }

    confirmAction(message, callback) {
        if (confirm(message)) {
            callback();
        }
    }

    // Session Management Methods
    createSession(formData) {
        return $.ajax({
            url: '/accounting/bank-reconciliation/sessions/create/',
            method: 'POST',
            data: formData,
            headers: {
                'X-CSRFToken': this.getCSRFToken()
            }
        });
    }

    updateSession(sessionId, formData) {
        return $.ajax({
            url: `/accounting/bank-reconciliation/sessions/${sessionId}/edit/`,
            method: 'POST',
            data: formData,
            headers: {
                'X-CSRFToken': this.getCSRFToken()
            }
        });
    }

    deleteSession(sessionId) {
        return $.ajax({
            url: `/accounting/bank-reconciliation/sessions/${sessionId}/delete/`,
            method: 'POST',
            headers: {
                'X-CSRFToken': this.getCSRFToken()
            }
        });
    }

    // Import Methods
    importBankStatement(sessionId, formData) {
        return $.ajax({
            url: `/accounting/bank-reconciliation/sessions/${sessionId}/import/`,
            method: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            headers: {
                'X-CSRFToken': this.getCSRFToken()
            }
        });
    }

    // Matching Methods
    performAutoMatch(sessionId, criteria) {
        return $.ajax({
            url: `/accounting/bank-reconciliation/sessions/${sessionId}/auto-match/`,
            method: 'POST',
            data: criteria,
            headers: {
                'X-CSRFToken': this.getCSRFToken()
            }
        });
    }

    manualMatch(sessionId, erpEntryId, bankEntryId) {
        return $.ajax({
            url: `/accounting/bank-reconciliation/sessions/${sessionId}/manual-match/`,
            method: 'POST',
            data: {
                erp_entry: erpEntryId,
                bank_entry: bankEntryId
            },
            headers: {
                'X-CSRFToken': this.getCSRFToken()
            }
        });
    }

    unmatchEntry(entryType, entryId) {
        return $.ajax({
            url: `/accounting/bank-reconciliation/ajax/unmatch/${entryType}/${entryId}/`,
            method: 'POST',
            headers: {
                'X-CSRFToken': this.getCSRFToken()
            }
        });
    }

    // Utility Methods
    getCSRFToken() {
        return $('[name=csrfmiddlewaretoken]').val() || 
               $('meta[name=csrf-token]').attr('content');
    }

    formatCurrency(amount, currency = 'AED') {
        return new Intl.NumberFormat('en-AE', {
            style: 'currency',
            currency: currency
        }).format(amount);
    }

    formatDate(date) {
        return new Intl.DateTimeFormat('en-AE', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        }).format(new Date(date));
    }

    debounce(func, wait) {
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
}

// Initialize when document is ready
$(document).ready(function() {
    window.bankReconciliation = new BankReconciliation();
    
    // Global utility functions
    window.showNotification = function(message, type) {
        window.bankReconciliation.showNotification(message, type);
    };
    
    window.confirmAction = function(message, callback) {
        window.bankReconciliation.confirmAction(message, callback);
    };
    
    window.formatCurrency = function(amount, currency) {
        return window.bankReconciliation.formatCurrency(amount, currency);
    };
    
    window.formatDate = function(date) {
        return window.bankReconciliation.formatDate(date);
    };
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = BankReconciliation;
} 