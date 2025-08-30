// LGP Module JavaScript

// Global variables
let itemCounter = 0;
let deletedItems = [];

// Initialize LGP module when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    initializeLGP();
});

function initializeLGP() {
    // Initialize form if present
    if (document.getElementById('lgp-form')) {
        initializeLGPForm();
    }
    
    // Initialize list if present
    if (document.getElementById('lgp-list')) {
        initializeLGPList();
    }
    
    // Initialize dispatch modal if present
    if (document.getElementById('dispatchModal')) {
        initializeDispatchModal();
    }
    
    // Initialize search functionality
    initializeSearch();
    
    // Initialize tooltips
    initializeTooltips();
}

// LGP Form Functions
function initializeLGPForm() {
    // Count existing items
    const existingItems = document.querySelectorAll('.item-row');
    itemCounter = existingItems.length;
    
    // Add one row if no existing items (for new forms)
    if (itemCounter === 0) {
        addLGPItem();
    }
    
    // Update formset management to reflect current state
    updateFormsetManagement();
    
    // Add event listeners
    const addItemBtn = document.getElementById('add-item-btn');
    if (addItemBtn) {
        addItemBtn.addEventListener('click', addLGPItem);
    }
    
    // Initialize automatic date calculation
    initializeDocumentDateCalculation();
    
    // Initialize existing delete buttons
    document.querySelectorAll('.delete-item-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            deleteLGPItem(this);
        });
    });
    
    // Initialize tab event listeners for existing remarks fields
    initializeRemarksTabListeners();
    
    // Initialize form validation
    initializeFormValidation();
    
    // Initialize auto-calculation
    initializeAutoCalculation();
    
    // Initialize form auto-save (optional)
    // initializeAutoSave();
}

function addLGPItem() {
    const tbody = document.querySelector('#itemsTableBody');
    
    // Get the template and clone it
    const template = document.querySelector('#emptyItemRowTemplate');
    if (!template) {
        console.error('Template not found');
        return;
    }
    
    const templateContent = template.content.cloneNode(true);
    const newRow = templateContent.querySelector('tr');
    
    // Update all the name attributes and IDs to use the current counter
    const inputs = newRow.querySelectorAll('input, select, textarea');
    inputs.forEach(input => {
        if (input.name) {
            input.name = input.name.replace('__prefix__', itemCounter);
        }
        if (input.id) {
            input.id = input.id.replace('__prefix__', itemCounter);
        }
    });
    
    // Set the data-form-index
    newRow.setAttribute('data-form-index', itemCounter);
    
    // Set line number
    const lineNumberInput = newRow.querySelector('input[name*="line_number"]');
    if (lineNumberInput) {
        lineNumberInput.value = itemCounter + 1;
    }
    
    // Add hidden fields for Django formset
    const lastCell = newRow.querySelector('td:last-child');
    if (lastCell) {
        // Add hidden DELETE and id fields if they don't exist
        if (!lastCell.querySelector('input[name$="-DELETE"]')) {
            lastCell.innerHTML += `<input type="hidden" name="items-${itemCounter}-DELETE" value="">`;
        }
        if (!lastCell.querySelector('input[name$="-id"]')) {
            lastCell.innerHTML += `<input type="hidden" name="items-${itemCounter}-id" value="">`;
        }
    }
    
    // Add event listener for delete button
    const deleteBtn = newRow.querySelector('.delete-item-btn');
    if (deleteBtn) {
        deleteBtn.addEventListener('click', function() {
            deleteLGPItem(this);
        });
    }
    
    // Add event listener for Tab key on remarks field to auto-generate new row
    const remarksField = newRow.querySelector('textarea[name*="remarks"]');
    if (remarksField) {
        remarksField.addEventListener('keydown', handleRemarksTab);
    }
    
    tbody.appendChild(newRow);
    itemCounter++;
    
    // Update the TOTAL_FORMS count in the management form
    updateFormsetManagement();
    
    // Add fade-in animation
    newRow.classList.add('lgp-fade-in');
    
    // Focus on first input
    const firstInput = newRow.querySelector('input, select');
    if (firstInput) {
        firstInput.focus();
    }
    
    updateTotals();
}



