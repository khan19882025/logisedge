// Job Management JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize job management functionality
    initializeJobManagement();
});

function initializeJobManagement() {
    // Initialize quick view functionality
    initializeQuickView();
    
    // Initialize form enhancements
    initializeFormEnhancements();
    
    // Initialize search functionality
    initializeSearch();
}

// Quick View Functionality
function initializeQuickView() {
    const quickViewButtons = document.querySelectorAll('.quick-view-btn');
    const quickViewModal = document.getElementById('quickViewModal');
    const quickViewContent = document.getElementById('quickViewContent');
    
    quickViewButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const jobId = this.getAttribute('data-job-id');
            loadQuickView(jobId);
        });
    });
    
    function loadQuickView(jobId) {
        // Show loading state
        quickViewContent.innerHTML = '<div class="text-center"><i class="bi bi-arrow-clockwise spin"></i> Loading...</div>';
        
        // Make AJAX request
        fetch(`/job/${jobId}/quick-view/`)
            .then(response => response.text())
            .then(html => {
                quickViewContent.innerHTML = html;
                const modal = new bootstrap.Modal(quickViewModal);
                modal.show();
            })
            .catch(error => {
                console.error('Error loading quick view:', error);
                quickViewContent.innerHTML = '<div class="alert alert-danger">Error loading job details.</div>';
            });
    }
}

// Form Enhancements
function initializeFormEnhancements() {
    // Auto-save form data
    const jobForm = document.getElementById('jobForm');
    if (jobForm) {
        initializeAutoSave(jobForm);
    }
    
    // Enhanced date picker
    const dateInputs = document.querySelectorAll('input[type="datetime-local"]');
    dateInputs.forEach(input => {
        enhanceDatePicker(input);
    });
    
    // Character counter for text areas
    const textAreas = document.querySelectorAll('textarea');
    textAreas.forEach(textarea => {
        addCharacterCounter(textarea);
    });
    
    // Customer salesman auto-population
    initializeCustomerSalesmanAutoPopulate();
    
    // Cargo table functionality - only initialize if not on job form page
    // (job form uses Django formset with its own JavaScript)
    if (!document.getElementById('cargoTableBody')) {
        initializeCargoTable();
    }
}

function initializeAutoSave(form) {
    // Disable auto-save for job creation/editing forms as it's not implemented on server
    if (form.action.includes('/job/create/') || form.action.includes('/job/update/')) {
        return;
    }
    
    let autoSaveTimer;
    const formData = new FormData(form);
    
    form.addEventListener('input', function() {
        clearTimeout(autoSaveTimer);
        autoSaveTimer = setTimeout(() => {
            saveFormData(form);
        }, 2000); // Auto-save after 2 seconds of inactivity
    });
    
    function saveFormData(form) {
        const formData = new FormData(form);
        formData.append('auto_save', 'true');
        
        fetch(form.action, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => {
            // Check if response is JSON
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                return response.json();
            } else {
                // If not JSON, return a default response
                return { success: false, message: 'Auto-save not supported for this form' };
            }
        })
        .then(data => {
            if (data.success) {
                showNotification('Form auto-saved', 'success');
            } else {
                // Don't show error for auto-save failures
                console.log('Auto-save response:', data.message || 'Auto-save completed');
            }
        })
        .catch(error => {
            // Don't log auto-save errors to console as they're not critical
            console.log('Auto-save not available:', error.message);
        });
    }
}

function enhanceDatePicker(input) {
    // Add today button
    const todayButton = document.createElement('button');
    todayButton.type = 'button';
    todayButton.className = 'btn btn-outline-secondary btn-sm ms-2';
    todayButton.textContent = 'Today';
    todayButton.onclick = function() {
        const now = new Date();
        const localDateTime = new Date(now.getTime() - now.getTimezoneOffset() * 60000)
            .toISOString().slice(0, 16);
        input.value = localDateTime;
    };
    
    input.parentNode.appendChild(todayButton);
}

