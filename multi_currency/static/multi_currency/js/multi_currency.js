// Multi-Currency Management JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Currency status toggle functionality
    initializeCurrencyStatusToggle();
    
    // Exchange rate status toggle functionality
    initializeExchangeRateStatusToggle();
    
    // Form validation
    initializeFormValidation();
    
    // Search functionality
    initializeSearch();
    
    // Currency converter
    initializeCurrencyConverter();
});

// Currency status toggle
function initializeCurrencyStatusToggle() {
    const toggleButtons = document.querySelectorAll('.toggle-currency-status');
    
    toggleButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            
            const currencyId = this.dataset.currencyId;
            const button = this;
            
            // Show loading state
            button.disabled = true;
            button.innerHTML = '<i class="bi bi-hourglass-split"></i>';
            
            fetch(`/multi-currency/currencies/${currencyId}/toggle-status/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'Content-Type': 'application/json',
                },
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Update button appearance
                    if (data.is_active) {
                        button.classList.remove('btn-outline-secondary');
                        button.classList.add('btn-outline-success');
                        button.innerHTML = '<i class="bi bi-check-circle"></i> Active';
                    } else {
                        button.classList.remove('btn-outline-success');
                        button.classList.add('btn-outline-secondary');
                        button.innerHTML = '<i class="bi bi-x-circle"></i> Inactive';
                    }
                    
                    // Show success message
                    showNotification(data.message, 'success');
                } else {
                    showNotification(data.message, 'error');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showNotification('An error occurred while updating status', 'error');
            })
            .finally(() => {
                button.disabled = false;
            });
        });
    });
}

// Exchange rate status toggle
function initializeExchangeRateStatusToggle() {
    const toggleButtons = document.querySelectorAll('.toggle-exchange-rate-status');
    
    toggleButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            
            const rateId = this.dataset.rateId;
            const button = this;
            
            // Show loading state
            button.disabled = true;
            button.innerHTML = '<i class="bi bi-hourglass-split"></i>';
            
            fetch(`/multi-currency/exchange-rates/${rateId}/toggle-status/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'Content-Type': 'application/json',
                },
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Update button appearance
                    if (data.is_active) {
                        button.classList.remove('btn-outline-secondary');
                        button.classList.add('btn-outline-success');
                        button.innerHTML = '<i class="bi bi-check-circle"></i> Active';
                    } else {
                        button.classList.remove('btn-outline-success');
                        button.classList.add('btn-outline-secondary');
                        button.innerHTML = '<i class="bi bi-x-circle"></i> Inactive';
                    }
                    
                    // Show success message
                    showNotification(data.message, 'success');
                } else {
                    showNotification(data.message, 'error');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showNotification('An error occurred while updating status', 'error');
            })
            .finally(() => {
                button.disabled = false;
            });
        });
    });
}

// Form validation
function initializeFormValidation() {
    const forms = document.querySelectorAll('.needs-validation');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });
    
    // Currency code validation
    const currencyCodeInputs = document.querySelectorAll('input[name="code"]');
    currencyCodeInputs.forEach(input => {
        input.addEventListener('input', function() {
            this.value = this.value.toUpperCase();
            if (this.value.length > 3) {
                this.value = this.value.slice(0, 3);
            }
        });
    });
    
    // Exchange rate validation
    const rateInputs = document.querySelectorAll('input[name="rate"]');
    rateInputs.forEach(input => {
        input.addEventListener('input', function() {
            const value = parseFloat(this.value);
            if (value <= 0) {
                this.setCustomValidity('Rate must be greater than 0');
            } else {
                this.setCustomValidity('');
            }
        });
    });
}

// Search functionality
function initializeSearch() {
    const searchForms = document.querySelectorAll('.search-form');
    
    searchForms.forEach(form => {
        const searchInput = form.querySelector('input[type="text"]');
        const clearButton = form.querySelector('.clear-search');
        
        if (searchInput && clearButton) {
            // Clear search functionality
            clearButton.addEventListener('click', function(e) {
                e.preventDefault();
                searchInput.value = '';
                form.submit();
            });
            
            // Auto-submit on enter
            searchInput.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    form.submit();
                }
            });
        }
    });
}

// Currency converter
function initializeCurrencyConverter() {
    const converter = document.getElementById('currency-converter');
    if (!converter) return;
    
    const amountInput = converter.querySelector('#amount');
    const fromCurrencySelect = converter.querySelector('#from-currency');
    const toCurrencySelect = converter.querySelector('#to-currency');
    const resultDisplay = converter.querySelector('#conversion-result');
    const convertButton = converter.querySelector('#convert-btn');
    
    if (convertButton) {
        convertButton.addEventListener('click', function() {
            const amount = parseFloat(amountInput.value);
            const fromCurrency = fromCurrencySelect.value;
            const toCurrency = toCurrencySelect.value;
            
            if (!amount || !fromCurrency || !toCurrency) {
                showNotification('Please fill in all fields', 'warning');
                return;
            }
            
            if (fromCurrency === toCurrency) {
                resultDisplay.textContent = `${amount} ${fromCurrency}`;
                return;
            }
            
            // Show loading state
            convertButton.disabled = true;
            convertButton.innerHTML = '<i class="bi bi-hourglass-split"></i> Converting...';
            
            // Simulate API call (replace with actual API call)
            setTimeout(() => {
                // This would be replaced with actual exchange rate API call
                const mockRate = 1.5; // Mock rate
                const convertedAmount = amount * mockRate;
                
                resultDisplay.textContent = `${convertedAmount.toFixed(2)} ${toCurrency}`;
                
                convertButton.disabled = false;
                convertButton.innerHTML = '<i class="bi bi-arrow-left-right"></i> Convert';
            }, 1000);
        });
    }
}

// Utility functions
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show position-fixed`;
    notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // Add to page
    document.body.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 5000);
}

// Data table functionality
function initializeDataTable(tableId) {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    // Add sorting functionality
    const headers = table.querySelectorAll('th[data-sortable]');
    headers.forEach(header => {
        header.addEventListener('click', function() {
            const column = this.cellIndex;
            const tbody = table.querySelector('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));
            
            // Toggle sort direction
            const isAscending = !this.classList.contains('sort-desc');
            
            // Remove sort classes from all headers
            headers.forEach(h => h.classList.remove('sort-asc', 'sort-desc'));
            
            // Add sort class to current header
            this.classList.add(isAscending ? 'sort-asc' : 'sort-desc');
            
            // Sort rows
            rows.sort((a, b) => {
                const aValue = a.cells[column].textContent.trim();
                const bValue = b.cells[column].textContent.trim();
                
                if (isAscending) {
                    return aValue.localeCompare(bValue);
                } else {
                    return bValue.localeCompare(aValue);
                }
            });
            
            // Reorder rows
            rows.forEach(row => tbody.appendChild(row));
        });
    });
}

// Export functionality
function exportToCSV(tableId, filename) {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    const rows = table.querySelectorAll('tr');
    let csv = [];
    
    rows.forEach(row => {
        const cols = row.querySelectorAll('td, th');
        const rowData = [];
        cols.forEach(col => {
            rowData.push('"' + col.textContent.replace(/"/g, '""') + '"');
        });
        csv.push(rowData.join(','));
    });
    
    const csvContent = csv.join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    
    if (link.download !== undefined) {
        const url = URL.createObjectURL(blob);
        link.setAttribute('href', url);
        link.setAttribute('download', filename);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
}

// Initialize data tables when page loads
document.addEventListener('DOMContentLoaded', function() {
    initializeDataTable('currencies-table');
    initializeDataTable('exchange-rates-table');
}); 