// Supplier Payments JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Auto-format amount field
    const amountField = document.getElementById('payment-amount');
    if (amountField) {
        amountField.addEventListener('input', function(e) {
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
    }

    // Auto-format reference number
    const referenceField = document.getElementById('reference-number');
    if (referenceField) {
        referenceField.addEventListener('input', function(e) {
            // Remove special characters except alphanumeric and common separators
            e.target.value = e.target.value.replace(/[^a-zA-Z0-9\-\_\/]/g, '');
        });
    }

    // Real-time search functionality
    const searchField = document.getElementById('search');
    if (searchField) {
        let searchTimeout;
        searchField.addEventListener('input', function(e) {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(function() {
                // Trigger form submission for search
                const form = searchField.closest('form');
                if (form) {
                    form.submit();
                }
            }, 500);
        });
    }

    // Date range validation
    const dateFromField = document.getElementById('date_from');
    const dateToField = document.getElementById('date_to');
    
    if (dateFromField && dateToField) {
        dateFromField.addEventListener('change', function() {
            if (dateToField.value && this.value > dateToField.value) {
                dateToField.value = this.value;
            }
        });
        
        dateToField.addEventListener('change', function() {
            if (dateFromField.value && this.value < dateFromField.value) {
                dateFromField.value = this.value;
            }
        });
    }

    // Table row selection
    const tableRows = document.querySelectorAll('tbody tr');
    tableRows.forEach(row => {
        row.addEventListener('click', function(e) {
            // Don't trigger if clicking on action buttons
            if (e.target.closest('.btn-group')) {
                return;
            }
            
            // Remove selection from other rows
            tableRows.forEach(r => r.classList.remove('table-active'));
            
            // Add selection to current row
            this.classList.add('table-active');
        });
    });

    // Keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + N for new payment
        if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
            e.preventDefault();
            const newPaymentBtn = document.querySelector('a[href*="create"]');
            if (newPaymentBtn) {
                newPaymentBtn.click();
            }
        }
        
        // Ctrl/Cmd + F for search focus
        if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
            e.preventDefault();
            if (searchField) {
                searchField.focus();
                searchField.select();
            }
        }
    });

    // Form auto-save (localStorage)
    const form = document.getElementById('supplierPaymentForm');
    if (form) {
        const formFields = form.querySelectorAll('input, select, textarea');
        
        // Load saved data (exclude payment date to preserve default current date)
        formFields.forEach(field => {
            // Skip payment date field to preserve the default current date
            if (field.id === 'payment-date') {
                console.log('Skipping payment-date field, current value:', field.value);
                return;
            }
            const savedValue = localStorage.getItem('supplier_payment_' + field.id);
            if (savedValue && !field.value) {
                field.value = savedValue;
            }
        });
        
        // Clear any existing payment date from localStorage
        localStorage.removeItem('supplier_payment_payment-date');
        console.log('Cleared payment-date from localStorage');
        
        // Save data on input (exclude payment date to preserve default current date)
        formFields.forEach(field => {
            field.addEventListener('input', function() {
                // Skip payment date field to preserve the default current date
                if (this.id === 'payment-date') {
                    return;
                }
                localStorage.setItem('supplier_payment_' + this.id, this.value);
            });
        });
        
        // Clear saved data on successful submission and handle selected invoices
        form.addEventListener('submit', function(e) {
            console.log('Form submission started');
            
            // Get selected invoices
            const checkedInvoices = document.querySelectorAll('.invoice-checkbox:checked');
            const selectedInvoices = [];
            const invoiceAmounts = [];
            
            console.log('Found', checkedInvoices.length, 'checked invoices');
            
            checkedInvoices.forEach(checkbox => {
                selectedInvoices.push(checkbox.dataset.invoice);
                invoiceAmounts.push(checkbox.dataset.amount);
                console.log('Adding invoice:', checkbox.dataset.invoice, 'amount:', checkbox.dataset.amount);
            });
            
            // Get selected bills
            const checkedBills = document.querySelectorAll('.bill-checkbox:checked');
            const selectedBills = [];
            const billAmounts = [];
            
            console.log('Found', checkedBills.length, 'checked bills');
            
            checkedBills.forEach(checkbox => {
                selectedBills.push(checkbox.dataset.bill);
                billAmounts.push(checkbox.dataset.amount);
                console.log('Adding bill:', checkbox.dataset.bill, 'amount:', checkbox.dataset.amount);
            });
            
            // Remove existing hidden fields to avoid duplicates
            const existingFields = form.querySelectorAll('input[name="selected_invoices"], input[name="invoice_amounts"], input[name="selected_bills"], input[name="bill_amounts"]');
            console.log('Removing', existingFields.length, 'existing hidden fields');
            existingFields.forEach(field => field.remove());
            
            // Add selected invoices as hidden form fields
            console.log('Adding', selectedInvoices.length, 'invoice hidden fields');
            selectedInvoices.forEach(invoice => {
                const hiddenField = document.createElement('input');
                hiddenField.type = 'hidden';
                hiddenField.name = 'selected_invoices';
                hiddenField.value = invoice;
                form.appendChild(hiddenField);
                console.log('Added hidden field: selected_invoices =', invoice);
            });
            
            // Add invoice amounts as hidden form fields
            console.log('Adding', invoiceAmounts.length, 'invoice amount hidden fields');
            invoiceAmounts.forEach(amount => {
                const hiddenField = document.createElement('input');
                hiddenField.type = 'hidden';
                hiddenField.name = 'invoice_amounts';
                hiddenField.value = amount;
                form.appendChild(hiddenField);
                console.log('Added hidden field: invoice_amounts =', amount);
            });
            
            // Add selected bills as hidden form fields
            console.log('Adding', selectedBills.length, 'bill hidden fields');
            selectedBills.forEach(bill => {
                const hiddenField = document.createElement('input');
                hiddenField.type = 'hidden';
                hiddenField.name = 'selected_bills';
                hiddenField.value = bill;
                form.appendChild(hiddenField);
                console.log('Added hidden field: selected_bills =', bill);
            });
            
            // Add bill amounts as hidden form fields
            console.log('Adding', billAmounts.length, 'bill amount hidden fields');
            billAmounts.forEach(amount => {
                const hiddenField = document.createElement('input');
                hiddenField.type = 'hidden';
                hiddenField.name = 'bill_amounts';
                hiddenField.value = amount;
                form.appendChild(hiddenField);
                console.log('Added hidden field: bill_amounts =', amount);
            });
            
            // Clear saved data
             formFields.forEach(field => {
                 localStorage.removeItem('supplier_payment_' + field.id);
             });
         });
     }

    // Export functionality
    const exportBtn = document.getElementById('exportBtn');
    if (exportBtn) {
        exportBtn.addEventListener('click', function() {
            exportTableToCSV();
        });
    }

    // Supplier selection change handler
    $(document).ready(function() {
        console.log('Document ready, initializing supplier payments JS');
        console.log('jQuery version:', $.fn.jquery);
        console.log('Supplier select element exists:', $('#supplier-select').length > 0);
        
        $('#supplier-select').on('change', function() {
            console.log('Supplier selection changed, value:', this.value);
            const supplierId = this.value;
            console.log('Supplier changed to:', supplierId);
            const pendingInvoicesCard = $('#pendingInvoicesCard');
            const pendingInvoicesBody = $('#pendingInvoicesBody');
            const pendingCount = $('#pendingCount');
            const noInvoicesMessage = $('#noInvoicesMessage');
            if (!supplierId) {
                console.log('No supplier selected, hiding invoice section');
                pendingInvoicesCard.hide();
                pendingInvoicesBody.empty();
                pendingCount.text('0');
                noInvoicesMessage.show();
                $('#invoice-bill-section').hide();
                return;
            }
            console.log('Fetching pending invoices for supplier:', supplierId);
            
            // Check if URLs are available
            if (!window.supplierPaymentUrls || !window.supplierPaymentUrls.getPendingInvoices) {
                console.error('Supplier payment URLs not available');
                $('#invoice-bill-section').hide();
                return;
            }
            
            fetch(window.supplierPaymentUrls.getPendingInvoices + supplierId + '/', {
                method: 'GET',
                credentials: 'same-origin',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Content-Type': 'application/json',
                }
            })
                .then(response => {
                    console.log('Response status:', response.status);
                    return response.json();
                })
                .then(data => {
                    console.log('Response data:', data);
                    // Combine invoices and bills
                    const allItems = [];
                    
                    // Add invoices to the list
                    if (data.invoices && data.invoices.length > 0) {
                        data.invoices.forEach(invoice => {
                            allItems.push({
                                type: 'invoice',
                                ...invoice
                            });
                        });
                    }
                    
                    // Add bills to the list
                    if (data.bills && data.bills.length > 0) {
                        data.bills.forEach(bill => {
                            allItems.push({
                                type: 'bill',
                                ...bill
                            });
                        });
                    }
                    
                    console.log('Total items found:', allItems.length);
                    if (allItems.length > 0) {
                        console.log('Showing pending invoices card with', allItems.length, 'items');
                        pendingInvoicesCard.show();
                        pendingCount.text(allItems.length);
                        noInvoicesMessage.hide();
                        
                        // Show the invoice-bill section
                        $('#invoice-bill-section').show();
                        
                        // Clear existing content
                        pendingInvoicesBody.empty();
                        
                        // Add each item as a row
                        allItems.forEach(item => {
                            const row = $('<tr>');
                            
                            if (item.type === 'invoice') {
                                // Ensure cost_total is properly formatted
                                const costAmount = item.cost_total || '0.00';
                                const formattedCost = typeof costAmount === 'number' ? costAmount.toFixed(2) : costAmount;
                                
                                row.html(
                                    '<td><input type="checkbox" class="form-check-input invoice-checkbox" data-invoice="' + item.invoice_number + '" data-amount="' + formattedCost + '"></td>' +
                                    '<td><strong>' + item.invoice_number + '</strong> <span class="badge bg-primary">Invoice</span></td>' +
                                    '<td>' + (item.job_number || '-') + '</td>' +
                                    '<td>' + (item.customer_name || '-') + '</td>' +
                                    '<td>' + (item.bl_number || '-') + '</td>' +
                                    '<td>' + (item.ed_number || '-') + '</td>' +
                                    '<td>' + (item.container_number || '-') + '</td>' +
                                    '<td>' + item.invoice_date + '</td>' +
                                    '<td><span class="badge bg-success">AED ' + formattedCost + '</span></td>' +
                                    '<td><span class="badge bg-warning">' + item.status + '</span></td>' +
                                    '<td>' +
                                        '<button type="button" class="btn btn-outline-primary btn-sm" onclick="setAmount(\"' + formattedCost + '\")">' +
                                            '<i class="bi bi-cash"></i> Use Amount' +
                                        '</button>' +
                                    '</td>'
                                );
                            } else if (item.type === 'bill') {
                                // Handle supplier bills
                                const billAmount = item.amount || '0.00';
                                const formattedAmount = typeof billAmount === 'number' ? billAmount.toFixed(2) : billAmount;
                                
                                row.html(
                                    '<td><input type="checkbox" class="form-check-input bill-checkbox" data-bill="' + item.bill_number + '" data-amount="' + formattedAmount + '"></td>' +
                                    '<td><strong>' + item.bill_number + '</strong> <span class="badge bg-info">Bill</span></td>' +
                                    '<td>-</td>' +
                                    '<td>' + (item.supplier || '-') + '</td>' +
                                    '<td>-</td>' +
                                    '<td>-</td>' +
                                    '<td>-</td>' +
                                    '<td>' + item.bill_date + '</td>' +
                                    '<td><span class="badge bg-success">AED ' + formattedAmount + '</span></td>' +
                                    '<td><span class="badge bg-warning">' + item.status + '</span></td>' +
                                    '<td>' +
                                        '<button type="button" class="btn btn-outline-primary btn-sm" onclick="setAmount(\"' + formattedAmount + '\")">' +
                                            '<i class="bi bi-cash"></i> Use Amount' +
                                        '</button>' +
                                    '</td>'
                                );
                            }
                            
                            pendingInvoicesBody.append(row);
                        });
                        
                        // Add event listeners for checkboxes
                        setupCheckboxHandlers();
                    } else {
                        console.log('No items found, showing no invoices message');
                        pendingInvoicesCard.show();
                        pendingInvoicesBody.empty();
                        pendingCount.text('0');
                        noInvoicesMessage.show();
                        
                        // Show the invoice-bill section even when no items
                        $('#invoice-bill-section').show();
                    }
                })
                .catch(error => {
                    console.error('Error fetching pending invoices:', error);
                    pendingInvoicesCard.show();
                    pendingInvoicesBody.empty();
                    pendingCount.text('0');
                    noInvoicesMessage.show();
                    
                    // Show the invoice-bill section even on error
                    $('#invoice-bill-section').show();
                });
        });
    });

