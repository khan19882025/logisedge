/**
 * Asset Register JavaScript - Modern Professional Functionality
 */

class AssetRegister {
    constructor() {
        this.init();
    }

    init() {
        this.bindEvents();
        this.initSearch();
        this.initFilters();
        this.initBulkActions();
        this.initModals();
        this.initQRScanner();
        this.initAutoSave();
        this.initKeyboardShortcuts();
    }

    bindEvents() {
        // Search functionality
        const searchInput = document.getElementById('asset-search');
        if (searchInput) {
            searchInput.addEventListener('input', this.debounce(this.handleSearch.bind(this), 300));
        }

        // Filter form submission
        const filterForm = document.getElementById('filter-form');
        if (filterForm) {
            filterForm.addEventListener('submit', this.handleFilterSubmit.bind(this));
        }

        // Bulk action checkboxes
        const selectAllCheckbox = document.getElementById('select-all');
        if (selectAllCheckbox) {
            selectAllCheckbox.addEventListener('change', this.handleSelectAll.bind(this));
        }

        // Export buttons
        const exportButtons = document.querySelectorAll('[data-export]');
        exportButtons.forEach(button => {
            button.addEventListener('click', this.handleExport.bind(this));
        });

        // QR/Barcode buttons
        const qrButtons = document.querySelectorAll('[data-qr]');
        qrButtons.forEach(button => {
            button.addEventListener('click', this.handleQRCode.bind(this));
        });

        const barcodeButtons = document.querySelectorAll('[data-barcode]');
        barcodeButtons.forEach(button => {
            button.addEventListener('click', this.handleBarcode.bind(this));
        });

        // Print buttons
        const printButtons = document.querySelectorAll('[data-print]');
        printButtons.forEach(button => {
            button.addEventListener('click', this.handlePrint.bind(this));
        });

        // Form validation
        const forms = document.querySelectorAll('form[data-validate]');
        forms.forEach(form => {
            form.addEventListener('submit', this.handleFormValidation.bind(this));
        });

        // Auto-save forms
        const autoSaveForms = document.querySelectorAll('form[data-auto-save]');
        autoSaveForms.forEach(form => {
            this.initAutoSaveForm(form);
        });
    }

    // Search functionality
    initSearch() {
        const searchInput = document.getElementById('asset-search');
        if (!searchInput) return;

        // Create autocomplete dropdown
        const autocompleteContainer = document.createElement('div');
        autocompleteContainer.className = 'autocomplete-dropdown';
        autocompleteContainer.style.display = 'none';
        searchInput.parentNode.appendChild(autocompleteContainer);

        searchInput.addEventListener('input', this.debounce(async (e) => {
            const query = e.target.value.trim();
            if (query.length < 2) {
                autocompleteContainer.style.display = 'none';
                return;
            }

            try {
                const response = await fetch(`/asset-register/ajax/search/?q=${encodeURIComponent(query)}`);
                const data = await response.json();
                this.displayAutocomplete(data.results, autocompleteContainer, searchInput);
            } catch (error) {
                console.error('Search error:', error);
            }
        }, 300));
    }

    displayAutocomplete(results, container, input) {
        if (results.length === 0) {
            container.style.display = 'none';
            return;
        }

        container.innerHTML = '';
        results.forEach(result => {
            const item = document.createElement('div');
            item.className = 'autocomplete-item';
            item.innerHTML = `
                <div class="autocomplete-code">${result.code}</div>
                <div class="autocomplete-name">${result.name}</div>
                <div class="autocomplete-location">${result.location}</div>
            `;
            item.addEventListener('click', () => {
                window.location.href = result.url;
            });
            container.appendChild(item);
        });
        container.style.display = 'block';
    }

    // Filter functionality
    initFilters() {
        const filterToggle = document.getElementById('filter-toggle');
        const filterPanel = document.getElementById('filter-panel');
        
        if (filterToggle && filterPanel) {
            filterToggle.addEventListener('click', () => {
                filterPanel.classList.toggle('show');
                filterToggle.textContent = filterPanel.classList.contains('show') ? 'Hide Filters' : 'Show Filters';
            });
        }

        // Date range picker
        const dateRangeInputs = document.querySelectorAll('input[type="date"]');
        dateRangeInputs.forEach(input => {
            input.addEventListener('change', this.handleDateRangeChange.bind(this));
        });
    }

    handleDateRangeChange(e) {
        const fromDate = document.getElementById('purchase_date_from');
        const toDate = document.getElementById('purchase_date_to');
        
        if (fromDate && toDate && fromDate.value && toDate.value) {
            if (fromDate.value > toDate.value) {
                this.showAlert('From date cannot be after to date', 'warning');
                e.target.value = '';
            }
        }
    }

    // Bulk actions
    initBulkActions() {
        const bulkActionSelect = document.getElementById('bulk-action');
        const bulkActionButton = document.getElementById('bulk-action-submit');
        
        if (bulkActionSelect && bulkActionButton) {
            bulkActionButton.addEventListener('click', this.handleBulkAction.bind(this));
        }
    }

