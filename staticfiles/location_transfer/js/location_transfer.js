/**
 * Location Transfer Application JavaScript
 * Handles dynamic functionality for location transfers
 */

document.addEventListener('DOMContentLoaded', function() {
    initializeLocationTransferApp();
});

function initializeLocationTransferApp() {
    // Initialize tooltips
    initializeTooltips();
    
    // Initialize confirmations
    initializeConfirmations();
    
    // Initialize form validation
    initializeFormValidation();
    
    // Initialize dynamic fields
    initializeDynamicFields();
    
    // Initialize search functionality
    initializeSearchFunctionality();
    
    // Initialize notifications
    initializeNotifications();
}

/**
 * Initialize Bootstrap tooltips
 */
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Initialize confirmation dialogs
 */
function initializeConfirmations() {
    document.addEventListener('click', function(e) {
        if (e.target.matches('[data-confirm]')) {
            const message = e.target.getAttribute('data-confirm');
            if (!confirm(message)) {
                e.preventDefault();
                e.stopPropagation();
            }
        }
    });
}

/**
 * Initialize form validation
 */
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
}

/**
 * Initialize dynamic form fields
 */
function initializeDynamicFields() {
    // Handle pallet selection
    const palletSelect = document.getElementById('pallet-select');
    if (palletSelect) {
        palletSelect.addEventListener('change', function() {
            updateSourceLocation(this.value);
        });
    }
    
    // Handle destination location change
    const destinationSelect = document.getElementById('destination-location-select');
    if (destinationSelect) {
        destinationSelect.addEventListener('change', function() {
            validateLocationSelection();
        });
    }
}

/**
 * Initialize search functionality
 */
function initializeSearchFunctionality() {
    // Pallet search
    const palletSearchInput = document.querySelector('input[name="pallet_id"]');
    if (palletSearchInput) {
        palletSearchInput.addEventListener('input', debounce(function() {
            const query = this.value.trim();
            if (query.length >= 2) {
                searchPallets(query);
            }
        }, 300));
    }
    
    // Transfer search
    const transferSearchInput = document.querySelector('input[name="transfer_number"]');
    if (transferSearchInput) {
        transferSearchInput.addEventListener('input', debounce(function() {
            const query = this.value.trim();
            if (query.length >= 2) {
                searchTransfers(query);
            }
        }, 300));
    }
}

/**
 * Initialize notification system
 */