// Export table to CSV
function exportTableToCSV() {
    const table = document.querySelector('table');
    if (!table) return;
    
    let csv = [];
    const rows = table.querySelectorAll('tr');
    
    for (let i = 0; i < rows.length; i++) {
        let row = [], cols = rows[i].querySelectorAll('td, th');
        
        for (let j = 0; j < cols.length; j++) {
            // Get text content, removing action buttons
            let text = cols[j].textContent.trim();
            if (cols[j].querySelector('.btn-group')) {
                text = ''; // Skip action columns
            }
            row.push('"' + text + '"');
        }
        
        csv.push(row.join(','));
    }
    
    // Download CSV file
    const csvContent = csv.join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', 'supplier_payments.csv');
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// Utility functions
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-AE', {
        style: 'currency',
        currency: 'AED'
    }).format(amount);
}

function formatDate(date) {
    return new Intl.DateTimeFormat('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    }).format(new Date(date));
}

// Show notification
function showNotification(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-' + type + ' alert-dismissible fade show position-fixed';
    alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    alertDiv.innerHTML = message + '<button type="button" class="btn-close" data-bs-dismiss="alert"></button>';
    
    document.body.appendChild(alertDiv);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}

// Helper to set the payment amount from invoice
function setAmount(amount) {
    const amountField = document.getElementById('payment-amount');
    if (amountField) {
        amountField.value = amount;
        amountField.focus();
    }
}

// Setup checkbox handlers
function setupCheckboxHandlers() {
    // Handle "Select All" functionality
    $('#selectAllInvoices').off('change').on('change', function() {
        const isChecked = this.checked;
        $('.invoice-checkbox, .bill-checkbox').prop('checked', isChecked);
        updateSelectedAmount();
        updateSelectAllState();
    });
    
    // Handle individual checkbox changes
    $('.invoice-checkbox, .bill-checkbox').off('change').on('change', function() {
        updateSelectedAmount();
        updateSelectAllState();
    });
}

// Update selected amount based on checked invoices and bills
function updateSelectedAmount() {
    const checkedInvoices = $('.invoice-checkbox:checked');
    const checkedBills = $('.bill-checkbox:checked');
    const allChecked = [...checkedInvoices, ...checkedBills];
    let totalAmount = 0;
    
    allChecked.forEach(checkbox => {
        const amount = parseFloat($(checkbox).data('amount')) || 0;
        totalAmount += amount;
    });
    
    const amountField = $('#payment-amount');
    if (amountField.length) {
        amountField.val(totalAmount.toFixed(2));
    }
    
    // Show notification with selected count
    if (allChecked.length > 0) {
        const invoiceCount = checkedInvoices.length;
        const billCount = checkedBills.length;
        let message = '';
        if (invoiceCount > 0 && billCount > 0) {
            message = invoiceCount + ' invoice(s) and ' + billCount + ' bill(s) selected. Total: AED ' + totalAmount.toFixed(2);
        } else if (invoiceCount > 0) {
            message = invoiceCount + ' invoice(s) selected. Total: AED ' + totalAmount.toFixed(2);
        } else {
            message = billCount + ' bill(s) selected. Total: AED ' + totalAmount.toFixed(2);
        }
        showNotification(message, 'info');
    }
}

// Update select all checkbox state
function updateSelectAllState() {
    const selectAllCheckbox = $('#selectAllInvoices');
    const invoiceCheckboxes = $('.invoice-checkbox');
    const billCheckboxes = $('.bill-checkbox');
    const allCheckboxes = [...invoiceCheckboxes, ...billCheckboxes];
    const checkedInvoices = $('.invoice-checkbox:checked');
    const checkedBills = $('.bill-checkbox:checked');
    const allChecked = [...checkedInvoices, ...checkedBills];
    
    if (selectAllCheckbox.length) {
        if (allChecked.length === 0) {
            selectAllCheckbox.prop('indeterminate', false);
            selectAllCheckbox.prop('checked', false);
        } else if (allChecked.length === allCheckboxes.length) {
            selectAllCheckbox.prop('indeterminate', false);
            selectAllCheckbox.prop('checked', true);
        } else {
            selectAllCheckbox.prop('indeterminate', true);
            selectAllCheckbox.prop('checked', false);
        }
    }
}

// Note: updateHiddenInputs function removed as it was unused and had incorrect field naming
// The correct form submission logic is handled in the form.addEventListener('submit') handler above

// Calculate total of selected invoices and bills
function calculateSelectedTotal() {
    const checkedInvoices = $('.invoice-checkbox:checked');
    const checkedBills = $('.bill-checkbox:checked');
    
    if (checkedInvoices.length === 0 && checkedBills.length === 0) {
        showNotification('Please select at least one invoice or bill to calculate total', 'warning');
        return;
    }
    
    let totalAmount = 0;
    const selectedItems = [];
    
    checkedInvoices.each(function() {
        const amount = parseFloat($(this).data('amount')) || 0;
        const invoiceNumber = $(this).data('invoice');
        selectedItems.push('Invoice: ' + invoiceNumber);
        totalAmount += amount;
    });
    
    checkedBills.each(function() {
        const amount = parseFloat($(this).data('amount')) || 0;
        const billNumber = $(this).data('bill');
        selectedItems.push('Bill: ' + billNumber);
        totalAmount += amount;
    });
    
    const amountField = $('#payment-amount');
    if (amountField.length) {
        amountField.val(totalAmount.toFixed(2));
        amountField.focus();
    }
    
    const invoiceCount = checkedInvoices.length;
    const billCount = checkedBills.length;
    let message = 'Total calculated: AED ' + totalAmount.toFixed(2) + ' for ';
    if (invoiceCount > 0 && billCount > 0) {
        message += invoiceCount + ' invoice(s) and ' + billCount + ' bill(s)';
    } else if (invoiceCount > 0) {
        message += invoiceCount + ' invoice(s)';
    } else {
        message += billCount + ' bill(s)';
    }
    
    showNotification(message, 'success');
}

// Payment method change handler for ledger account filtering
function initializeLedgerAccountFiltering() {
    const paymentMethodSelect = document.getElementById('payment-method');
    const ledgerAccountSelect = document.getElementById('ledger-account');
    
    console.log('Initializing ledger account filtering...');
    console.log('Payment method select element:', paymentMethodSelect);
    console.log('Ledger account select element:', ledgerAccountSelect);
    
    // Try alternative selectors if primary ones fail
    if (!ledgerAccountSelect) {
        const alternativeSelectors = [
            'select[name="ledger_account"]',
            '#id_ledger_account',
            'select[id*="ledger"]'
        ];
        
        for (const selector of alternativeSelectors) {
            const element = document.querySelector(selector);
            if (element) {
                console.log(`Found ledger account element with selector: ${selector}`, element);
                break;
            }
        }
    }
    
    if (paymentMethodSelect && ledgerAccountSelect) {
        console.log('Both elements found, setting up event listener');
        paymentMethodSelect.addEventListener('change', function() {
            const paymentMethod = this.value;
            console.log('Payment method changed to:', paymentMethod);
            
            if (paymentMethod) {
                filterLedgerAccounts(paymentMethod);
            } else {
                // Reset to show all accounts if no payment method selected
                loadAllLedgerAccounts();
            }
        });
    } else {
        console.error('Missing elements - Payment method:', !!paymentMethodSelect, 'Ledger account:', !!ledgerAccountSelect);
        
        // Log all select elements for debugging
        const allSelects = document.querySelectorAll('select');
        console.log('All select elements on page:', allSelects);
        allSelects.forEach((select, index) => {
            console.log(`Select ${index}: ID='${select.id}', Name='${select.name}', Classes='${select.className}'`);
        });
        
        // Try to find the ledger account element with different approaches
        console.log('Searching for ledger account element...');
        const byId = document.getElementById('ledger-account');
        const byName = document.querySelector('select[name="ledger_account"]');
        const byIdAlt = document.getElementById('id_ledger_account');
        const byClass = document.querySelector('.form-control[name="ledger_account"]');
        
        console.log('By ID (ledger-account):', byId);
        console.log('By name (ledger_account):', byName);
        console.log('By ID alt (id_ledger_account):', byIdAlt);
        console.log('By class + name:', byClass);
        
        // Check if the element exists but is hidden
        if (byName) {
            const styles = window.getComputedStyle(byName);
            console.log('Ledger account element styles:', {
                display: styles.display,
                visibility: styles.visibility,
                opacity: styles.opacity,
                height: styles.height,
                width: styles.width
            });
        }
    }
}

// Initialize when DOM is ready
console.log('Document ready state:', document.readyState);
console.log('DOM elements at script load:', document.querySelectorAll('select').length);

// Immediate debug check
console.log('=== IMMEDIATE DEBUG CHECK ===');
console.log('All select elements:');
document.querySelectorAll('select').forEach((select, index) => {
    console.log(`Select ${index}: ID='${select.id}', Name='${select.name}', Classes='${select.className}', HTML:`, select.outerHTML.substring(0, 200));
});
console.log('=== END IMMEDIATE DEBUG ===');

// Retry mechanism with multiple attempts
let retryCount = 0;
const maxRetries = 5;

function retryInitialization() {
    retryCount++;
    console.log(`Retry attempt ${retryCount}/${maxRetries}`);
    
    // Debug: Log current page URL and title
    console.log('Current page URL:', window.location.href);
    console.log('Current page title:', document.title);
    
    // Check if we're on the correct page (supplier payment form)
    if (!window.location.href.includes('supplier-payments/create') && !window.location.href.includes('supplier-payments') && !document.title.toLowerCase().includes('supplier payment')) {
        console.log('Not on supplier payment page, skipping initialization');
        return false;
    }
    
    // Check if we're on a login page
    if (document.title.toLowerCase().includes('login') || window.location.href.includes('/login/')) {
        console.log('On login page, skipping supplier payment initialization');
        return false;
    }
    
    const paymentMethodSelect = document.getElementById('payment-method') || document.querySelector('select[name="payment_method"]');
    const ledgerAccountSelect = document.getElementById('ledger-account') || 
                               document.querySelector('select[name="ledger_account"]') ||
                               document.getElementById('id_ledger_account');
    
    console.log('Payment method element found:', !!paymentMethodSelect);
    console.log('Ledger account element found:', !!ledgerAccountSelect);
    
    if (paymentMethodSelect && ledgerAccountSelect) {
        console.log('Both elements found on retry, setting up event listener');
        paymentMethodSelect.addEventListener('change', function() {
            const paymentMethod = this.value;
            console.log('Payment method changed to:', paymentMethod);
            
            if (paymentMethod) {
                filterLedgerAccounts(paymentMethod);
            } else {
                loadAllLedgerAccounts();
            }
        });
        return true; // Success
    } else if (retryCount < maxRetries) {
        setTimeout(retryInitialization, 500 * retryCount); // Increasing delay
        return false;
    } else {
        console.warn('Failed to find elements after all retries - this may be expected if not on supplier payment form page');
        console.log('Final check - all select elements:');
        document.querySelectorAll('select').forEach((select, index) => {
            console.log(`Select ${index}: ID='${select.id}', Name='${select.name}', Classes='${select.className}'`);
        });
        return false;
    }
}

// Use window.onload to ensure all resources are fully loaded
if (document.readyState === 'complete') {
    console.log('Page already fully loaded, initializing immediately');
    setTimeout(retryInitialization, 50);
} else {
    console.log('Waiting for window load event');
    window.addEventListener('load', function() {
        console.log('Window load event fired, select elements:', document.querySelectorAll('select').length);
        setTimeout(retryInitialization, 50);
    });
    
    // Also listen for DOMContentLoaded as fallback
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            console.log('DOMContentLoaded fired as fallback');
            setTimeout(retryInitialization, 200);
        });
    }
}

