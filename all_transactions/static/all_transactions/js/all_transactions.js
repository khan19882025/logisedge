/**
 * All Transactions View JavaScript
 * Handles filtering, searching, pagination, and interactive features
 */

class AllTransactionsView {
    constructor() {
        this.currentPage = 1;
        this.isLoading = false;
        this.filters = {};
        this.init();
    }

    init() {
        this.bindEvents();
        this.initializeTooltips();
        this.initializeDatePickers();
        this.setupAutoRefresh();
        this.loadInitialData();
    }

    bindEvents() {
        // Filter form events
        $('#filter-form').on('submit', (e) => this.handleFilterSubmit(e));
        $('#clear-filters').on('click', (e) => this.clearFilters(e));
        
        // Search functionality
        $('#search-input').on('input', this.debounce(() => this.handleSearch(), 500));
        
        // Pagination events
        $(document).on('click', '.pagination .page-link', (e) => this.handlePagination(e));
        
        // Table row click events
        $(document).on('click', '.transaction-row', (e) => this.handleRowClick(e));
        
        // Export buttons
        $('#export-excel').on('click', () => this.exportData('excel'));
        $('#export-pdf').on('click', () => this.exportData('pdf'));
        
        // Quick filters
        $('.quick-filter').on('click', (e) => this.handleQuickFilter(e));
        
        // Column sorting
        $('.sortable-column').on('click', (e) => this.handleSort(e));
        
        // Responsive table toggle
        $('#toggle-filters').on('click', () => this.toggleFilters());
        
        // Keyboard shortcuts
        $(document).on('keydown', (e) => this.handleKeyboardShortcuts(e));
    }

    initializeTooltips() {
        // Initialize Bootstrap tooltips
        $('[data-bs-toggle="tooltip"]').tooltip();
        
        // Custom tooltips for transaction types
        $('.transaction-type-badge').each(function() {
            const type = $(this).data('type');
            const description = this.getTransactionTypeDescription(type);
            $(this).attr('title', description);
        });
    }

    initializeDatePickers() {
        // Initialize date range picker if available
        if (typeof $.fn.daterangepicker !== 'undefined') {
            $('#date-range').daterangepicker({
                opens: 'left',
                locale: {
                    format: 'YYYY-MM-DD'
                },
                ranges: {
                    'Today': [moment(), moment()],
                    'Yesterday': [moment().subtract(1, 'days'), moment().subtract(1, 'days')],
                    'Last 7 Days': [moment().subtract(6, 'days'), moment()],
                    'Last 30 Days': [moment().subtract(29, 'days'), moment()],
                    'This Month': [moment().startOf('month'), moment().endOf('month')],
                    'Last Month': [moment().subtract(1, 'month').startOf('month'), moment().subtract(1, 'month').endOf('month')]
                }
            }, (start, end) => {
                $('#date_from').val(start.format('YYYY-MM-DD'));
                $('#date_to').val(end.format('YYYY-MM-DD'));
                this.applyFilters();
            });
        }
    }

    setupAutoRefresh() {
        // Auto-refresh data every 5 minutes
        setInterval(() => {
            if (!this.isLoading && $('#auto-refresh').is(':checked')) {
                this.refreshData();
            }
        }, 300000); // 5 minutes
    }

    loadInitialData() {
        // Load initial data if no filters are applied
        if (Object.keys(this.filters).length === 0) {
            this.loadTransactions();
        }
    }

    handleFilterSubmit(e) {
        e.preventDefault();
        this.collectFilters();
        this.applyFilters();
    }

    clearFilters(e) {
        e.preventDefault();
        $('#filter-form')[0].reset();
        this.filters = {};
        this.currentPage = 1;
        this.loadTransactions();
        this.showNotification('Filters cleared', 'info');
    }

    collectFilters() {
        const formData = new FormData($('#filter-form')[0]);
        this.filters = {};
        
        for (let [key, value] of formData.entries()) {
            if (value) {
                this.filters[key] = value;
            }
        }
        
        this.currentPage = 1;
    }

