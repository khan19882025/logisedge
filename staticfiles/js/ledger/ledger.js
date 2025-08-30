// Ledger App JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize delete functionality
    initializeDeleteButtons();
    
    // Initialize reconciliation functionality
    initializeReconciliationButtons();
    
    // Initialize search functionality
    initializeSearch();
    
    // Initialize form validation
    initializeFormValidation();
    
    // Initialize print functionality
    initializePrint();
});

// Delete Entry Functionality
function initializeDeleteButtons() {
    const deleteButtons = document.querySelectorAll('.delete-entry-btn');
    
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            
            const entryId = this.getAttribute('data-entry-id');
            const entryNumber = this.getAttribute('data-entry-number');
            
            // Show confirmation modal
            document.getElementById('entryNumberToDelete').textContent = entryNumber;
            const deleteModal = new bootstrap.Modal(document.getElementById('deleteEntryModal'));
            deleteModal.show();
            
            // Handle confirmation
            document.getElementById('confirmDeleteBtn').onclick = function() {
                deleteLedgerEntry(entryId);
                deleteModal.hide();
            };
        });
    });
}

function deleteLedgerEntry(entryId) {
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    
    fetch(`/ledger/${entryId}/delete/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken,
            'Content-Type': 'application/json',
        },
    })
    .then(response => {
        if (response.ok) {
            // Remove the row from the table
            const row = document.querySelector(`tr[data-entry-id="${entryId}"]`);
            if (row) {
                row.remove();
                showNotification('Ledger entry deleted successfully', 'success');
            }
        } else {
            showNotification('Error deleting ledger entry', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Error deleting ledger entry', 'error');
    });
}

// Reconciliation Functionality
function initializeReconciliationButtons() {
    const reconcileButtons = document.querySelectorAll('.reconcile-entry-btn');
    
    reconcileButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            
            const entryId = this.getAttribute('data-entry-id');
            
            // Set default reconciliation date to today
            const today = new Date().toISOString().split('T')[0];
            document.getElementById('reconciliation-date').value = today;
            
            // Show reconciliation modal
            const reconcileModal = new bootstrap.Modal(document.getElementById('reconcileEntryModal'));
            reconcileModal.show();
            
            // Handle form submission
            document.getElementById('reconcileForm').onsubmit = function(e) {
                e.preventDefault();
                reconcileLedgerEntry(entryId);
                reconcileModal.hide();
            };
        });
    });
}

function reconcileLedgerEntry(entryId) {
    const form = document.getElementById('reconcileForm');
    const formData = new FormData(form);
    
    fetch(`/ledger/${entryId}/reconcile/`, {
        method: 'POST',
        body: formData,
    })
    .then(response => {
        if (response.ok) {
            // Update the UI to show reconciled status
            const row = document.querySelector(`tr[data-entry-id="${entryId}"]`);
            if (row) {
                const reconciledCell = row.querySelector('td:nth-child(9)');
                reconciledCell.innerHTML = `
                    <span class="badge bg-success">
                        <i class="bi bi-check-circle"></i> Yes
                    </span>
                `;
                
                // Remove the reconcile button
                const reconcileBtn = row.querySelector('.reconcile-entry-btn');
                if (reconcileBtn) {
                    reconcileBtn.remove();
                }
                
                showNotification('Ledger entry reconciled successfully', 'success');
            }
        } else {
            showNotification('Error reconciling ledger entry', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Error reconciling ledger entry', 'error');
    });
}

// Search Functionality
function initializeSearch() {
    const searchInput = document.getElementById('search-term');
    const searchBySelect = document.getElementById('search-by');
    
    if (searchInput) {
        // Debounce search input
        let searchTimeout;
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                performSearch();
            }, 500);
        });
    }
    
    if (searchBySelect) {
        searchBySelect.addEventListener('change', function() {
            performSearch();
        });
    }
}

function performSearch() {
    const searchTerm = document.getElementById('search-term').value;
    const searchBy = document.getElementById('search-by').value;
    const accountId = document.getElementById('account').value;
    
    if (searchTerm.length > 2 || accountId) {
        fetch(`/ledger/ajax/search/?q=${encodeURIComponent(searchTerm)}&search_by=${searchBy}&account_id=${accountId}`)
            .then(response => response.json())
            .then(data => {
                updateSearchResults(data.results);
            })
            .catch(error => {
                console.error('Search error:', error);
            });
    }
}

function updateSearchResults(results) {
    // This function can be used to update search results dynamically
    // For now, we'll just log the results
    console.log('Search results:', results);
}

// Form Validation
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
    
    // Custom validation for amount fields
    const amountInputs = document.querySelectorAll('input[type="number"][step="0.01"]');
    amountInputs.forEach(input => {
        input.addEventListener('input', function() {
            const value = parseFloat(this.value);
            if (value <= 0) {
                this.setCustomValidity('Amount must be greater than zero');
            } else {
                this.setCustomValidity('');
            }
        });
    });
}

// Print Functionality
function initializePrint() {
    window.printLedger = function() {
        window.print();
    };
}

// Notification System
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show position-fixed`;
    notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Add to page
    document.body.appendChild(notification);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 5000);
}