// Function to get CSRF token
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

// Function to filter ledger accounts based on payment method
function filterLedgerAccounts(paymentMethod) {
    const ledgerAccountSelect = document.getElementById('ledger-account') || 
                               document.querySelector('select[name="ledger_account"]') ||
                               document.getElementById('id_ledger_account');
    
    if (!ledgerAccountSelect) {
        console.error('Ledger account select element not found in filterLedgerAccounts');
        return;
    }
    
    console.log('Filtering ledger accounts for payment method:', paymentMethod);
    
    // Check if URLs are available
    if (!window.supplierPaymentUrls || !window.supplierPaymentUrls.filterLedgerAccounts) {
        console.error('Supplier payment URLs not available for filtering ledger accounts');
        return;
    }
    
    // Make AJAX call to get filtered ledger accounts
    fetch(window.supplierPaymentUrls.filterLedgerAccounts, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            'payment_method': paymentMethod
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Clear existing options except the first one (empty option)
            const firstOption = ledgerAccountSelect.options[0];
            ledgerAccountSelect.innerHTML = '';
            if (firstOption) {
                ledgerAccountSelect.appendChild(firstOption);
            }
            
            // Add filtered options
            let cashAccountFound = false;
            data.accounts.forEach(account => {
                const option = document.createElement('option');
                option.value = account.id;
                option.textContent = `${account.account_code} - ${account.name}`;
                ledgerAccountSelect.appendChild(option);
                
                // Auto-select "1000 - Cash" for cash payment method
                if (paymentMethod === 'cash' && account.account_code === '1000' && account.name.toLowerCase().includes('cash')) {
                    option.selected = true;
                    cashAccountFound = true;
                }
            });
            
            if (paymentMethod === 'cash') {
                if (cashAccountFound) {
                    console.log('Auto-selected 1000 - Cash account for cash payment');
                }
                console.log(`Loaded ${data.accounts.length} cash ledger accounts`);
            } else if (paymentMethod === 'bank_transfer') {
                console.log(`Loaded ${data.accounts.length} bank ledger accounts`);
            } else {
                console.log(`Loaded ${data.accounts.length} ledger accounts for ${paymentMethod}`);
            }
        } else {
            console.error('Error filtering ledger accounts:', data.error);
        }
    })
    .catch(error => {
        console.error('Error filtering ledger accounts:', error);
    });
}

