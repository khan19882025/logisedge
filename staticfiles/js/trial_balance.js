/**
 * Trial Balance JavaScript - Modern Professional Interactions
 */

class TrialBalance {
    constructor() {
        this.init();
    }

    init() {
        this.bindEvents();
        this.initializeComponents();
        this.setupAutoRefresh();
    }

    bindEvents() {
        // Filter form submission
        const filterForm = document.getElementById('trial-balance-filter-form');
        if (filterForm) {
            filterForm.addEventListener('submit', this.handleFilterSubmit.bind(this));
        }

        // Export button
        const exportBtn = document.getElementById('export-btn');
        if (exportBtn) {
            exportBtn.addEventListener('click', this.showExportModal.bind(this));
        }

        // Export modal events
        this.setupExportModal();

        // Print button
        const printBtn = document.getElementById('print-btn');
        if (printBtn) {
            printBtn.addEventListener('click', this.handlePrint.bind(this));
        }

        // Refresh button
        const refreshBtn = document.getElementById('refresh-btn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', this.handleRefresh.bind(this));
        }

        // Date range quick select
        this.setupDateRangeQuickSelect();

        // Table sorting
        this.setupTableSorting();

        // Search functionality
        this.setupSearch();

        // Keyboard shortcuts
        this.setupKeyboardShortcuts();
    }

    initializeComponents() {
        // Initialize tooltips
        this.initializeTooltips();

        // Initialize loading states
        this.initializeLoadingStates();

        // Initialize responsive table
        this.initializeResponsiveTable();
    }

    setupAutoRefresh() {
        // Auto-refresh every 5 minutes if data is stale
        setInterval(() => {
            const lastUpdate = document.querySelector('[data-last-update]');
            if (lastUpdate) {
                const lastUpdateTime = new Date(lastUpdate.dataset.lastUpdate);
                const now = new Date();
                const diffMinutes = (now - lastUpdateTime) / (1000 * 60);
                
                if (diffMinutes > 5) {
                    this.showNotification('Data may be stale. Consider refreshing.', 'info');
                }
            }
        }, 300000); // 5 minutes
    }

    handleFilterSubmit(event) {
        event.preventDefault();
        
        const form = event.target;
        const formData = new FormData(form);
        
        // Show loading state
        this.showLoading();
        
        // Build query string
        const params = new URLSearchParams();
        for (let [key, value] of formData.entries()) {
            if (value) {
                params.append(key, value);
            }
        }
        
        // Navigate to filtered results
        window.location.href = `${window.location.pathname}?${params.toString()}`;
    }

    showExportModal() {
        const modal = document.getElementById('export-modal');
        if (modal) {
            modal.classList.add('show');
            document.body.style.overflow = 'hidden';
            
            // Focus first input
            const firstInput = modal.querySelector('input');
            if (firstInput) {
                firstInput.focus();
            }
        }
    }

    hideExportModal() {
        const modal = document.getElementById('export-modal');
        if (modal) {
            modal.classList.remove('show');
            document.body.style.overflow = '';
        }
    }

    setupExportModal() {
        const modal = document.getElementById('export-modal');
        if (!modal) return;

        // Close button
        const closeBtn = modal.querySelector('.export-modal-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', this.hideExportModal.bind(this));
        }

        // Click outside to close
        modal.addEventListener('click', (event) => {
            if (event.target === modal) {
                this.hideExportModal();
            }
        });

        // Export form submission
        const exportForm = modal.querySelector('#export-form');
        if (exportForm) {
            exportForm.addEventListener('submit', this.handleExport.bind(this));
        }

        // ESC key to close
        document.addEventListener('keydown', (event) => {
            if (event.key === 'Escape' && modal.classList.contains('show')) {
                this.hideExportModal();
            }
        });
    }

    handleExport(event) {
        event.preventDefault();
        
        const form = event.target;
        const formData = new FormData(form);
        
        // Add current filter parameters
        const currentParams = new URLSearchParams(window.location.search);
        for (let [key, value] of currentParams.entries()) {
            formData.append(key, value);
        }
        
        // Show loading state
        this.showLoading();
        
        // Submit export request
        fetch('{% url "trial_balance:export_trial_balance" %}', {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': this.getCSRFToken()
            }
        })
        .then(response => {
            if (response.ok) {
                return response.blob();
            }
            throw new Error('Export failed');
        })
        .then(blob => {
            // Create download link
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `trial_balance_${new Date().toISOString().split('T')[0]}.${formData.get('export_format')}`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
            this.hideExportModal();
            this.showNotification('Export completed successfully!', 'success');
        })
        .catch(error => {
            console.error('Export error:', error);
            this.showNotification('Export failed. Please try again.', 'error');
        })
        .finally(() => {
            this.hideLoading();
        });
    }

    handlePrint() {
        window.print();
    }

    handleRefresh() {
        this.showLoading();
        window.location.reload();
    }

    setupDateRangeQuickSelect() {
        const quickSelectContainer = document.getElementById('date-range-quick-select');
        if (!quickSelectContainer) return;

        const quickSelects = quickSelectContainer.querySelectorAll('.quick-select-btn');
        quickSelects.forEach(btn => {
            btn.addEventListener('click', (event) => {
                event.preventDefault();
                
                const range = btn.dataset.range;
                const { fromDate, toDate } = this.calculateDateRange(range);
                
                // Update form fields
                const fromDateInput = document.getElementById('id_from_date');
                const toDateInput = document.getElementById('id_to_date');
                
                if (fromDateInput) fromDateInput.value = fromDate;
                if (toDateInput) toDateInput.value = toDate;
                
                // Submit form
                const form = document.getElementById('trial-balance-filter-form');
                if (form) {
                    form.submit();
                }
            });
        });
    }

    calculateDateRange(range) {
        const today = new Date();
        let fromDate, toDate;
        
        switch (range) {
            case 'today':
                fromDate = toDate = today.toISOString().split('T')[0];
                break;
            case 'yesterday':
                const yesterday = new Date(today);
                yesterday.setDate(yesterday.getDate() - 1);
                fromDate = toDate = yesterday.toISOString().split('T')[0];
                break;
            case 'this-week':
                const startOfWeek = new Date(today);
                startOfWeek.setDate(today.getDate() - today.getDay());
                fromDate = startOfWeek.toISOString().split('T')[0];
                toDate = today.toISOString().split('T')[0];
                break;
            case 'this-month':
                fromDate = new Date(today.getFullYear(), today.getMonth(), 1).toISOString().split('T')[0];
                toDate = today.toISOString().split('T')[0];
                break;
            case 'last-month':
                const lastMonth = new Date(today.getFullYear(), today.getMonth() - 1, 1);
                fromDate = lastMonth.toISOString().split('T')[0];
                toDate = new Date(today.getFullYear(), today.getMonth(), 0).toISOString().split('T')[0];
                break;
            case 'this-quarter':
                const quarter = Math.floor(today.getMonth() / 3);
                const startOfQuarter = new Date(today.getFullYear(), quarter * 3, 1);
                fromDate = startOfQuarter.toISOString().split('T')[0];
                toDate = today.toISOString().split('T')[0];
                break;
            case 'this-year':
                fromDate = new Date(today.getFullYear(), 0, 1).toISOString().split('T')[0];
                toDate = today.toISOString().split('T')[0];
                break;
            default:
                fromDate = toDate = today.toISOString().split('T')[0];
        }
        
        return { fromDate, toDate };
    }

    setupTableSorting() {
        const table = document.querySelector('.table');
        if (!table) return;

        const headers = table.querySelectorAll('thead th[data-sortable]');
        headers.forEach(header => {
            header.addEventListener('click', () => {
                this.sortTable(header);
            });
            
            // Add sort indicator
            header.style.cursor = 'pointer';
            header.innerHTML += ' <span class="sort-indicator">↕</span>';
        });
    }

    sortTable(header) {
        const table = header.closest('table');
        const tbody = table.querySelector('tbody');
        const rows = Array.from(tbody.querySelectorAll('tr'));
        const columnIndex = Array.from(header.parentElement.children).indexOf(header);
        const isAscending = !header.classList.contains('sort-asc');
        
        // Clear other sort indicators
        table.querySelectorAll('th').forEach(th => {
            th.classList.remove('sort-asc', 'sort-desc');
        });
        
        // Set current sort direction
        header.classList.add(isAscending ? 'sort-asc' : 'sort-desc');
        
        // Sort rows
        rows.sort((a, b) => {
            const aValue = a.children[columnIndex]?.textContent || '';
            const bValue = b.children[columnIndex]?.textContent || '';
            
            // Handle numeric values
            const aNum = parseFloat(aValue.replace(/[^\d.-]/g, ''));
            const bNum = parseFloat(bValue.replace(/[^\d.-]/g, ''));
            
            if (!isNaN(aNum) && !isNaN(bNum)) {
                return isAscending ? aNum - bNum : bNum - aNum;
            }
            
            // Handle text values
            return isAscending ? 
                aValue.localeCompare(bValue) : 
                bValue.localeCompare(aValue);
        });
        
        // Reorder rows
        rows.forEach(row => tbody.appendChild(row));
        
        // Update sort indicator
        const indicator = header.querySelector('.sort-indicator');
        if (indicator) {
            indicator.textContent = isAscending ? '↑' : '↓';
        }
    }

    setupSearch() {
        const searchInput = document.getElementById('table-search');
        if (!searchInput) return;

        searchInput.addEventListener('input', (event) => {
            const searchTerm = event.target.value.toLowerCase();
            const table = document.querySelector('.table');
            const rows = table.querySelectorAll('tbody tr');
            
            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                const isVisible = text.includes(searchTerm);
                row.style.display = isVisible ? '' : 'none';
            });
            
            // Update row count
            this.updateRowCount();
        });
    }

    updateRowCount() {
        const table = document.querySelector('.table');
        const visibleRows = table.querySelectorAll('tbody tr:not([style*="display: none"])').length;
        const totalRows = table.querySelectorAll('tbody tr').length;
        
        const countElement = document.getElementById('row-count');
        if (countElement) {
            countElement.textContent = `${visibleRows} of ${totalRows} accounts`;
        }
    }

    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (event) => {
            // Ctrl/Cmd + F: Focus search
            if ((event.ctrlKey || event.metaKey) && event.key === 'f') {
                event.preventDefault();
                const searchInput = document.getElementById('table-search');
                if (searchInput) {
                    searchInput.focus();
                }
            }
            
            // Ctrl/Cmd + E: Export
            if ((event.ctrlKey || event.metaKey) && event.key === 'e') {
                event.preventDefault();
                this.showExportModal();
            }
            
            // Ctrl/Cmd + P: Print
            if ((event.ctrlKey || event.metaKey) && event.key === 'p') {
                event.preventDefault();
                this.handlePrint();
            }
            
            // F5: Refresh
            if (event.key === 'F5') {
                event.preventDefault();
                this.handleRefresh();
            }
        });
    }

    initializeTooltips() {
        // Initialize Bootstrap tooltips if available
        if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
            const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
            tooltipTriggerList.map(function (tooltipTriggerEl) {
                return new bootstrap.Tooltip(tooltipTriggerEl);
            });
        }
    }

    initializeLoadingStates() {
        // Add loading spinner to buttons
        const buttons = document.querySelectorAll('.btn');
        buttons.forEach(btn => {
            btn.addEventListener('click', () => {
                if (!btn.classList.contains('no-loading')) {
                    this.addLoadingSpinner(btn);
                }
            });
        });
    }

    addLoadingSpinner(button) {
        const originalText = button.innerHTML;
        button.innerHTML = '<span class="loading-spinner"></span> Loading...';
        button.disabled = true;
        
        // Remove spinner after a delay (or when page changes)
        setTimeout(() => {
            button.innerHTML = originalText;
            button.disabled = false;
        }, 2000);
    }

    initializeResponsiveTable() {
        const table = document.querySelector('.table');
        if (!table) return;

        // Add horizontal scroll indicator
        const tableContainer = table.closest('.table-responsive');
        if (tableContainer) {
            tableContainer.addEventListener('scroll', () => {
                const isScrollable = tableContainer.scrollWidth > tableContainer.clientWidth;
                const hasScrolled = tableContainer.scrollLeft > 0;
                
                if (isScrollable) {
                    tableContainer.classList.add('scrollable');
                    if (hasScrolled) {
                        tableContainer.classList.add('scrolled');
                    } else {
                        tableContainer.classList.remove('scrolled');
                    }
                }
            });
        }
    }

    showLoading() {
        document.body.classList.add('loading');
        const loadingOverlay = document.createElement('div');
        loadingOverlay.className = 'loading-overlay';
        loadingOverlay.innerHTML = '<div class="loading-spinner"></div><p>Loading trial balance data...</p>';
        document.body.appendChild(loadingOverlay);
    }

    hideLoading() {
        document.body.classList.remove('loading');
        const loadingOverlay = document.querySelector('.loading-overlay');
        if (loadingOverlay) {
            loadingOverlay.remove();
        }
    }

    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <span class="notification-message">${message}</span>
                <button class="notification-close">&times;</button>
            </div>
        `;
        
        // Add to page
        document.body.appendChild(notification);
        
        // Show notification
        setTimeout(() => {
            notification.classList.add('show');
        }, 100);
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            this.hideNotification(notification);
        }, 5000);
        
        // Close button
        const closeBtn = notification.querySelector('.notification-close');
        closeBtn.addEventListener('click', () => {
            this.hideNotification(notification);
        });
    }

    hideNotification(notification) {
        notification.classList.remove('show');
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }

    getCSRFToken() {
        const token = document.querySelector('[name=csrfmiddlewaretoken]');
        return token ? token.value : '';
    }

    // Utility methods
    formatCurrency(amount) {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }).format(amount);
    }

    formatNumber(number) {
        return new Intl.NumberFormat('en-US', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }).format(number);
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

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new TrialBalance();
});

// Export for use in other scripts
window.TrialBalance = TrialBalance; 