    applyFilters() {
        this.showLoading();
        this.loadTransactions();
    }

    handleSearch() {
        const searchTerm = $('#search-input').val();
        this.filters.search = searchTerm;
        this.currentPage = 1;
        this.loadTransactions();
    }

    handlePagination(e) {
        e.preventDefault();
        const page = $(e.currentTarget).data('page');
        if (page) {
            this.currentPage = page;
            this.loadTransactions();
        }
    }

    handleRowClick(e) {
        const transactionId = $(e.currentTarget).data('id');
        if (transactionId) {
            this.openTransactionDetail(transactionId);
        }
    }

    handleQuickFilter(e) {
        e.preventDefault();
        const filterType = $(e.currentTarget).data('filter');
        const filterValue = $(e.currentTarget).data('value');
        
        this.filters[filterType] = filterValue;
        this.currentPage = 1;
        this.applyFilters();
        
        // Update active state
        $('.quick-filter').removeClass('active');
        $(e.currentTarget).addClass('active');
    }

    handleSort(e) {
        e.preventDefault();
        const column = $(e.currentTarget).data('column');
        const currentOrder = $(e.currentTarget).data('order') || 'asc';
        const newOrder = currentOrder === 'asc' ? 'desc' : 'asc';
        
        // Update sort indicators
        $('.sortable-column').removeClass('sort-asc sort-desc');
        $(e.currentTarget).addClass(`sort-${newOrder}`);
        $(e.currentTarget).data('order', newOrder);
        
        this.filters.ordering = `${newOrder === 'desc' ? '-' : ''}${column}`;
        this.loadTransactions();
    }

    toggleFilters() {
        $('.filter-sidebar').toggleClass('collapsed');
        $('#toggle-filters i').toggleClass('fa-chevron-left fa-chevron-right');
    }

    handleKeyboardShortcuts(e) {
        // Ctrl/Cmd + F: Focus search
        if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
            e.preventDefault();
            $('#search-input').focus();
        }
        
        // Ctrl/Cmd + E: Export Excel
        if ((e.ctrlKey || e.metaKey) && e.key === 'e') {
            e.preventDefault();
            this.exportData('excel');
        }
        