function initializeNotifications() {
    // Create notification container if it doesn't exist
    if (!document.getElementById('notification-container')) {
        const container = document.createElement('div');
        container.id = 'notification-container';
        container.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
            max-width: 400px;
        `;
        document.body.appendChild(container);
    }
}

/**
 * Update source location based on pallet selection
 */
function updateSourceLocation(palletId) {
    if (!palletId) return;
    
    fetch('{% url "location_transfer:get_pallet_details" %}', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify({ pallet_id: palletId })
    })
    .then(response => response.json())
    .then(data => {
        if (data.current_location) {
            const sourceLocationSelect = document.getElementById('source-location-select');
            if (sourceLocationSelect) {
                sourceLocationSelect.value = data.current_location.id;
                sourceLocationSelect.disabled = true;
            }
        }
    })
    .catch(error => {
        console.error('Error updating source location:', error);
    });
}

/**
 * Validate location selection
 */
function validateLocationSelection() {
    const sourceSelect = document.getElementById('source-location-select');
    const destinationSelect = document.getElementById('destination-location-select');
    
    if (sourceSelect && destinationSelect) {
        if (sourceSelect.value === destinationSelect.value) {
            showNotification('Source and destination locations must be different', 'error');
            destinationSelect.value = '';
        }
    }
}

/**
 * Search pallets via AJAX
 */
function searchPallets(query) {
    fetch('{% url "location_transfer:search_pallets" %}', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify({ query: query })
    })
    .then(response => response.json())
    .then(data => {
        if (data.pallets && data.pallets.length > 0) {
            showPalletSuggestions(data.pallets);
        }
    })
    .catch(error => {
        console.error('Error searching pallets:', error);
    });
}

/**
 * Search transfers via AJAX
 */
function searchTransfers(query) {
    // This would be implemented if you have a transfer search endpoint
    console.log('Searching transfers for:', query);
}

/**
 * Show pallet suggestions
 */
function showPalletSuggestions(pallets) {
    let dropdown = document.getElementById('pallet-suggestions');
    if (!dropdown) {
        dropdown = document.createElement('div');
        dropdown.id = 'pallet-suggestions';
        dropdown.className = 'dropdown-menu show position-absolute w-100';
        const input = document.querySelector('input[name="pallet_id"]');
        if (input) {
            input.parentNode.style.position = 'relative';
            input.parentNode.appendChild(dropdown);
        }
    }
    
    dropdown.innerHTML = '';
    pallets.forEach(pallet => {
        const item = document.createElement('a');
        item.className = 'dropdown-item';
        item.href = '#';
        item.textContent = `${pallet.pallet_id} - ${pallet.current_location}`;
        item.addEventListener('click', function(e) {
            e.preventDefault();
            const input = document.querySelector('input[name="pallet_id"]');
            if (input) {
                input.value = pallet.pallet_id;
            }
            dropdown.remove();
        });
        dropdown.appendChild(item);
    });
}

/**
 * Get pallet details via AJAX
 */
function getPalletDetails(palletId) {
    return fetch('{% url "location_transfer:get_pallet_details" %}', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify({ pallet_id: palletId })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            throw new Error(data.error);
        }
        return data;
    });
}

/**
 * Get available locations via AJAX
 */
function getAvailableLocations(sourceLocationId) {
    return fetch('{% url "location_transfer:get_available_locations" %}', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify({ source_location_id: sourceLocationId })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            throw new Error(data.error);
        }
        return data.locations;
    });
}

/**
 * Display pallet details
 */
function displayPalletDetails(data) {
    // Update pallet information
    const elements = {
        'pallet-id': data.pallet_id,
        'pallet-description': data.description || 'N/A',
        'current-location': data.current_location ? data.current_location.name : 'No Location',
        'pallet-status': data.status,
        'pallet-weight': data.weight ? data.weight + ' KGS' : 'N/A',
        'pallet-volume': data.volume ? data.volume + ' CBM' : 'N/A',
        'pallet-dimensions': data.dimensions || 'N/A',
        'total-items': data.total_items
    };
    
    Object.keys(elements).forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = elements[id];
        }
    });
    
    // Display pallet items
    displayPalletItems(data.items);
    
    // Show details cards
    showElement('pallet-details-card');
    showElement('pallet-items-card');
}

/**
 * Display pallet items
 */
function displayPalletItems(items) {
    const tbody = document.getElementById('pallet-items-tbody');
    if (!tbody) return;
    
    tbody.innerHTML = '';
    
    items.forEach(item => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${item.item_name}</td>
            <td><span class="badge bg-secondary">${item.item_code}</span></td>
            <td>${item.quantity}</td>
            <td>${item.unit_of_measure || 'N/A'}</td>
            <td>
                ${item.batch_number ? `<div><strong>Batch:</strong> ${item.batch_number}</div>` : ''}
                ${item.serial_number ? `<div><strong>Serial:</strong> ${item.serial_number}</div>` : ''}
            </td>
            <td>${item.total_value ? '$' + parseFloat(item.total_value).toFixed(2) : 'N/A'}</td>
        `;
        tbody.appendChild(row);
    });
}

/**
 * Display available locations
 */
function displayAvailableLocations(locations) {
    const grid = document.getElementById('available-locations-grid');
    if (!grid) return;
    
    grid.innerHTML = '';
    
    locations.forEach(location => {
        const utilizationClass = location.utilization < 50 ? 'success' : 
                               location.utilization < 80 ? 'warning' : 'danger';
        
        const card = document.createElement('div');
        card.className = 'col-md-6 col-lg-4 mb-3';
        card.innerHTML = `
            <div class="card location-card ${location.is_available ? 'border-success' : 'border-danger'}">
                <div class="card-body">
                    <h6 class="card-title">${location.name}</h6>
                    <p class="card-text text-muted">${location.code}</p>
                    <div class="d-flex justify-content-between align-items-center">
                        <span class="badge bg-${utilizationClass}">${location.utilization}% Full</span>
                        <span class="badge bg-secondary">${location.type}</span>
                    </div>
                    ${location.is_available ? 
                        '<div class="mt-2"><span class="badge bg-success">Available</span></div>' : 
                        '<div class="mt-2"><span class="badge bg-danger">Full</span></div>'
                    }
                </div>
            </div>
        `;
        grid.appendChild(card);
    });
    
    showElement('available-locations-card');
}