function deleteLGPItem(button) {
    const row = button.closest('.item-row');
    const deleteInput = row.querySelector('input[name$="-DELETE"]');
    const idInput = row.querySelector('input[name$="-id"]');
    
    if (idInput && idInput.value) {
        // Existing item - mark for deletion
        deleteInput.value = 'on';
        row.classList.add('to-delete');
        row.style.display = 'none';
        deletedItems.push(row);
    } else {
        // New item - remove completely
        row.remove();
        // Decrease counter for removed new items
        itemCounter--;
    }
    
    // Update the formset management form
    updateFormsetManagement();
    updateTotals();
}

function updateTotals() {
    let totalQuantity = 0;
    let totalWeight = 0;
    let totalVolume = 0;
    let totalValue = 0;
    
    // Calculate totals from all visible item rows
    document.querySelectorAll('.item-row').forEach(row => {
        const quantity = parseFloat(row.querySelector('input[name$="-quantity"]')?.value || 0);
        const weight = parseFloat(row.querySelector('input[name$="-weight"]')?.value || 0);
        const volume = parseFloat(row.querySelector('input[name$="-volume"]')?.value || 0);
        const value = parseFloat(row.querySelector('input[name$="-value"]')?.value || 0);
        
        totalQuantity += quantity;
        totalWeight += weight;
        totalVolume += volume;
        totalValue += value;
    });
    
    // Update footer totals using correct IDs
    document.getElementById('totalQuantity').textContent = totalQuantity.toFixed(0);
    document.getElementById('totalWeight').textContent = totalWeight.toFixed(3);
    document.getElementById('totalVolume').textContent = totalVolume.toFixed(3);
    document.getElementById('totalValue').textContent = totalValue.toFixed(2);
}

function updateFormsetManagement() {
    // Update TOTAL_FORMS count in the management form
    const totalFormsInput = document.querySelector('input[name="items-TOTAL_FORMS"]');
    if (totalFormsInput) {
        totalFormsInput.value = itemCounter;
    }
}

function initializeRemarksTabListeners() {
    // Add tab event listeners to all existing remarks fields
    const tbody = document.querySelector('#itemsTableBody');
    if (!tbody) return;
    
    const remarksFields = tbody.querySelectorAll('textarea[name*="remarks"]');
    remarksFields.forEach(remarksField => {
        // Remove existing listener to avoid duplicates
        remarksField.removeEventListener('keydown', handleRemarksTab);
        // Add new listener
        remarksField.addEventListener('keydown', handleRemarksTab);
    });
}

function handleRemarksTab(e) {
    if (e.key === 'Tab' && !e.shiftKey) {
        const tbody = document.querySelector('#itemsTableBody');
        const currentRow = e.target.closest('.item-row');
        const allRows = tbody.querySelectorAll('.item-row');
        const currentRowIndex = Array.from(allRows).indexOf(currentRow);
        
        if (currentRowIndex === allRows.length - 1) {
            // This is the last row, add a new one
            setTimeout(() => {
                addLGPItem();
            }, 10); // Small delay to ensure tab navigation completes
        }
    }
}

// LGP List Functions
function initializeLGPList() {
    // Initialize DataTable if available
    if (typeof DataTable !== 'undefined') {
        const table = document.getElementById('lgp-table');
        if (table) {
            new DataTable(table, {
                pageLength: 25,
                responsive: true,
                order: [[0, 'desc']], // Order by LGP Number descending
                columnDefs: [
                    { targets: -1, orderable: false } // Disable sorting on Actions column
                ]
            });
        }
    }
    
    // Initialize bulk actions
    initializeBulkActions();
}

function initializeBulkActions() {
    const selectAllCheckbox = document.getElementById('select-all-lgps');
    const itemCheckboxes = document.querySelectorAll('.lgp-checkbox');
    const bulkActionBtn = document.getElementById('bulk-action-btn');
    
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function() {
            itemCheckboxes.forEach(checkbox => {
                checkbox.checked = this.checked;
            });
            updateBulkActionButton();
        });
    }
    
    itemCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', updateBulkActionButton);
    });
}