        // Escape: Clear search
        if (e.key === 'Escape') {
            $('#search-input').val('');
            this.handleSearch();
        }
    }

    loadTransactions() {
        if (this.isLoading) return;
        
        this.isLoading = true;
        this.showLoading();
        
        const params = new URLSearchParams({
            page: this.currentPage,
            ...this.filters
        });
        
        $.ajax({
            url: `/accounting/all-transactions/api/transactions/?${params}`,
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            },
            success: (data) => {
                this.renderTransactions(data);
                this.updatePagination(data);
                this.updateSummary(data);
                this.hideLoading();
            },
            error: (xhr, status, error) => {
                this.hideLoading();
                this.showNotification('Error loading transactions', 'error');
                console.error('Error loading transactions:', error);
            },
            complete: () => {
                this.isLoading = false;
            }
        });
    }

    renderTransactions(data) {
        const tbody = $('#transactions-table tbody');
        tbody.empty();
        
        if (data.transactions.length === 0) {
            tbody.append(`
                <tr>
                    <td colspan="10" class="text-center py-4">
                        <div class="text-muted">
                            <i class="fas fa-inbox fa-3x mb-3"></i>
                            <p>No transactions found matching your criteria</p>
                        </div>
                    </td>
                </tr>
            `);
            return;
        }
        
        data.transactions.forEach(transaction => {
            const row = this.createTransactionRow(transaction);
            tbody.append(row);
        });
    }

    createTransactionRow(transaction) {
        const typeBadge = this.getTransactionTypeBadge(transaction.transaction_type);
        const statusBadge = this.getStatusBadge(transaction.status);
        const formattedAmount = this.formatAmount(transaction.amount);
        const formattedDate = this.formatDate(transaction.transaction_date);
        
        return `
            <tr class="transaction-row" data-id="${transaction.id}" style="cursor: pointer;">
                <td>${formattedDate}</td>
                <td>${typeBadge}</td>
                <td>
                    <strong>${transaction.document_number}</strong>
                    ${transaction.reference_number ? `<br><small class="text-muted">${transaction.reference_number}</small>` : ''}
                </td>
                <td>
                    <div class="account-name">${transaction.debit_account__account_name || '-'}</div>
                </td>
                <td>
                    <div class="account-name">${transaction.credit_account__account_name || '-'}</div>
                </td>
                <td class="amount-positive">${formattedAmount}</td>
                <td>
                    <div class="narration-text" title="${transaction.narration || ''}">
                        ${this.truncateText(transaction.narration || '', 50)}
                    </div>
                </td>
                <td>${transaction.posted_by__username}</td>
                <td>${statusBadge}</td>
                <td>
                    <div class="btn-group btn-group-sm">
                        <button class="btn btn-outline-primary btn-sm" onclick="event.stopPropagation(); allTransactionsView.openTransactionDetail(${transaction.id})">
                            <i class="fas fa-eye"></i>
                        </button>
                        <button class="btn btn-outline-secondary btn-sm" onclick="event.stopPropagation(); allTransactionsView.openSourceDocument(${JSON.stringify(transaction.source_model)}, ${transaction.source_id})">
                            <i class="fas fa-external-link-alt"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `;
    }

    updatePagination(data) {
        const pagination = $('.pagination');
        pagination.empty();
        
        if (data.total_pages <= 1) {
            pagination.hide();
            return;
        }
        
        pagination.show();
        
        // Previous button
        if (data.has_previous) {
            pagination.append(`
                <li class="page-item">
                    <a class="page-link" href="#" data-page="${data.current_page - 1}">
                        <i class="fas fa-chevron-left"></i>
                    </a>
                </li>
            `);
        }
        
        // Page numbers
        const startPage = Math.max(1, data.current_page - 2);
        const endPage = Math.min(data.total_pages, data.current_page + 2);
        
        for (let i = startPage; i <= endPage; i++) {
            const activeClass = i === data.current_page ? 'active' : '';
            pagination.append(`
                <li class="page-item ${activeClass}">
                    <a class="page-link" href="#" data-page="${i}">${i}</a>
                </li>
            `);
        }
        
        // Next button
        if (data.has_next) {
            pagination.append(`
                <li class="page-item">
                    <a class="page-link" href="#" data-page="${data.current_page + 1}">
                        <i class="fas fa-chevron-right"></i>
                    </a>
                </li>
            `);
        }
        
        // Update pagination info
        $('.pagination-info').text(
            `Showing ${((data.current_page - 1) * 25) + 1} to ${Math.min(data.current_page * 25, data.total_count)} of ${data.total_count} transactions`
        );
    }

    updateSummary(data) {
        // Update summary cards if available
        if (data.summary) {
            $('#total-transactions').text(data.summary.total_count);
            $('#total-amount').text(this.formatAmount(data.summary.total_amount));
        }
    }

    openTransactionDetail(transactionId) {
        window.open(`/accounting/all-transactions/${transactionId}/`, '_blank');
    }

    openSourceDocument(sourceModel, sourceId) {
        const url = this.getSourceDocumentUrl(sourceModel, sourceId);
        if (url) {
            window.open(url, '_blank');
        }
    }

    getSourceDocumentUrl(sourceModel, sourceId) {
        const urlMap = {
            'invoice.Invoice': `/accounting/invoice/${sourceId}/`,
            'payment_voucher.PaymentVoucher': `/accounting/payment-voucher/${sourceId}/`,
            'receipt_voucher.ReceiptVoucher': `/accounting/receipt-voucher/${sourceId}/`,
            'general_journal.GeneralJournal': `/accounting/general-journal/${sourceId}/`,
            'contra_entry.ContraEntry': `/accounting/contra-entry/${sourceId}/`,
            'adjustment_entry.AdjustmentEntry': `/accounting/adjustment-entry/${sourceId}/`,
            'opening_balance.OpeningBalanceEntry': `/accounting/opening-balance/${sourceId}/`
        };
        return urlMap[sourceModel] || '#';
    }

    exportData(format) {
        const params = new URLSearchParams({
            export_format: format,
            ...this.filters
        });
        
        window.open(`/accounting/all-transactions/?${params}`, '_blank');
        this.showNotification(`Exporting to ${format.toUpperCase()}...`, 'info');
    }

    refreshData() {
        this.loadTransactions();
        this.showNotification('Data refreshed', 'success');
    }

    getTransactionTypeBadge(type) {
        const badges = {
            'sales_invoice': '<span class="transaction-type-badge badge-sales-invoice">Sales</span>',
            'purchase_invoice': '<span class="transaction-type-badge badge-purchase-invoice">Purchase</span>',
            'payment_voucher': '<span class="transaction-type-badge badge-payment-voucher">Payment</span>',
            'receipt_voucher': '<span class="transaction-type-badge badge-receipt-voucher">Receipt</span>',
            'journal_entry': '<span class="transaction-type-badge badge-journal-entry">Journal</span>',
            'contra_entry': '<span class="transaction-type-badge badge-contra-entry">Contra</span>',
            'adjustment_entry': '<span class="transaction-type-badge badge-adjustment-entry">Adjustment</span>',
            'opening_balance': '<span class="transaction-type-badge badge-opening-balance">Opening</span>'
        };
        return badges[type] || `<span class="transaction-type-badge">${type}</span>`;
    }

    getStatusBadge(status) {
        const badges = {
            'posted': '<span class="status-badge badge-posted">Posted</span>',
            'draft': '<span class="status-badge badge-draft">Draft</span>',
            'reversed': '<span class="status-badge badge-reversed">Reversed</span>'
        };
        return badges[status] || `<span class="status-badge">${status}</span>`;
    }

    getTransactionTypeDescription(type) {
        const descriptions = {
            'sales_invoice': 'Sales invoice transaction',
            'purchase_invoice': 'Purchase invoice transaction',
            'payment_voucher': 'Payment voucher transaction',
            'receipt_voucher': 'Receipt voucher transaction',
            'journal_entry': 'General journal entry',
            'contra_entry': 'Contra entry transaction',
            'adjustment_entry': 'Adjustment entry transaction',
            'opening_balance': 'Opening balance entry'
        };
        return descriptions[type] || 'Transaction';
    }

    formatAmount(amount) {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'AED',
            minimumFractionDigits: 2
        }).format(amount);
    }

    formatDate(dateString) {
        return new Date(dateString).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    }

    truncateText(text, maxLength) {
        if (text.length <= maxLength) return text;
        return text.substring(0, maxLength) + '...';
    }

    showLoading() {
        if (!$('.loading-overlay').length) {
            $('body').append(`
                <div class="loading-overlay">
                    <div class="spinner"></div>
                </div>
            `);
        }
        $('.loading-overlay').show();
    }

    hideLoading() {
        $('.loading-overlay').hide();
    }

    showNotification(message, type = 'info') {
        const alertClass = {
            'success': 'alert-success',
            'error': 'alert-danger',
            'warning': 'alert-warning',
            'info': 'alert-info'
        }[type] || 'alert-info';
        
        const alert = $(`
            <div class="alert ${alertClass} alert-dismissible fade show" role="alert">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `);
        
        $('.notifications-container').append(alert);
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            alert.alert('close');
        }, 5000);
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
    window.allTransactionsView = new AllTransactionsView();
    
    // Global functions for inline event handlers
    window.openTransactionDetail = (id) => allTransactionsView.openTransactionDetail(id);
    window.openSourceDocument = (model, id) => allTransactionsView.openSourceDocument(model, id);
    window.exportData = (format) => allTransactionsView.exportData(format);
});