// Function to load all ledger accounts
function loadAllLedgerAccounts() {
    const ledgerAccountSelect = document.getElementById('ledger-account') || 
                               document.querySelector('select[name="ledger_account"]') ||
                               document.getElementById('id_ledger_account');
    
    if (!ledgerAccountSelect) {
        console.error('Ledger account select element not found in loadAllLedgerAccounts');
        return;
    }
    
    // Check if URLs are available
    if (!window.supplierPaymentUrls || !window.supplierPaymentUrls.allLedgerAccounts) {
        console.error('Supplier payment URLs not available for loading all ledger accounts');
        return;
    }
    
    fetch(window.supplierPaymentUrls.allLedgerAccounts, {
        method: 'GET',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Clear existing options except the first one (empty option)
            const firstOption = ledgerAccountSelect.options[0];
            ledgerAccountSelect.innerHTML = '';
            if (firstOption) {
                ledgerAccountSelect.appendChild(firstOption);
            }
            
            // Add all options
            data.accounts.forEach(account => {
                const option = document.createElement('option');
                option.value = account.id;
                option.textContent = `${account.account_code} - ${account.name}`;
                ledgerAccountSelect.appendChild(option);
            });
            
            console.log(`Loaded ${data.accounts.length} total ledger accounts`);
        } else {
            console.error('Error loading ledger accounts:', data.error);
        }
    })
    .catch(error => {
        console.error('Error loading ledger accounts:', error);
    });
}

}); // End of DOMContentLoaded