function updateBulkActionButton() {
    const checkedBoxes = document.querySelectorAll('.lgp-checkbox:checked');
    const bulkActionBtn = document.getElementById('bulk-action-btn');
    
    if (bulkActionBtn) {
        if (checkedBoxes.length > 0) {
            bulkActionBtn.style.display = 'inline-block';
            bulkActionBtn.textContent = `Actions (${checkedBoxes.length})`;
        } else {
            bulkActionBtn.style.display = 'none';
        }
    }
}

// Search Functions
function initializeSearch() {
    const searchForm = document.getElementById('lgp-search-form');
    if (searchForm) {
        // Auto-submit on filter change
        const filterInputs = searchForm.querySelectorAll('select, input[type="date"]');
        filterInputs.forEach(input => {
            input.addEventListener('change', function() {
                searchForm.submit();
            });
        });
        
        // Debounced search for text inputs
        const textInputs = searchForm.querySelectorAll('input[type="text"], input[type="search"]');
        textInputs.forEach(input => {
            let timeout;
            input.addEventListener('input', function() {
                clearTimeout(timeout);
                timeout = setTimeout(() => {
                    searchForm.submit();
                }, 500);
            });
        });
    }
}

// Dispatch Modal Functions
function initializeDispatchModal() {
    const dispatchModal = document.getElementById('dispatchModal');
    if (dispatchModal) {
        dispatchModal.addEventListener('show.bs.modal', function(event) {
            const button = event.relatedTarget;
            const lgpId = button.getAttribute('data-lgp-id');
            const lgpNumber = button.getAttribute('data-lgp-number');
            
            // Update modal content
            const modalTitle = dispatchModal.querySelector('.modal-title');
            const modalBody = dispatchModal.querySelector('.modal-body');
            
            modalTitle.textContent = `Dispatch LGP ${lgpNumber}`;
            
            // Load LGP details via AJAX
            loadLGPDetails(lgpId, modalBody);
        });
    }
}

function loadLGPDetails(lgpId, container) {
    container.innerHTML = '<div class="text-center"><div class="spinner-border" role="status"></div></div>';
    
    fetch(`/lgp/${lgpId}/details/`)
        .then(response => response.json())
        .then(data => {
            container.innerHTML = `
                <div class="row">
                    <div class="col-md-6">
                        <h6>LGP Details</h6>
                        <p><strong>Customer:</strong> ${data.customer}</p>
                        <p><strong>DPW Ref No:</strong> ${data.dpw_ref_no}</p>
                        <p><strong>Warehouse:</strong> ${data.warehouse}</p>
                    </div>
                    <div class="col-md-6">
                        <h6>Summary</h6>
                        <p><strong>Total Items:</strong> ${data.total_items}</p>
                        <p><strong>Total Weight:</strong> ${data.total_weight} kg</p>
                        <p><strong>Total Value:</strong> $${data.total_value}</p>
                    </div>
                </div>
                <div class="mt-3">
                    <h6>Dispatch Information</h6>
                    <form id="dispatch-form" action="/lgp/${lgpId}/dispatch/" method="post">
                        <div class="mb-3">
                            <label class="form-label">Dispatch Date</label>
                            <input type="date" class="form-control" name="dispatch_date" 
                                   value="${new Date().toISOString().split('T')[0]}" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Dispatch Notes</label>
                            <textarea class="form-control" name="dispatch_notes" rows="3"
                                      placeholder="Enter any dispatch notes..."></textarea>
                        </div>
                    </form>
                </div>
            `;
        })
        .catch(error => {
            container.innerHTML = '<div class="alert alert-danger">Error loading LGP details</div>';
            console.error('Error:', error);
        });
}