// Table Sorting
function initializeTableSorting() {
    const tableHeaders = document.querySelectorAll('.ledger-table th[data-sortable]');
    
    tableHeaders.forEach(header => {
        header.addEventListener('click', function() {
            const column = this.getAttribute('data-column');
            const currentOrder = this.getAttribute('data-order') || 'asc';
            const newOrder = currentOrder === 'asc' ? 'desc' : 'asc';
            
            // Update all headers
            tableHeaders.forEach(h => h.setAttribute('data-order', ''));
            this.setAttribute('data-order', newOrder);
            
            // Sort table
            sortTable(column, newOrder);
        });
    });
}

function sortTable(column, order) {
    const table = document.querySelector('.ledger-table');
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    
    rows.sort((a, b) => {
        const aValue = a.querySelector(`td[data-${column}]`).getAttribute(`data-${column}`);
        const bValue = b.querySelector(`td[data-${column}]`).getAttribute(`data-${column}`);
        
        if (order === 'asc') {
            return aValue.localeCompare(bValue);
        } else {
            return bValue.localeCompare(aValue);
        }
    });
    
    // Reorder rows
    rows.forEach(row => tbody.appendChild(row));
}

// Export Functionality
function exportToCSV() {
    const table = document.querySelector('.ledger-table');
    const rows = table.querySelectorAll('tr');
    let csv = [];
    
    rows.forEach(row => {
        const cols = row.querySelectorAll('td, th');
        const rowData = [];
        cols.forEach(col => {
            rowData.push(`"${col.textContent.trim()}"`);
        });
        csv.push(rowData.join(','));
    });
    
    const csvContent = csv.join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `ledger_entries_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
}

// Filter Management
function initializeFilters() {
    const filterInputs = document.querySelectorAll('input[name], select[name]');
    
    filterInputs.forEach(input => {
        input.addEventListener('change', function() {
            updateFilterChips();
        });
    });
}

function updateFilterChips() {
    const filterContainer = document.getElementById('filter-chips');
    if (!filterContainer) return;
    
    filterContainer.innerHTML = '';
    
    const form = document.querySelector('form[method="get"]');
    const formData = new FormData(form);
    
    formData.forEach((value, key) => {
        if (value && key !== 'page') {
            const chip = document.createElement('span');
            chip.className = 'filter-chip';
            chip.innerHTML = `
                ${key}: ${value}
                <span class="remove-filter" onclick="removeFilter(${JSON.stringify(key)})">&times;</span>
            `;
            filterContainer.appendChild(chip);
        }
    });
}

function removeFilter(key) {
    const input = document.querySelector(`[name="${key}"]`);
    if (input) {
        input.value = '';
        input.dispatchEvent(new Event('change'));
    }
}

// Keyboard Shortcuts
function initializeKeyboardShortcuts() {
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + N for new entry
        if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
            e.preventDefault();
            window.location.href = '/ledger/create/';
        }
        
        // Ctrl/Cmd + F for search
        if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
            e.preventDefault();
            document.getElementById('search-term').focus();
        }
        
        // Ctrl/Cmd + P for print
        if ((e.ctrlKey || e.metaKey) && e.key === 'p') {
            e.preventDefault();
            window.printLedger();
        }
    });
}

// Auto-save functionality for forms
function initializeAutoSave() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        const inputs = form.querySelectorAll('input, select, textarea');
        
        inputs.forEach(input => {
            input.addEventListener('input', function() {
                saveFormData(form);
            });
        });
    });
}

function saveFormData(form) {
    const formData = new FormData(form);
    const data = {};
    
    formData.forEach((value, key) => {
        data[key] = value;
    });
    
    localStorage.setItem(`ledger_form_${form.id || 'default'}`, JSON.stringify(data));
}

function loadFormData(form) {
    const saved = localStorage.getItem(`ledger_form_${form.id || 'default'}`);
    if (saved) {
        const data = JSON.parse(saved);
        
        Object.keys(data).forEach(key => {
            const input = form.querySelector(`[name="${key}"]`);
            if (input && !input.value) {
                input.value = data[key];
            }
        });
    }
}

// Initialize all functionality when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeTableSorting();
    initializeFilters();
    initializeKeyboardShortcuts();
    initializeAutoSave();
    
    // Load saved form data
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        loadFormData(form);
    });
});