    handleSelectAll(e) {
        const checkboxes = document.querySelectorAll('input[name="asset_ids"]');
        checkboxes.forEach(checkbox => {
            checkbox.checked = e.target.checked;
        });
        this.updateBulkActionButton();
    }

    updateBulkActionButton() {
        const selectedCount = document.querySelectorAll('input[name="asset_ids"]:checked').length;
        const bulkActionButton = document.getElementById('bulk-action-submit');
        
        if (bulkActionButton) {
            bulkActionButton.textContent = `Apply to ${selectedCount} assets`;
            bulkActionButton.disabled = selectedCount === 0;
        }
    }

    async handleBulkAction() {
        const selectedAssets = document.querySelectorAll('input[name="asset_ids"]:checked');
        const action = document.getElementById('bulk-action').value;
        
        if (selectedAssets.length === 0) {
            this.showAlert('Please select at least one asset', 'warning');
            return;
        }

        const assetIds = Array.from(selectedAssets).map(cb => cb.value);
        
        try {
            const response = await fetch('/accounting/asset-register/ajax/bulk-action/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    action: action,
                    asset_ids: assetIds
                })
            });

            const data = await response.json();
            if (data.success) {
                this.showAlert(data.message, 'success');
                setTimeout(() => window.location.reload(), 1500);
            } else {
                this.showAlert(data.message, 'danger');
            }
        } catch (error) {
            console.error('Bulk action error:', error);
            this.showAlert('An error occurred while processing the bulk action', 'danger');
        }
    }

    // Export functionality
    handleExport(e) {
        e.preventDefault();
        const format = e.target.dataset.export;
        const currentUrl = new URL(window.location);
        currentUrl.searchParams.set('format', format);
        window.location.href = currentUrl.toString();
    }

    // QR Code functionality
    handleQRCode(e) {
        e.preventDefault();
        const assetId = e.target.dataset.qr;
        window.open(`/accounting/asset-register/${assetId}/qr-code/`, '_blank');
    }

    handleBarcode(e) {
        e.preventDefault();
        const assetId = e.target.dataset.barcode;
        window.open(`/accounting/asset-register/${assetId}/barcode/`, '_blank');
    }

    // Print functionality
    handlePrint(e) {
        e.preventDefault();
        const assetId = e.target.dataset.print;
        window.open(`/accounting/asset-register/${assetId}/print/`, '_blank');
    }

    // QR Scanner functionality
    initQRScanner() {
        const scanButton = document.getElementById('qr-scan-button');
        if (scanButton) {
            scanButton.addEventListener('click', this.startQRScanner.bind(this));
        }
    }

    async startQRScanner() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } });
            this.showQRScannerModal(stream);
        } catch (error) {
            console.error('Camera access error:', error);
            this.showAlert('Unable to access camera for QR scanning', 'warning');
        }
    }

    showQRScannerModal(stream) {
        const modal = document.createElement('div');
        modal.className = 'modal show';
        modal.innerHTML = `
            <div class="modal-dialog">
                <div class="modal-header">
                    <h5 class="modal-title">QR Code Scanner</h5>
                    <button type="button" class="modal-close" onclick="this.closest('.modal').remove()">&times;</button>
                </div>
                <div class="modal-body">
                    <video id="qr-video" autoplay style="width: 100%; height: 300px;"></video>
                    <p class="text-center mt-3">Point camera at QR code to scan</p>
                </div>
            </div>
        `;
        document.body.appendChild(modal);

        const video = modal.querySelector('#qr-video');
        video.srcObject = stream;

        // Add QR code detection logic here
        // This would require a QR code detection library like jsQR
    }

    // Modal functionality
    initModals() {
        const modalTriggers = document.querySelectorAll('[data-modal]');
        modalTriggers.forEach(trigger => {
            trigger.addEventListener('click', this.showModal.bind(this));
        });

        // Close modals when clicking outside
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal')) {
                e.target.remove();
            }
        });
    }

    showModal(e) {
        e.preventDefault();
        const modalId = e.target.dataset.modal;
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.add('show');
        }
    }

    // Auto-save functionality
    initAutoSave() {
        const autoSaveForms = document.querySelectorAll('form[data-auto-save]');
        autoSaveForms.forEach(form => {
            this.initAutoSaveForm(form);
        });
    }

    initAutoSaveForm(form) {
        let autoSaveTimer;
        const inputs = form.querySelectorAll('input, textarea, select');
        
        inputs.forEach(input => {
            input.addEventListener('input', () => {
                clearTimeout(autoSaveTimer);
                autoSaveTimer = setTimeout(() => {
                    this.autoSaveForm(form);
                }, 2000);
            });
        });
    }

    async autoSaveForm(form) {
        const formData = new FormData(form);
        const saveUrl = form.dataset.saveUrl || form.action;
        
        try {
            const response = await fetch(saveUrl, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': this.getCSRFToken()
                }
            });

            if (response.ok) {
                this.showAutoSaveIndicator();
            }
        } catch (error) {
            console.error('Auto-save error:', error);
        }
    }

    showAutoSaveIndicator() {
        const indicator = document.getElementById('auto-save-indicator');
        if (indicator) {
            indicator.textContent = 'Auto-saved';
            indicator.style.display = 'block';
            setTimeout(() => {
                indicator.style.display = 'none';
            }, 2000);
        }
    }

    // Keyboard shortcuts
    initKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + N for new asset
            if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
                e.preventDefault();
                window.location.href = '/accounting/asset-register/create/';
            }

            // Ctrl/Cmd + F for search
            if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
                e.preventDefault();
                const searchInput = document.getElementById('asset-search');
                if (searchInput) {
                    searchInput.focus();
                }
            }

            // Ctrl/Cmd + E for export
            if ((e.ctrlKey || e.metaKey) && e.key === 'e') {
                e.preventDefault();
                const exportButton = document.querySelector('[data-export="excel"]');
                if (exportButton) {
                    exportButton.click();
                }
            }

            // Escape to close modals
            if (e.key === 'Escape') {
                const modals = document.querySelectorAll('.modal.show');
                modals.forEach(modal => modal.remove());
            }
        });
    }

    // Form validation
    handleFormValidation(e) {
        const form = e.target;
        const inputs = form.querySelectorAll('input, textarea, select');
        let isValid = true;

        inputs.forEach(input => {
            if (input.hasAttribute('required') && !input.value.trim()) {
                this.showFieldError(input, 'This field is required');
                isValid = false;
            } else if (input.type === 'email' && input.value && !this.isValidEmail(input.value)) {
                this.showFieldError(input, 'Please enter a valid email address');
                isValid = false;
            } else if (input.type === 'number' && input.value && input.value < 0) {
                this.showFieldError(input, 'Value cannot be negative');
                isValid = false;
            } else {
                this.clearFieldError(input);
            }
        });

        if (!isValid) {
            e.preventDefault();
        }
    }

    showFieldError(input, message) {
        input.classList.add('is-invalid');
        let errorDiv = input.parentNode.querySelector('.invalid-feedback');
        if (!errorDiv) {
            errorDiv = document.createElement('div');
            errorDiv.className = 'invalid-feedback';
            input.parentNode.appendChild(errorDiv);
        }
        errorDiv.textContent = message;
    }

    clearFieldError(input) {
        input.classList.remove('is-invalid');
        const errorDiv = input.parentNode.querySelector('.invalid-feedback');
        if (errorDiv) {
            errorDiv.remove();
        }
    }

    isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }

    // Utility functions
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

    getCSRFToken() {
        const token = document.querySelector('[name=csrfmiddlewaretoken]');
        return token ? token.value : '';
    }

    showAlert(message, type = 'info') {
        const alertContainer = document.getElementById('alert-container') || document.body;
        const alert = document.createElement('div');
        alert.className = `alert alert-${type} alert-dismissible fade show`;
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        alertContainer.appendChild(alert);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            alert.remove();
        }, 5000);
    }

    // AJAX handlers
    async handleSearch(e) {
        const query = e.target.value.trim();
        if (query.length < 2) return;

        try {
            const response = await fetch(`/accounting/asset-register/ajax/search/?q=${encodeURIComponent(query)}`);
            const data = await response.json();
            this.updateSearchResults(data.results);
        } catch (error) {
            console.error('Search error:', error);
        }
    }

    updateSearchResults(results) {
        const resultsContainer = document.getElementById('search-results');
        if (!resultsContainer) return;

        resultsContainer.innerHTML = '';
        results.forEach(result => {
            const item = document.createElement('div');
            item.className = 'search-result-item';
            item.innerHTML = `
                <div class="search-result-code">${result.code}</div>
                <div class="search-result-name">${result.name}</div>
                <div class="search-result-location">${result.location}</div>
            `;
            item.addEventListener('click', () => {
                window.location.href = result.url;
            });
            resultsContainer.appendChild(item);
        });
    }

    async handleFilterSubmit(e) {
        e.preventDefault();
        const formData = new FormData(e.target);
        const params = new URLSearchParams(formData);
        window.location.href = `${window.location.pathname}?${params.toString()}`;
    }

    // Statistics update
    async updateStats() {
        try {
            const response = await fetch('/accounting/asset-register/ajax/stats/');
            const data = await response.json();
            this.updateStatsDisplay(data);
        } catch (error) {
            console.error('Stats update error:', error);
        }
    }

    updateStatsDisplay(stats) {
        const elements = {
            'total-assets': stats.total_assets,
            'active-assets': stats.active_assets,
            'disposed-assets': stats.disposed_assets,
            'under-repair': stats.under_repair,
            'total-value': stats.total_value,
            'total-book-value': stats.total_book_value
        };

        Object.entries(elements).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = this.formatNumber(value);
            }
        });
    }

    formatNumber(num) {
        return new Intl.NumberFormat('en-US', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }).format(num);
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new AssetRegister();
});

// Export for global access
window.AssetRegister = AssetRegister; 