// Form Validation
function initializeFormValidation() {
    const form = document.getElementById('lgp-form');
    if (form) {
        console.log('Form validation initialized for:', form);
        
        form.addEventListener('submit', function(event) {
            console.log('=== FORM SUBMIT EVENT START ===');
            console.log('Event object:', event);
            console.log('Form data before validation:');
            
            // Log form data
            const formData = new FormData(form);
            for (let [key, value] of formData.entries()) {
                console.log(`${key}: ${value}`);
            }
            
            // Temporarily disable client-side validation to see server-side errors
            console.log('Client-side validation disabled - allowing form submission');
            console.log('=== FORM SUBMIT EVENT END ===');
            
            // Let the form submit naturally to see server-side validation
            return true;
        });
        
        // Also log any button clicks
        const submitButtons = form.querySelectorAll('button[type="submit"], input[type="submit"]');
        console.log('Found submit buttons:', submitButtons.length);
        submitButtons.forEach((button, index) => {
            console.log(`Submit button ${index}:`, button);
            button.addEventListener('click', function(event) {
                console.log('=== BUTTON CLICK EVENT ===');
                console.log('Submit button clicked:', button);
                console.log('Button text:', button.textContent.trim());
                console.log('Button event:', event);
                console.log('Event type:', event.type);
                console.log('Event target:', event.target);
                console.log('=== END BUTTON CLICK ===');
            });
        });
        
        // Add a direct click listener to any element with "Save LGP" text
        document.addEventListener('click', function(event) {
            if (event.target.textContent && event.target.textContent.includes('Save LGP')) {
                console.log('=== SAVE LGP CLICKED ===');
                console.log('Clicked element:', event.target);
                console.log('Element type:', event.target.tagName);
                console.log('Element classes:', event.target.className);
                console.log('=== END SAVE LGP CLICK ===');
            }
        });
    } else {
        console.error('Form with ID "lgp-form" not found');
    }
}

function validateLGPForm() {
    console.log('=== VALIDATION START ===');
    let isValid = true;
    const errors = [];
    
    // Check required fields
    const requiredFields = [
        { name: 'customer', label: 'Customer' },
        { name: 'dpw_ref_no', label: 'DPW Ref No' },
        { name: 'document_date', label: 'Document Date' },
        { name: 'warehouse', label: 'Warehouse' }
    ];
    
    console.log('Checking required fields...');
    requiredFields.forEach(field => {
        const input = document.querySelector(`[name="${field.name}"]`);
        console.log(`Field ${field.name}:`, input, 'Value:', input ? input.value : 'NOT FOUND');
        if (input && !input.value.trim()) {
            errors.push(`${field.label} is required`);
            isValid = false;
            console.log(`❌ ${field.label} validation failed`);
        } else if (input) {
            console.log(`✅ ${field.label} validation passed`);
        } else {
            errors.push(`${field.label} is required`);
            isValid = false;
            console.log(`❌ ${field.label} field not found`);
        }
    });
    
    // Check if at least one item exists
    const visibleItems = document.querySelectorAll('.item-row');
    console.log('Visible items found:', visibleItems.length);
    if (visibleItems.length === 0) {
        errors.push('At least one LGP item is required');
        isValid = false;
        console.log('❌ No items found');
    } else {
        console.log('✅ Items exist, checking content...');
    }
    
    // Validate item data - only check if items have some content
    let hasValidItem = false;
    visibleItems.forEach((row, index) => {
        const description = row.querySelector('textarea[name$="-good_description"]');
        const quantity = row.querySelector('input[name$="-quantity"]');
        
        console.log(`Item ${index}:`);
        console.log('  Description:', description ? description.value : 'NOT FOUND');
        console.log('  Quantity:', quantity ? quantity.value : 'NOT FOUND');
        
        // If either description or quantity has content, consider it a valid item
        if ((description && description.value.trim()) || (quantity && quantity.value && parseFloat(quantity.value) > 0)) {
            hasValidItem = true;
            console.log(`  ✅ Item ${index} is valid`);
        } else {
            console.log(`  ❌ Item ${index} is empty`);
        }
    });
    
    if (!hasValidItem && visibleItems.length > 0) {
        errors.push('Please fill in at least one item with description or quantity');
        isValid = false;
        console.log('❌ No valid items found');
    } else if (hasValidItem) {
        console.log('✅ At least one valid item found');
    }
    
    console.log('Validation errors:', errors);
    console.log('Overall validation result:', isValid);
    
    // Display errors
    if (errors.length > 0) {
        showValidationErrors(errors);
    }
    
    console.log('=== VALIDATION END ===');
    return isValid;
}