function addCharacterCounter(textarea) {
    const maxLength = textarea.getAttribute('maxlength');
    if (!maxLength) return;
    
    const counter = document.createElement('div');
    counter.className = 'form-text text-muted character-counter';
    counter.textContent = `0 / ${maxLength} characters`;
    
    textarea.parentNode.appendChild(counter);
    
    textarea.addEventListener('input', function() {
        const currentLength = this.value.length;
        counter.textContent = `${currentLength} / ${maxLength} characters`;
        
        if (currentLength > maxLength * 0.9) {
            counter.classList.add('text-warning');
        } else {
            counter.classList.remove('text-warning');
        }
        
        if (currentLength > maxLength) {
            counter.classList.add('text-danger');
        } else {
            counter.classList.remove('text-danger');
        }
    });
}

// Search Functionality
function initializeSearch() {
    const searchForm = document.querySelector('form[method="get"]');
    if (!searchForm) return;
    
    // Debounced search
    let searchTimer;
    const searchInput = searchForm.querySelector('input[name="search_term"]');
    
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimer);
            searchTimer = setTimeout(() => {
                performSearch(searchForm);
            }, 500);
        });
    }
    
    // Clear search
    const clearButton = document.querySelector('a[href*="job_list"]');
    if (clearButton) {
        clearButton.addEventListener('click', function(e) {
            e.preventDefault();
            clearSearch(searchForm);
        });
    }
}

function performSearch(form) {
    const formData = new FormData(form);
    const searchParams = new URLSearchParams(formData);
    
    fetch(`${window.location.pathname}?${searchParams.toString()}`, {
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.text())
    .then(html => {
        // Update the jobs list section
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, 'text/html');
        const newJobsList = doc.querySelector('.row:last-child');
        const currentJobsList = document.querySelector('.row:last-child');
        
        if (newJobsList && currentJobsList) {
            currentJobsList.innerHTML = newJobsList.innerHTML;
        }
    })
    .catch(error => {
        console.error('Search error:', error);
    });
}

function clearSearch(form) {
    form.reset();
    window.location.href = form.action;
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
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 5000);
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function formatDuration(hours) {
    if (!hours) return 'Not set';
    
    const wholeHours = Math.floor(hours);
    const minutes = Math.round((hours - wholeHours) * 60);
    
    if (minutes === 0) {
        return `${wholeHours}h`;
    } else {
        return `${wholeHours}h ${minutes}m`;
    }
}

// Export functionality
function exportJobs(format = 'csv') {
    const searchParams = new URLSearchParams(window.location.search);
    searchParams.append('export', format);
    
    window.location.href = `/job/export/?${searchParams.toString()}`;
}

