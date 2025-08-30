/**
 * Dispose Asset Module JavaScript
 * Handles all interactive functionality for the disposal asset system
 */

class DisposeAssetManager {
    constructor() {
        this.initializeEventListeners();
        this.initializeComponents();
    }

    initializeEventListeners() {
        // Asset selection
        document.addEventListener('change', (e) => {
            if (e.target.classList.contains('asset-checkbox')) {
                this.handleAssetSelection(e.target);
            }
        });

        // Form validation
        document.addEventListener('submit', (e) => {
            if (e.target.classList.contains('disposal-form')) {
                this.validateForm(e);
            }
        });

        // Search functionality
        const searchInput = document.querySelector('#asset-search');
        if (searchInput) {
            searchInput.addEventListener('input', this.debounce(this.handleSearch.bind(this), 300));
        }

        // Filter functionality
        document.querySelectorAll('.filter-control').forEach(control => {
            control.addEventListener('change', this.handleFilter.bind(this));
        });

        // Document upload
        this.initializeDocumentUpload();

        // Approval actions
        document.querySelectorAll('.approval-action').forEach(button => {
            button.addEventListener('click', this.handleApproval.bind(this));
        });

        // Bulk actions
        document.querySelectorAll('.bulk-action').forEach(button => {
            button.addEventListener('click', this.handleBulkAction.bind(this));
        });

        // QR/Barcode scanning
        this.initializeScanner();
    }

    initializeComponents() {
        // Initialize tooltips
        this.initializeTooltips();

        // Initialize date pickers
        this.initializeDatePickers();

        // Initialize select2 for better dropdowns
        this.initializeSelect2();

        // Initialize progress bars
        this.initializeProgressBars();
    }

    // Asset Selection Methods
    handleAssetSelection(checkbox) {
        const assetCard = checkbox.closest('.asset-card');
        const isSelected = checkbox.checked;

        if (isSelected) {
            assetCard.classList.add('selected');
            this.updateSelectedAssetsCount();
        } else {
            assetCard.classList.remove('selected');
            this.updateSelectedAssetsCount();
        }

        // Update disposal value calculation
        this.updateDisposalValue();
    }

    updateSelectedAssetsCount() {
        const selectedAssets = document.querySelectorAll('.asset-checkbox:checked');
        const countElement = document.querySelector('#selected-count');
        
        if (countElement) {
            countElement.textContent = selectedAssets.length;
        }

        // Enable/disable bulk action buttons
        const bulkButtons = document.querySelectorAll('.bulk-action');
        bulkButtons.forEach(button => {
            button.disabled = selectedAssets.length === 0;
        });
    }

    updateDisposalValue() {
        const selectedAssets = document.querySelectorAll('.asset-checkbox:checked');
        let totalValue = 0;

        selectedAssets.forEach(checkbox => {
            const assetCard = checkbox.closest('.asset-card');
            const valueElement = assetCard.querySelector('.asset-value');
            if (valueElement) {
                const value = parseFloat(valueElement.dataset.value || 0);
                totalValue += value;
            }
        });

        const disposalValueInput = document.querySelector('#id_disposal_value');
        if (disposalValueInput) {
            disposalValueInput.value = totalValue.toFixed(2);
        }

        // Update financial summary
        this.updateFinancialSummary();
    }

    updateFinancialSummary() {
        const totalAssetValue = this.calculateTotalAssetValue();
        const disposalValue = parseFloat(document.querySelector('#id_disposal_value')?.value || 0);
        const gainLoss = disposalValue - totalAssetValue;

        // Update display
        const gainLossElement = document.querySelector('#gain-loss-amount');
        if (gainLossElement) {
            gainLossElement.textContent = `AED ${gainLoss.toFixed(2)}`;
            gainLossElement.className = gainLoss >= 0 ? 'financial-value gain' : 'financial-value loss';
        }
    }

    calculateTotalAssetValue() {
        const selectedAssets = document.querySelectorAll('.asset-checkbox:checked');
        let totalValue = 0;

        selectedAssets.forEach(checkbox => {
            const assetCard = checkbox.closest('.asset-card');
            const valueElement = assetCard.querySelector('.asset-value');
            if (valueElement) {
                const value = parseFloat(valueElement.dataset.value || 0);
                totalValue += value;
            }
        });

        return totalValue;
    }