function showValidationErrors(errors) {
    const errorContainer = document.getElementById('validation-errors');
    if (errorContainer) {
        errorContainer.innerHTML = `
            <div class="alert alert-danger alert-dismissible fade show" role="alert">
                <h6>Please correct the following errors:</h6>
                <ul class="mb-0">
                    ${errors.map(error => `<li>${error}</li>`).join('')}
                </ul>
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        errorContainer.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
}

// Auto-calculation
function initializeAutoCalculation() {
    // Update totals when any numeric input changes
    document.addEventListener('input', function(event) {
        if (event.target.matches('input[name$="-quantity"], input[name$="-weight"], input[name$="-volume"], input[name$="-value"]')) {
            updateTotals();
        }
    });
}

// Tooltips
function initializeTooltips() {
    if (typeof bootstrap !== 'undefined') {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function(tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
}

// Utility Functions
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(notification);
    
    // Auto-remove after 1 second
    setTimeout(() => {
        if (notification.parentNode) {
            notification.classList.remove('show');
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.remove();
                }
            }, 150); // Wait for fade animation to complete
        }
    }, 1000);
}

function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

function formatCurrency(amount, currencyCode = 'USD') {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: currencyCode
    }).format(amount);
}

function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

// Document Date Calculation Functions
function initializeDocumentDateCalculation() {
    const documentDateField = document.querySelector('input[name="document_date"]');
    const validityDateField = document.querySelector('input[name="document_validity_date"]');
    
    if (documentDateField && validityDateField) {
        // Set initial values if document date is empty
        if (!documentDateField.value) {
            const today = new Date();
            documentDateField.value = today.toISOString().split('T')[0];
            
            // Set validity date to 365 days from today
            const validityDate = new Date(today);
            validityDate.setDate(validityDate.getDate() + 365);
            validityDateField.value = validityDate.toISOString().split('T')[0];
        }
        
        // Add event listener for document date changes
        documentDateField.addEventListener('change', function() {
            if (this.value) {
                const documentDate = new Date(this.value);
                const validityDate = new Date(documentDate);
                validityDate.setDate(validityDate.getDate() + 365);
                validityDateField.value = validityDate.toISOString().split('T')[0];
            }
        });
    }
}

// Export functions for global access
window.LGP = {
    addItem: addLGPItem,
    deleteItem: deleteLGPItem,
    updateTotals: updateTotals,
    showNotification: showNotification,
    confirmAction: confirmAction,
    formatCurrency: formatCurrency,
    formatDate: formatDate,
    refreshAvailableLGPs: refreshAvailableLGPs,
    handleDispatchSuccess: handleDispatchSuccess
};

// Dynamic LGP List Management
function refreshAvailableLGPs() {
    // Refresh the LGP list to show only available (non-dispatched) LGPs
    if (window.location.pathname.includes('/lgp/')) {
        // Only refresh if we're on an LGP page
        const currentUrl = new URL(window.location);
        const params = currentUrl.searchParams;
        
        fetch(currentUrl.pathname + '?' + params.toString(), {
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.text())
        .then(html => {
            // Parse the response and update the table
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            const newTableBody = doc.querySelector('.table tbody');
            const currentTableBody = document.querySelector('.table tbody');
            
            if (newTableBody && currentTableBody) {
                currentTableBody.innerHTML = newTableBody.innerHTML;
                
                // Update the count
                const newCount = doc.querySelector('.card-header h5');
                const currentCount = document.querySelector('.card-header h5');
                if (newCount && currentCount) {
                    currentCount.innerHTML = newCount.innerHTML;
                }
                
                showNotification('LGP list updated - dispatched items removed', 'success');
            }
        })
        .catch(error => {
            console.error('Error refreshing LGP list:', error);
        });
    }
}

// Handle successful dispatch operations
function handleDispatchSuccess(dispatchedLGPIds) {
    if (Array.isArray(dispatchedLGPIds)) {
        // Remove dispatched LGP rows from the current view
        dispatchedLGPIds.forEach(lgpId => {
            const rows = document.querySelectorAll(`tr[data-lgp-id="${lgpId}"]`);
            rows.forEach(row => {
                row.style.transition = 'opacity 0.5s ease-out';
                row.style.opacity = '0';
                setTimeout(() => {
                    row.remove();
                }, 500);
            });
        });
        
        // Update the total count
        setTimeout(() => {
            updateLGPCount();
        }, 600);
        
        showNotification(`${dispatchedLGPIds.length} LGP(s) dispatched and removed from available list`, 'success');
    } else {
        // Fallback: refresh the entire list
        refreshAvailableLGPs();
    }
}

// Update LGP count in the header
function updateLGPCount() {
    const remainingRows = document.querySelectorAll('.lgp-row').length;
    const countElement = document.querySelector('.card-header h5');
    if (countElement) {
        const currentText = countElement.innerHTML;
        const updatedText = currentText.replace(/\(\d+\)/, `(${remainingRows})`);
        countElement.innerHTML = updatedText;
    }
}

// Auto-refresh functionality for LGP list
function initializeLGPListAutoRefresh() {
    // Auto-refresh every 30 seconds if on LGP list page
    if (window.location.pathname.includes('/lgp/') && document.querySelector('.lgp-row')) {
        setInterval(() => {
            refreshAvailableLGPs();
        }, 30000); // 30 seconds
    }
}

// AJAX Functions for dynamic loading
function loadLGPList(filters = {}) {
    const params = new URLSearchParams(filters);
    
    fetch(`/lgp/search/?${params}`)
        .then(response => response.json())
        .then(data => {
            updateLGPTable(data.lgps);
            updatePagination(data.pagination);
        })
        .catch(error => {
            console.error('Error loading LGP list:', error);
            showNotification('Error loading LGP list', 'danger');
        });
}

function updateLGPTable(lgps) {
    const tbody = document.querySelector('#lgp-table tbody');
    if (!tbody) return;
    
    tbody.innerHTML = lgps.map(lgp => `
        <tr>
            <td>
                <input type="checkbox" class="form-check-input lgp-checkbox" value="${lgp.id}">
            </td>
            <td>
                <a href="/lgp/${lgp.id}/" class="lgp-number-link">${lgp.lgp_number}</a>
            </td>
            <td>${lgp.customer}</td>
            <td>${lgp.dpw_ref_no}</td>
            <td>${formatDate(lgp.document_date)}</td>
            <td>${lgp.warehouse}</td>
            <td>
                <span class="badge lgp-status-${lgp.status.toLowerCase()}">${lgp.status}</span>
            </td>
            <td>${lgp.total_items}</td>
            <td>${formatCurrency(lgp.total_value)}</td>
            <td>${formatDate(lgp.created_at)}</td>
            <td>
                <div class="btn-group btn-group-sm">
                    <a href="/lgp/${lgp.id}/" class="btn btn-outline-primary" title="View">
                        <i class="bi bi-eye"></i>
                    </a>
                    <a href="/lgp/${lgp.id}/edit/" class="btn btn-outline-secondary" title="Edit">
                        <i class="bi bi-pencil"></i>
                    </a>
                    <a href="/lgp/${lgp.id}/dispatch/" class="btn btn-outline-success" title="Dispatch">
                        <i class="bi bi-truck"></i>
                    </a>
                </div>
            </td>
        </tr>
    `).join('');
    
    // Reinitialize checkboxes
    initializeBulkActions();
}

function updatePagination(pagination) {
    const paginationContainer = document.querySelector('.pagination-container');
    if (!paginationContainer || !pagination) return;
    
    // Update pagination HTML based on pagination data
    // This would depend on your pagination structure
}

// Print functionality
function printLGP(lgpId) {
    window.open(`/lgp/${lgpId}/print/`, '_blank');
}

// Export LGP data
function exportLGP(lgpId, format = 'pdf') {
    window.location.href = `/lgp/${lgpId}/export/?format=${format}`;
}

// Auto-save functionality (optional)
function initializeAutoSave() {
    let autoSaveTimeout;
    const form = document.getElementById('lgp-form');
    
    if (form) {
        form.addEventListener('input', function() {
            clearTimeout(autoSaveTimeout);
            autoSaveTimeout = setTimeout(() => {
                autoSaveLGP();
            }, 30000); // Auto-save every 30 seconds
        });
    }
}

function autoSaveLGP() {
    const form = document.getElementById('lgp-form');
    if (!form) return;
    
    const formData = new FormData(form);
    formData.append('auto_save', 'true');
    
    fetch(form.action, {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Draft saved automatically', 'success');
        }
    })
    .catch(error => {
        console.error('Auto-save error:', error);
    });
}