/**
 * Show element
 */
function showElement(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.style.display = 'block';
        element.classList.add('fade-in');
    }
}

/**
 * Hide element
 */
function hideElement(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.style.display = 'none';
        element.classList.remove('fade-in');
    }
}

/**
 * Show notification
 */
function showNotification(message, type = 'info', duration = 5000) {
    const container = document.getElementById('notification-container');
    if (!container) return;
    
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show`;
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    container.appendChild(notification);
    
    // Auto-remove after duration
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, duration);
}

/**
 * Set loading state
 */
function setLoadingState(element, loading = true) {
    if (loading) {
        element.classList.add('loading');
        element.disabled = true;
    } else {
        element.classList.remove('loading');
        element.disabled = false;
    }
}

/**
 * Format number
 */
function formatNumber(number, decimals = 2) {
    return parseFloat(number).toFixed(decimals);
}

/**
 * Format currency
 */
function formatCurrency(amount, currency = 'USD') {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: currency
    }).format(amount);
}

/**
 * Get CSRF token
 */
function getCSRFToken() {
    const token = document.querySelector('[name=csrfmiddlewaretoken]');
    return token ? token.value : '';
}

/**
 * Debounce function
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func.apply(this, args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Handle form submission
 */
function handleFormSubmission(form, successCallback = null) {
    const formData = new FormData(form);
    const submitButton = form.querySelector('button[type="submit"]');
    
    if (submitButton) {
        setLoadingState(submitButton, true);
    }
    
    fetch(form.action, {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (response.redirected) {
            window.location.href = response.url;
        } else {
            return response.text();
        }
    })
    .then(html => {
        if (html) {
            // Handle form errors
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            const errors = doc.querySelectorAll('.invalid-feedback');
            
            if (errors.length > 0) {
                errors.forEach(error => {
                    showNotification(error.textContent, 'error');
                });
            } else if (successCallback) {
                successCallback();
            }
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('An error occurred while processing your request', 'error');
    })
    .finally(() => {
        if (submitButton) {
            setLoadingState(submitButton, false);
        }
    });
}

/**
 * Initialize data tables
 */
function initializeDataTables() {
    const tables = document.querySelectorAll('.data-table');
    tables.forEach(table => {
        // Add sorting functionality
        const headers = table.querySelectorAll('th[data-sort]');
        headers.forEach(header => {
            header.addEventListener('click', function() {
                const column = this.getAttribute('data-sort');
                const direction = this.getAttribute('data-direction') === 'asc' ? 'desc' : 'asc';
                
                // Update all headers
                headers.forEach(h => h.setAttribute('data-direction', ''));
                this.setAttribute('data-direction', direction);
                
                // Sort table
                sortTable(table, column, direction);
            });
        });
    });
}

/**
 * Sort table
 */
function sortTable(table, column, direction) {
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    
    rows.sort((a, b) => {
        const aValue = a.querySelector(`td[data-${column}]`).getAttribute(`data-${column}`);
        const bValue = b.querySelector(`td[data-${column}]`).getAttribute(`data-${column}`);
        
        if (direction === 'asc') {
            return aValue.localeCompare(bValue);
        } else {
            return bValue.localeCompare(aValue);
        }
    });
    
    // Reorder rows
    rows.forEach(row => tbody.appendChild(row));
}

/**
 * Export data
 */
function exportData(format = 'csv') {
    const table = document.querySelector('.data-table');
    if (!table) return;
    
    const rows = Array.from(table.querySelectorAll('tr'));
    let data = '';
    
    if (format === 'csv') {
        rows.forEach(row => {
            const cells = Array.from(row.querySelectorAll('th, td'));
            const rowData = cells.map(cell => `"${cell.textContent.trim()}"`).join(',');
            data += rowData + '\n';
        });
        
        const blob = new Blob([data], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'location_transfer_data.csv';
        a.click();
        window.URL.revokeObjectURL(url);
    }
}

// Global utility functions
window.LocationTransfer = {
    showNotification,
    formatNumber,
    formatCurrency,
    getCSRFToken,
    handleFormSubmission,
    exportData
}; 