    // Search and Filter Methods
    handleSearch(event) {
        const searchTerm = event.target.value.toLowerCase();
        const assetCards = document.querySelectorAll('.asset-card');

        assetCards.forEach(card => {
            const assetName = card.querySelector('.asset-name').textContent.toLowerCase();
            const assetCode = card.querySelector('.asset-code')?.textContent.toLowerCase() || '';
            const serialNumber = card.querySelector('.asset-serial')?.textContent.toLowerCase() || '';

            const matches = assetName.includes(searchTerm) || 
                           assetCode.includes(searchTerm) || 
                           serialNumber.includes(searchTerm);

            card.style.display = matches ? 'block' : 'none';
        });
    }

    handleFilter(event) {
        const filterType = event.target.dataset.filter;
        const filterValue = event.target.value;
        const assetCards = document.querySelectorAll('.asset-card');

        assetCards.forEach(card => {
            let show = true;

            // Apply filters
            if (filterType === 'category') {
                const category = card.dataset.category;
                show = show && (filterValue === '' || category === filterValue);
            } else if (filterType === 'location') {
                const location = card.dataset.location;
                show = show && (filterValue === '' || location === filterValue);
            } else if (filterType === 'status') {
                const status = card.dataset.status;
                show = show && (filterValue === '' || status === filterValue);
            }

            card.style.display = show ? 'block' : 'none';
        });
    }

    // Form Validation Methods
    validateForm(event) {
        const form = event.target;
        let isValid = true;

        // Clear previous errors
        form.querySelectorAll('.error-message').forEach(error => error.remove());
        form.querySelectorAll('.is-invalid').forEach(field => field.classList.remove('is-invalid'));

        // Required field validation
        form.querySelectorAll('[required]').forEach(field => {
            if (!field.value.trim()) {
                this.showFieldError(field, 'This field is required.');
                isValid = false;
            }
        });

        // Date validation
        const disposalDate = form.querySelector('#id_disposal_date');
        if (disposalDate && disposalDate.value) {
            const selectedDate = new Date(disposalDate.value);
            const today = new Date();
            today.setHours(0, 0, 0, 0);

            if (selectedDate > today) {
                this.showFieldError(disposalDate, 'Disposal date cannot be in the future.');
                isValid = false;
            }
        }

        // Value validation
        const disposalValue = form.querySelector('#id_disposal_value');
        if (disposalValue && disposalValue.value) {
            const value = parseFloat(disposalValue.value);
            if (value < 0) {
                this.showFieldError(disposalValue, 'Disposal value cannot be negative.');
                isValid = false;
            }
        }

        // Asset selection validation
        const selectedAssets = form.querySelectorAll('.asset-checkbox:checked');
        if (selectedAssets.length === 0) {
            this.showFormError(form, 'Please select at least one asset for disposal.');
            isValid = false;
        }

        if (!isValid) {
            event.preventDefault();
            this.showNotification('Please correct the errors in the form.', 'error');
        }

        return isValid;
    }

    showFieldError(field, message) {
        field.classList.add('is-invalid');
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message text-danger mt-1';
        errorDiv.textContent = message;
        field.parentNode.appendChild(errorDiv);
    }

    showFormError(form, message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'alert alert-danger error-message';
        errorDiv.textContent = message;
        form.insertBefore(errorDiv, form.firstChild);
    }