// Job status updates
function updateJobStatus(jobId, status) {
    fetch(`/job/${jobId}/update-status/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({ status: status })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Job status updated successfully', 'success');
            // Reload the page or update the UI
            location.reload();
        } else {
            showNotification('Error updating job status', 'danger');
        }
    })
    .catch(error => {
        console.error('Error updating job status:', error);
        showNotification('Error updating job status', 'danger');
    });
}

// Get CSRF token
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

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + N for new job
    if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
        e.preventDefault();
        const newJobLink = document.querySelector('a[href*="job_create"]');
        if (newJobLink) {
            newJobLink.click();
        }
    }
    
    // Ctrl/Cmd + F for search
    if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
        e.preventDefault();
        const searchInput = document.querySelector('input[name="search_term"]');
        if (searchInput) {
            searchInput.focus();
        }
    }
    
    // Escape to close modals
    if (e.key === 'Escape') {
        const modals = document.querySelectorAll('.modal.show');
        modals.forEach(modal => {
            const modalInstance = bootstrap.Modal.getInstance(modal);
            if (modalInstance) {
                modalInstance.hide();
            }
        });
    }
});

// Customer Salesman Auto-population
function initializeCustomerSalesmanAutoPopulate() {
    const customerSelect = document.getElementById('id_customer_name');
    const salesmanSelect = document.getElementById('salesman-select');
    
    if (customerSelect && salesmanSelect) {
        customerSelect.addEventListener('change', function() {
            const customerId = this.value;
            if (customerId) {
                fetchCustomerSalesman(customerId, salesmanSelect);
            } else {
                // Clear salesman if no customer selected
                salesmanSelect.innerHTML = '<option value="">Select Salesman</option>';
            }
        });
    }
}

function fetchCustomerSalesman(customerId, salesmanSelect) {
    // Show loading state
    salesmanSelect.innerHTML = '<option value="">Loading...</option>';
    salesmanSelect.disabled = true;
    
    fetch(`/job/get-customer-salesman/${customerId}/`)
        .then(response => response.json())
        .then(data => {
            salesmanSelect.disabled = false;
            
            if (data.success) {
                if (data.salesman) {
                    // Populate salesman data
                    salesmanSelect.innerHTML = `
                        <option value="${data.salesman.id}">${data.salesman.name} (${data.salesman.code})</option>
                    `;
                } else {
                    // No salesman assigned to this customer
                    salesmanSelect.innerHTML = '<option value="">No salesman assigned</option>';
                    showNotification('No salesman assigned to this customer', 'warning');
                }
            } else {
                salesmanSelect.innerHTML = '<option value="">Error loading salesman</option>';
                showNotification('Error loading salesman data', 'danger');
            }
        })
        .catch(error => {
            console.error('Error fetching customer salesman:', error);
            salesmanSelect.disabled = false;
            salesmanSelect.innerHTML = '<option value="">Error loading salesman</option>';
            showNotification('Error loading salesman data', 'danger');
        });
}

// ===== CARGO TABLE MANAGEMENT =====

/**
 * Add a new cargo row to the table
 */
function addCargoRow() {
    const tbody = document.getElementById('cargoTableBody');
    if (!tbody) return;
    
    // Get the total forms count and update it
    const totalForms = document.getElementById('id_cargo_items-TOTAL_FORMS');
    const formNum = tbody.querySelectorAll('tr').length;
    
    // Update the total forms count
    if (totalForms) {
        totalForms.value = formNum + 1;
    }
    
    const newRow = createCargoRow(formNum);
    tbody.appendChild(newRow);
    
    // Set up event listeners for the new row
    setupCargoRowEventListeners(newRow);
    
    // Update row numbers and totals
    updateRowNumbers();
    updateTotals();
    
    // Return the new row for focus management
    return newRow;
}

/**
 * Create a new cargo row element with proper Django formset structure
 */
function createCargoRow(formNum) {
    const row = document.createElement('tr');
    row.className = 'cargo-form-row';
    row.innerHTML = `
        <td>${formNum + 1}</td>
        <td>
            <input type="text" class="form-control form-control-sm item-code-input" name="cargo_items-${formNum}-item_code" id="id_cargo_items-${formNum}-item_code" readonly>
        </td>
        <td>
            <select class="form-select form-select-sm item-select" name="cargo_items-${formNum}-item" id="id_cargo_items-${formNum}-item">
                <option value="">Select Item</option>
            </select>
        </td>
        <td>
            <input type="text" class="form-control form-control-sm" name="cargo_items-${formNum}-hs_code" id="id_cargo_items-${formNum}-hs_code" placeholder="HS Code">
        </td>
        <td>
            <select class="form-select form-select-sm unit-select" name="cargo_items-${formNum}-unit" id="id_cargo_items-${formNum}-unit">
                <option value="">Unit</option>
                <option value="PCS">PCS</option>
                <option value="KG">KG</option>
                <option value="M">M</option>
                <option value="L">L</option>
                <option value="BOX">BOX</option>
                <option value="CARTON">CARTON</option>
                <option value="CTN">CTN</option>
            </select>
        </td>
        <td>
            <input type="number" class="form-control form-control-sm qty-input" name="cargo_items-${formNum}-quantity" id="id_cargo_items-${formNum}-quantity" step="0.01" min="0" placeholder="Qty">
        </td>
        <td>
            <input type="text" class="form-control form-control-sm" name="cargo_items-${formNum}-coo" id="id_cargo_items-${formNum}-coo" placeholder="COO">
        </td>
        <td>
            <input type="number" class="form-control form-control-sm n-weight-input" name="cargo_items-${formNum}-net_weight" id="id_cargo_items-${formNum}-net_weight" step="0.01" min="0" placeholder="N-weight">
        </td>
        <td>
            <input type="number" class="form-control form-control-sm g-weight-input" name="cargo_items-${formNum}-gross_weight" id="id_cargo_items-${formNum}-gross_weight" step="0.01" min="0" placeholder="G-weight">
        </td>
        <td>
            <input type="number" class="form-control form-control-sm rate-input" name="cargo_items-${formNum}-rate" id="id_cargo_items-${formNum}-rate" step="0.01" min="0" placeholder="Rate">
        </td>
        <td>
            <input type="number" class="form-control form-control-sm amount-input" name="cargo_items-${formNum}-amount" id="id_cargo_items-${formNum}-amount" step="0.01" readonly placeholder="Amount">
        </td>
        <td>
            <input type="text" class="form-control form-control-sm remark-input" name="cargo_items-${formNum}-remark" id="id_cargo_items-${formNum}-remark" placeholder="Remark">
        </td>
        <td>
            <button type="button" class="btn btn-danger btn-sm remove-row-btn">
                <i class="bi bi-trash"></i>
            </button>
        </td>
    `;
    
    return row;
}

/**
 * Set up event listeners for a cargo row
 */
function setupCargoRowEventListeners(row) {
    // Item selection - look for field name containing "cargo_items" and "item"
    const itemSelect = row.querySelector('select[name*="cargo_items-"][name*="-item"]');
    if (itemSelect) {
        // Always populate dropdown for new rows
        populateItemDropdown(itemSelect);
        
        itemSelect.addEventListener('change', function() {
            const itemId = this.value;
            if (itemId) {
                fetchItemData(itemId, this);
            } else {
                clearItemFields(this);
            }
        });
    }
    
    // Calculation fields - look for field names containing the respective field names
    const qtyInput = row.querySelector('input[name*="cargo_items-"][name*="-quantity"]');
    const rateInput = row.querySelector('input[name*="cargo_items-"][name*="-rate"]');
    const nWeightInput = row.querySelector('input[name*="cargo_items-"][name*="-net_weight"]');
    const gWeightInput = row.querySelector('input[name*="cargo_items-"][name*="-gross_weight"]');
    
    if (qtyInput) {
        qtyInput.addEventListener('input', () => calculateRowAmount(row));
    }
    
    if (rateInput) {
        rateInput.addEventListener('input', () => calculateRowAmount(row));
    }
    
    if (nWeightInput) {
        nWeightInput.addEventListener('input', updateTotals);
    }
    
    if (gWeightInput) {
        gWeightInput.addEventListener('input', updateTotals);
    }
    
    // Tab key to add new row - look for field name containing "remark"
    const remarkInput = row.querySelector('input[name*="cargo_items-"][name*="-remark"]');
    if (remarkInput && !remarkInput.hasAttribute('data-tab-listener-added')) {
        remarkInput.setAttribute('data-tab-listener-added', 'true');
        remarkInput.addEventListener('keydown', function(e) {
            if (e.key === 'Tab' && !e.shiftKey) {
                e.preventDefault();
                // Add a small delay to prevent multiple rapid calls
                if (!this.dataset.processing) {
                    this.dataset.processing = 'true';
                    
                    // Add the new row and get a reference to it
                    const newRow = addCargoRow();
                    
                    // Focus on the item select of the new row with better timing
                    setTimeout(() => {
                        if (newRow) {
                            const itemSelect = newRow.querySelector('select[name*="cargo_items-"][name*="-item"]');
                            if (itemSelect) {
                                // Try multiple times to ensure focus works
                                itemSelect.focus();
                                // If focus doesn't work immediately, try again
                                setTimeout(() => {
                                    itemSelect.focus();
                                    // Also try to open the dropdown
                                    if (itemSelect.click) {
                                        itemSelect.click();
                                    }
                                }, 50);
                            }
                        }
                        // Reset the processing flag after a longer delay
                        setTimeout(() => {
                            delete this.dataset.processing;
                        }, 200);
                    }, 50);
                }
            }
        });
    }
    
    // Remove row button
    const removeBtn = row.querySelector('.remove-row-btn');
    if (removeBtn) {
        removeBtn.addEventListener('click', () => removeCargoRow(row));
    }
}

/**
 * Remove a cargo row
 */
function removeCargoRow(row) {
    if (row && row.parentNode) {
        // Check if this is an existing row (has an instance)
        const deleteCheckbox = row.querySelector('input[name*="cargo_items-"][name*="-DELETE"]');
        if (deleteCheckbox) {
            // Mark for deletion and hide the row
            deleteCheckbox.checked = true;
            row.style.display = 'none';
        } else {
            // If it's a new row, just remove it
            row.remove();
        }
        
        // Update the total forms count
        const tbody = document.getElementById('cargoTableBody');
        const totalForms = document.getElementById('id_cargo_items-TOTAL_FORMS');
        if (tbody && totalForms) {
            const visibleRows = tbody.querySelectorAll('tr:not([style*="display: none"])');
            totalForms.value = visibleRows.length;
        }
        
        updateRowNumbers();
        updateTotals();
    }
}

/**
 * Update row numbers in the cargo table
 */
function updateRowNumbers() {
    const rows = document.querySelectorAll('#cargoTableBody tr:not([style*="display: none"])');
    rows.forEach((row, index) => {
        const firstCell = row.querySelector('td:first-child');
        if (firstCell) {
            firstCell.textContent = index + 1;
        }
    });
}

/**
 * Calculate amount for a specific row
 */
function calculateRowAmount(row) {
    const qtyInput = row.querySelector('input[name*="cargo_items-"][name*="-quantity"]');
    const rateInput = row.querySelector('input[name*="cargo_items-"][name*="-rate"]');
    const amountInput = row.querySelector('input[name*="cargo_items-"][name*="-amount"]');
    
    if (qtyInput && rateInput && amountInput) {
        const qty = parseFloat(qtyInput.value) || 0;
        const rate = parseFloat(rateInput.value) || 0;
        const amount = qty * rate;
        amountInput.value = amount.toFixed(2);
        updateTotals();
    }
}

/**
 * Update totals for the entire cargo table
 */
function updateTotals() {
    let totalAmount = 0;
    let totalNWeight = 0;
    let totalGWeight = 0;
    
    const rows = document.querySelectorAll('#cargoTableBody tr:not([style*="display: none"])');
    rows.forEach(row => {
        const amountInput = row.querySelector('input[name*="cargo_items-"][name*="-amount"]');
        const nWeightInput = row.querySelector('input[name*="cargo_items-"][name*="-net_weight"]');
        const gWeightInput = row.querySelector('input[name*="cargo_items-"][name*="-gross_weight"]');
        
        if (amountInput) {
            totalAmount += parseFloat(amountInput.value) || 0;
        }
        if (nWeightInput) {
            totalNWeight += parseFloat(nWeightInput.value) || 0;
        }
        if (gWeightInput) {
            totalGWeight += parseFloat(gWeightInput.value) || 0;
        }
    });
    
    // Update display elements
    const totalAmountElement = document.getElementById('totalAmount');
    if (totalAmountElement) {
        totalAmountElement.textContent = totalAmount.toFixed(2);
    }
    
    const totalNWeightElement = document.getElementById('totalNWeight');
    if (totalNWeightElement) {
        totalNWeightElement.textContent = totalNWeight.toFixed(2);
    }
    
    const totalGWeightElement = document.getElementById('totalGWeight');
    if (totalGWeightElement) {
        totalGWeightElement.textContent = totalGWeight.toFixed(2);
    }
}

/**
 * Populate item dropdown with available items
 */
function populateItemDropdown(selectElement) {
    // Store the current selected value
    const currentValue = selectElement.value;
    
    // Only clear and repopulate if the dropdown is empty or has no items
    if (selectElement.options.length <= 1) {
        // Fetch items from server
        fetch('/job/get-items-list/')
            .then(response => response.json())
            .then(data => {
                if (data.success && data.items) {
                    data.items.forEach(item => {
                        const option = document.createElement('option');
                        option.value = item.id;
                        option.textContent = item.name;
                        selectElement.appendChild(option);
                    });
                    
                    // Restore the selected value if it exists
                    if (currentValue) {
                        selectElement.value = currentValue;
                    }
                }
            })
            .catch(error => {
                console.error('Error fetching items:', error);
            });
    }
}

/**
 * Fetch item data and populate fields
 */
function fetchItemData(itemId, selectElement) {
    const row = selectElement.closest('tr');
    
    fetch(`/job/get-item-data/${itemId}/`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const item = data.item;
                
                // Update item code
                const itemCodeInput = row.querySelector('input[name*="cargo_items-"][name*="-item_code"]');
                if (itemCodeInput) {
                    itemCodeInput.value = item.item_code;
                }
                
                // Update unit if empty
                const unitSelect = row.querySelector('select[name*="cargo_items-"][name*="-unit"]');
                if (unitSelect && !unitSelect.value) {
                    unitSelect.value = item.unit_of_measure;
                }
                
                // Don't auto-populate remark field - let users fill it manually
                // const remarkInput = row.querySelector('input[name*="cargo_items-"][name*="-remark"]');
                // if (remarkInput && !remarkInput.value) {
                //     remarkInput.value = item.description;
                // }
            }
        })
        .catch(error => {
            console.error('Error fetching item data:', error);
        });
}

/**
 * Clear item-related fields when no item is selected
 */
function clearItemFields(selectElement) {
    const row = selectElement.closest('tr');
    
    // Clear item code
    const itemCodeInput = row.querySelector('input[name*="cargo_items-"][name*="-item_code"]');
    if (itemCodeInput) {
        itemCodeInput.value = '';
    }
    
    // Clear unit
    const unitSelect = row.querySelector('select[name*="cargo_items-"][name*="-unit"]');
    if (unitSelect) {
        unitSelect.value = '';
    }
    
    // Clear remark
    const remarkInput = row.querySelector('input[name*="cargo_items-"][name*="-remark"]');
    if (remarkInput) {
        remarkInput.value = '';
    }
}

/**
 * Initialize cargo table functionality
 */
function initializeCargoTable() {
    // Prevent multiple initializations
    if (window.cargoTableInitialized) {
        return;
    }
    window.cargoTableInitialized = true;
    
    // Set up existing rows
    const existingRows = document.querySelectorAll('#cargoTableBody tr');
    existingRows.forEach(row => {
        setupCargoRowEventListeners(row);
    });
    
    // Initialize calculations
    updateTotals();
}

// Global functions for onclick handlers
window.addCargoRow = addCargoRow;
window.removeCargoRow = removeCargoRow;
window.calculateRowAmount = calculateRowAmount;
window.updateTotals = updateTotals;
window.populateItemDropdown = populateItemDropdown;
window.fetchItemData = fetchItemData;
window.clearItemFields = clearItemFields;
window.initializeCargoTable = initializeCargoTable; 