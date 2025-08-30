/**
 * Receipt Voucher System JavaScript
 * Handles autocomplete, form validation, and interactive features
 */

class ReceiptVoucherSystem {
    constructor() {
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupAutocomplete();
        this.setupFormValidation();
        this.setupAmountFormatting();
        this.setupDatePickers();
        this.setupFileUpload();
        this.setupSearchFilters();
    }

    setupEventListeners() {
        // Payer type change handler
        const payerTypeSelect = document.getElementById('id_payer_type');
        if (payerTypeSelect) {
            payerTypeSelect.addEventListener('change', (e) => {
                this.handlePayerTypeChange(e.target.value);
            });
        }

        // Currency change handler
        const currencySelect = document.getElementById('id_currency');
        if (currencySelect) {
            currencySelect.addEventListener('change', (e) => {
                this.updateAmountField(e.target.value);
            });
        }

        // Form submission
        const form = document.querySelector('.receipt-voucher-form form');
        if (form) {
            form.addEventListener('submit', (e) => {
                this.handleFormSubmission(e);
            });
        }

        // Print button
        const printBtn = document.querySelector('.print-btn');
        if (printBtn) {
            printBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.printVoucher();
            });
        }

        // Delete confirmation
        const deleteBtns = document.querySelectorAll('.delete-btn');
        deleteBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                if (!confirm('Are you sure you want to delete this receipt voucher?')) {
                    e.preventDefault();
                }
            });
        });
    }

    setupAutocomplete() {
        // Payer name autocomplete
        const payerNameField = document.getElementById('id_payer_name');
        if (payerNameField) {
            this.setupPayerAutocomplete(payerNameField);
        }

        // Account autocomplete
        const accountField = document.getElementById('id_account_to_credit');
        if (accountField) {
            this.setupAccountAutocomplete(accountField);
        }
    }

    setupPayerAutocomplete(field) {
        let dropdown = null;
        let selectedIndex = -1;

        field.addEventListener('input', (e) => {
            const query = e.target.value;
            const payerType = document.getElementById('id_payer_type')?.value || 'customer';

            if (query.length < 2) {
                this.hideDropdown();
                return;
            }

            this.searchPayers(query, payerType, (results) => {
                this.showPayerDropdown(field, results);
            });
        });

        field.addEventListener('keydown', (e) => {
            if (!dropdown) return;

            switch (e.key) {
                case 'ArrowDown':
                    e.preventDefault();
                    this.selectDropdownItem(1);
                    break;
                case 'ArrowUp':
                    e.preventDefault();
                    this.selectDropdownItem(-1);
                    break;
                case 'Enter':
                    e.preventDefault();
                    this.selectCurrentItem();
                    break;
                case 'Escape':
                    this.hideDropdown();
                    break;
            }
        });

        // Hide dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (!field.contains(e.target) && (!dropdown || !dropdown.contains(e.target))) {
                this.hideDropdown();
            }
        });
    }

    setupAccountAutocomplete(field) {
        let dropdown = null;

        field.addEventListener('input', (e) => {
            const query = e.target.value;

            if (query.length < 2) {
                this.hideDropdown();
                return;
            }

            this.searchAccounts(query, (results) => {
                this.showAccountDropdown(field, results);
            });
        });

        // Hide dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (!field.contains(e.target) && (!dropdown || !dropdown.contains(e.target))) {
                this.hideDropdown();
            }
        });
    }

    searchPayers(query, payerType, callback) {
        const url = `/accounting/receipt-vouchers/ajax/payer-search/?q=${encodeURIComponent(query)}&payer_type=${payerType}`;
        
        fetch(url)
            .then(response => response.json())
            .then(data => {
                callback(data.results || []);
            })
            .catch(error => {
                console.error('Error searching payers:', error);
                callback([]);
            });
    }

    searchAccounts(query, callback) {
        const url = `/accounting/receipt-vouchers/ajax/account-search/?q=${encodeURIComponent(query)}`;
        
        fetch(url)
            .then(response => response.json())
            .then(data => {
                callback(data.results || []);
            })
            .catch(error => {
                console.error('Error searching accounts:', error);
                callback([]);
            });
    }

    showPayerDropdown(field, results) {
        this.hideDropdown();
        
        if (results.length === 0) return;

        const dropdown = document.createElement('div');
        dropdown.className = 'autocomplete-dropdown';
        
        results.forEach((result, index) => {
            const item = document.createElement('div');
            item.className = 'autocomplete-item';
            item.textContent = result.text;
            item.dataset.index = index;
            item.dataset.result = JSON.stringify(result);
            
            item.addEventListener('click', () => {
                this.selectPayer(result);
                this.hideDropdown();
            });
            
            dropdown.appendChild(item);
        });

        field.parentNode.style.position = 'relative';
        field.parentNode.appendChild(dropdown);
    }

    showAccountDropdown(field, results) {
        this.hideDropdown();
        
        if (results.length === 0) return;

        const dropdown = document.createElement('div');
        dropdown.className = 'autocomplete-dropdown';
        
        results.forEach((result, index) => {
            const item = document.createElement('div');
            item.className = 'autocomplete-item';
            item.textContent = result.text;
            item.dataset.index = index;
            item.dataset.result = JSON.stringify(result);
            
            item.addEventListener('click', () => {
                this.selectAccount(result);
                this.hideDropdown();
            });
            
            dropdown.appendChild(item);
        });

        field.parentNode.style.position = 'relative';
        field.parentNode.appendChild(dropdown);
    }

    selectPayer(result) {
        const payerNameField = document.getElementById('id_payer_name');
        const payerCodeField = document.getElementById('id_payer_code');
        const payerContactField = document.getElementById('id_payer_contact');
        const payerEmailField = document.getElementById('id_payer_email');

        if (payerNameField) payerNameField.value = result.name;
        if (payerCodeField) payerCodeField.value = result.code || '';
        if (payerContactField) payerContactField.value = result.contact || '';
        if (payerEmailField) payerEmailField.value = result.email || '';
    }

    selectAccount(result) {
        const accountField = document.getElementById('id_account_to_credit');
        if (accountField) {
            accountField.value = result.id;
            // Trigger change event to update any dependent fields
            accountField.dispatchEvent(new Event('change'));
        }
    }

    hideDropdown() {
        const dropdowns = document.querySelectorAll('.autocomplete-dropdown');
        dropdowns.forEach(dropdown => dropdown.remove());
    }

    selectDropdownItem(direction) {
        const items = document.querySelectorAll('.autocomplete-item');
        const selected = document.querySelector('.autocomplete-item.selected');
        
        if (selected) {
            selected.classList.remove('selected');
        }
        
        let newIndex = 0;
        if (selected) {
            const currentIndex = parseInt(selected.dataset.index);
            newIndex = Math.max(0, Math.min(items.length - 1, currentIndex + direction));
        }
        
        if (items[newIndex]) {
            items[newIndex].classList.add('selected');
        }
    }

    selectCurrentItem() {
        const selected = document.querySelector('.autocomplete-item.selected');
        if (selected) {
            selected.click();
        }
    }

    handlePayerTypeChange(payerType) {
        // Clear payer fields when type changes
        const payerNameField = document.getElementById('id_payer_name');
        const payerCodeField = document.getElementById('id_payer_code');
        const payerContactField = document.getElementById('id_payer_contact');
        const payerEmailField = document.getElementById('id_payer_email');

        if (payerNameField) payerNameField.value = '';
        if (payerCodeField) payerCodeField.value = '';
        if (payerContactField) payerContactField.value = '';
        if (payerEmailField) payerEmailField.value = '';

        // Update placeholder text
        if (payerNameField) {
            switch (payerType) {
                case 'customer':
                    payerNameField.placeholder = 'Enter customer name';
                    break;
                case 'employee':
                    payerNameField.placeholder = 'Enter employee name';
                    break;
                case 'vendor':
                    payerNameField.placeholder = 'Enter vendor name';
                    break;
                case 'other':
                    payerNameField.placeholder = 'Enter payer name';
                    break;
            }
        }
    }

    setupFormValidation() {
        const form = document.querySelector('.receipt-voucher-form form');
        if (!form) return;

        const fields = form.querySelectorAll('input, select, textarea');
        fields.forEach(field => {
            field.addEventListener('blur', () => {
                this.validateField(field);
            });
            
            field.addEventListener('input', () => {
                this.clearFieldError(field);
            });
        });
    }

    validateField(field) {
        const value = field.value.trim();
        const fieldName = field.name;
        let isValid = true;
        let errorMessage = '';

        // Required field validation
        if (field.hasAttribute('required') && !value) {
            isValid = false;
            errorMessage = 'This field is required.';
        }

        // Amount validation
        if (fieldName === 'amount') {
            const amount = parseFloat(value);
            if (isNaN(amount) || amount <= 0) {
                isValid = false;
                errorMessage = 'Please enter a valid amount greater than zero.';
            }
        }

        // Email validation
        if (fieldName === 'payer_email' && value) {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(value)) {
                isValid = false;
                errorMessage = 'Please enter a valid email address.';
            }
        }

        // Date validation
        if (fieldName === 'voucher_date') {
            const selectedDate = new Date(value);
            const today = new Date();
            if (selectedDate > today) {
                isValid = false;
                errorMessage = 'Voucher date cannot be in the future.';
            }
        }

        if (!isValid) {
            this.showFieldError(field, errorMessage);
        } else {
            this.clearFieldError(field);
        }

        return isValid;
    }

    showFieldError(field, message) {
        this.clearFieldError(field);
        
        field.classList.add('is-invalid');
        
        const errorDiv = document.createElement('div');
        errorDiv.className = 'invalid-feedback';
        errorDiv.textContent = message;
        
        field.parentNode.appendChild(errorDiv);
    }

    clearFieldError(field) {
        field.classList.remove('is-invalid');
        
        const errorDiv = field.parentNode.querySelector('.invalid-feedback');
        if (errorDiv) {
            errorDiv.remove();
        }
    }

    setupAmountFormatting() {
        const amountField = document.getElementById('id_amount');
        if (!amountField) return;

        amountField.addEventListener('input', (e) => {
            let value = e.target.value.replace(/[^\d.]/g, '');
            
            // Ensure only one decimal point
            const parts = value.split('.');
            if (parts.length > 2) {
                value = parts[0] + '.' + parts.slice(1).join('');
            }
            
            // Limit to 2 decimal places
            if (parts.length === 2 && parts[1].length > 2) {
                value = parts[0] + '.' + parts[1].substring(0, 2);
            }
            
            e.target.value = value;
        });

        amountField.addEventListener('blur', (e) => {
            const value = parseFloat(e.target.value);
            if (!isNaN(value)) {
                e.target.value = value.toFixed(2);
            }
        });
    }

    updateAmountField(currencyCode) {
        const amountField = document.getElementById('id_amount');
        if (amountField) {
            amountField.setAttribute('data-currency', currencyCode);
        }
    }

    setupDatePickers() {
        const dateFields = document.querySelectorAll('input[type="date"]');
        dateFields.forEach(field => {
            // Set max date to today
            const today = new Date().toISOString().split('T')[0];
            field.setAttribute('max', today);
            
            // Set default value to today if empty
            if (!field.value) {
                field.value = today;
            }
        });
    }

    setupFileUpload() {
        const fileInput = document.querySelector('input[type="file"]');
        if (!fileInput) return;

        fileInput.addEventListener('change', (e) => {
            const files = Array.from(e.target.files);
            this.validateFiles(files);
        });
    }

    validateFiles(files) {
        const maxSize = 10 * 1024 * 1024; // 10MB
        const allowedTypes = [
            'application/pdf',
            'image/jpeg',
            'image/jpg',
            'image/png',
            'image/gif',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/vnd.ms-excel',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        ];

        files.forEach(file => {
            if (file.size > maxSize) {
                alert(`File "${file.name}" is too large. Maximum size is 10MB.`);
                return;
            }

            if (!allowedTypes.includes(file.type)) {
                alert(`File "${file.name}" is not a supported file type.`);
                return;
            }
        });
    }

    setupSearchFilters() {
        const searchForm = document.querySelector('.search-filter-section form');
        if (!searchForm) return;

        // Auto-submit on filter change
        const filterFields = searchForm.querySelectorAll('select, input[type="date"]');
        filterFields.forEach(field => {
            field.addEventListener('change', () => {
                searchForm.submit();
            });
        });

        // Clear filters button
        const clearBtn = document.querySelector('.clear-filters-btn');
        if (clearBtn) {
            clearBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.clearFilters();
            });
        }
    }

    clearFilters() {
        const searchForm = document.querySelector('.search-filter-section form');
        if (!searchForm) return;

        const fields = searchForm.querySelectorAll('input, select');
        fields.forEach(field => {
            if (field.type === 'text' || field.type === 'date') {
                field.value = '';
            } else if (field.tagName === 'SELECT') {
                field.selectedIndex = 0;
            }
        });

        searchForm.submit();
    }

    handleFormSubmission(e) {
        const form = e.target;
        const fields = form.querySelectorAll('input, select, textarea');
        let isValid = true;

        // Validate all fields
        fields.forEach(field => {
            if (!this.validateField(field)) {
                isValid = false;
            }
        });

        if (!isValid) {
            e.preventDefault();
            this.showAlert('Please correct the errors in the form.', 'error');
            return;
        }

        // Show loading state
        const submitBtn = form.querySelector('button[type="submit"]');
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.textContent = 'Saving...';
        }
    }

    printVoucher() {
        window.print();
    }

    showAlert(message, type = 'info') {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type}`;
        alertDiv.textContent = message;

        const container = document.querySelector('.receipt-voucher-container');
        if (container) {
            container.insertBefore(alertDiv, container.firstChild);
            
            // Auto-remove after 5 seconds
            setTimeout(() => {
                alertDiv.remove();
            }, 5000);
        }
    }

    // Utility methods
    formatCurrency(amount, currency = 'AED') {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: currency
        }).format(amount);
    }

    formatDate(date) {
        return new Intl.DateTimeFormat('en-US', {
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

// Initialize the system when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new ReceiptVoucherSystem();
});

// Export for use in other scripts
window.ReceiptVoucherSystem = ReceiptVoucherSystem; 