    // Document Upload Methods
    initializeDocumentUpload() {
        const uploadArea = document.querySelector('.document-upload');
        if (!uploadArea) return;

        const fileInput = uploadArea.querySelector('input[type="file"]');

        // Drag and drop functionality
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });

        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('dragover');
        });

        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                fileInput.files = files;
                this.handleFileUpload(files);
            }
        });

        // File input change
        fileInput.addEventListener('change', (e) => {
            this.handleFileUpload(e.target.files);
        });
    }

    handleFileUpload(files) {
        const fileList = document.querySelector('.file-list');
        if (!fileList) return;

        Array.from(files).forEach(file => {
            // Validate file type and size
            if (!this.validateFile(file)) return;

            // Create file item
            const fileItem = this.createFileItem(file);
            fileList.appendChild(fileItem);
        });
    }

    validateFile(file) {
        const allowedTypes = ['application/pdf', 'image/jpeg', 'image/png', 'application/msword', 
                             'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
        const maxSize = 10 * 1024 * 1024; // 10MB

        if (!allowedTypes.includes(file.type)) {
            this.showNotification('Invalid file type. Please upload PDF, Word, or image files.', 'error');
            return false;
        }

        if (file.size > maxSize) {
            this.showNotification('File size must be less than 10MB.', 'error');
            return false;
        }

        return true;
    }

    createFileItem(file) {
        const fileItem = document.createElement('div');
        fileItem.className = 'file-item d-flex align-items-center p-2 border rounded mb-2';
        
        const fileIcon = document.createElement('i');
        fileIcon.className = 'fas fa-file me-2';
        
        const fileName = document.createElement('span');
        fileName.className = 'flex-grow-1';
        fileName.textContent = file.name;
        
        const removeBtn = document.createElement('button');
        removeBtn.className = 'btn btn-sm btn-outline-danger ms-2';
        removeBtn.innerHTML = '<i class="fas fa-times"></i>';
        removeBtn.onclick = () => fileItem.remove();
        
        fileItem.appendChild(fileIcon);
        fileItem.appendChild(fileName);
        fileItem.appendChild(removeBtn);
        
        return fileItem;
    }

    // Approval Methods
    handleApproval(event) {
        const button = event.target.closest('.approval-action');
        const action = button.dataset.action;
        const disposalId = button.dataset.disposalId;

        if (action === 'approve' || action === 'reject') {
            this.showApprovalModal(action, disposalId);
        }
    }

    showApprovalModal(action, disposalId) {
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.innerHTML = `
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">${action.charAt(0).toUpperCase() + action.slice(1)} Disposal Request</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <form id="approval-form">
                            <div class="form-group">
                                <label for="approval-comments">Comments</label>
                                <textarea id="approval-comments" class="form-control" rows="3" placeholder="Enter your comments..."></textarea>
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        <button type="button" class="btn btn-${action === 'approve' ? 'success' : 'danger'}" onclick="disposeAssetManager.submitApproval(${JSON.stringify(action)}, ${disposalId})">
                            ${action.charAt(0).toUpperCase() + action.slice(1)}
                        </button>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);
        const modalInstance = new bootstrap.Modal(modal);
        modalInstance.show();

        modal.addEventListener('hidden.bs.modal', () => {
            modal.remove();
        });
    }

    async submitApproval(action, disposalId) {
        const comments = document.querySelector('#approval-comments').value;
        
        try {
            const response = await fetch(`/accounting/dispose-asset/${disposalId}/approve/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    action: action,
                    comments: comments
                })
            });

            if (response.ok) {
                this.showNotification(`Disposal request ${action}d successfully.`, 'success');
                setTimeout(() => window.location.reload(), 1500);
            } else {
                const error = await response.json();
                this.showNotification(error.message || 'An error occurred.', 'error');
            }
        } catch (error) {
            this.showNotification('An error occurred while processing the approval.', 'error');
        }
    }

    // Bulk Action Methods
    handleBulkAction(event) {
        const button = event.target.closest('.bulk-action');
        const action = button.dataset.action;
        const selectedAssets = document.querySelectorAll('.asset-checkbox:checked');

        if (selectedAssets.length === 0) {
            this.showNotification('Please select assets for bulk action.', 'warning');
            return;
        }

        if (action === 'dispose') {
            this.showBulkDisposalModal(selectedAssets);
        }
    }

    showBulkDisposalModal(selectedAssets) {
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.innerHTML = `
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Bulk Disposal</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <p>You are about to dispose of ${selectedAssets.length} assets.</p>
                        <form id="bulk-disposal-form">
                            <div class="form-row">
                                <div class="form-group">
                                    <label for="bulk-disposal-type">Disposal Type</label>
                                    <select id="bulk-disposal-type" class="form-control" required>
                                        <option value="">Select disposal type</option>
                                        <option value="sold">Sold</option>
                                        <option value="scrapped">Scrapped</option>
                                        <option value="donated">Donated</option>
                                        <option value="lost">Lost</option>
                                    </select>
                                </div>
                                <div class="form-group">
                                    <label for="bulk-disposal-date">Disposal Date</label>
                                    <input type="date" id="bulk-disposal-date" class="form-control" required>
                                </div>
                            </div>
                            <div class="form-group">
                                <label for="bulk-disposal-reason">Reason</label>
                                <textarea id="bulk-disposal-reason" class="form-control" rows="3" required></textarea>
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        <button type="button" class="btn btn-primary" onclick="disposeAssetManager.submitBulkDisposal()">
                            Create Disposal Request
                        </button>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);
        const modalInstance = new bootstrap.Modal(modal);
        modalInstance.show();

        // Set default date
        document.querySelector('#bulk-disposal-date').value = new Date().toISOString().split('T')[0];

        modal.addEventListener('hidden.bs.modal', () => {
            modal.remove();
        });
    }

    async submitBulkDisposal() {
        const form = document.querySelector('#bulk-disposal-form');
        const formData = new FormData(form);
        
        const selectedAssets = Array.from(document.querySelectorAll('.asset-checkbox:checked'))
            .map(checkbox => checkbox.value);

        try {
            const response = await fetch('/accounting/dispose-asset/bulk-disposal/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    assets: selectedAssets,
                    disposal_type: formData.get('bulk-disposal-type'),
                    disposal_date: formData.get('bulk-disposal-date'),
                    reason: formData.get('bulk-disposal-reason')
                })
            });

            if (response.ok) {
                this.showNotification('Bulk disposal request created successfully.', 'success');
                setTimeout(() => window.location.reload(), 1500);
            } else {
                const error = await response.json();
                this.showNotification(error.message || 'An error occurred.', 'error');
            }
        } catch (error) {
            this.showNotification('An error occurred while creating the bulk disposal request.', 'error');
        }
    }

    // QR/Barcode Scanner Methods
    initializeScanner() {
        const scanButton = document.querySelector('#scan-asset');
        if (!scanButton) return;

        scanButton.addEventListener('click', () => {
            this.showScannerModal();
        });
    }

    showScannerModal() {
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.innerHTML = `
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Scan Asset QR/Barcode</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div id="scanner-container" class="text-center">
                            <div class="scanner-placeholder">
                                <i class="fas fa-qrcode fa-3x text-muted mb-3"></i>
                                <p>Scanner will be initialized here</p>
                                <button class="btn btn-primary" onclick="disposeAssetManager.initializeScanner()">
                                    Start Scanner
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);
        const modalInstance = new bootstrap.Modal(modal);
        modalInstance.show();

        modal.addEventListener('hidden.bs.modal', () => {
            modal.remove();
        });
    }

    // Utility Methods
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
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || 
               document.cookie.split('; ').find(row => row.startsWith('csrftoken='))?.split('=')[1];
    }

    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;

        document.body.appendChild(notification);

        setTimeout(() => {
            notification.remove();
        }, 5000);
    }

    initializeTooltips() {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }

    initializeDatePickers() {
        document.querySelectorAll('input[type="date"]').forEach(input => {
            if (!input.value) {
                input.value = new Date().toISOString().split('T')[0];
            }
        });
    }

    initializeSelect2() {
        // Initialize select2 for better dropdowns if available
        if (typeof $.fn.select2 !== 'undefined') {
            $('.select2').select2({
                theme: 'bootstrap-5',
                width: '100%'
            });
        }
    }

    initializeProgressBars() {
        document.querySelectorAll('.progress-bar').forEach(bar => {
            const progress = bar.dataset.progress;
            if (progress) {
                bar.style.width = `${progress}%`;
            }
        });
    }
}

// Initialize the manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.disposeAssetManager = new DisposeAssetManager();
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DisposeAssetManager;
}