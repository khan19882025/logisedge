// Customer Payments JavaScript

// Function to get CSRF token from cookies
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

// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('Customer payments page loaded');
    
    // Initialize DOM elements
    const paymentForm = document.getElementById('payment-form');
    const customerSelect = document.getElementById('id_customer');
    const invoicesContainer = document.querySelector('#invoice-list-table tbody');
    const invoiceSection = document.getElementById('invoice-list-section');
    const paymentDateInput = document.getElementById('id_payment_date');
    const paymentAmountInput = document.getElementById('id_amount');
    const paymentMethodSelect = document.getElementById('id_payment_method');
    const ledgerAccountSelect = document.getElementById('id_ledger_account');
    const bankAccountSection = document.getElementById('bank-account-section');
    const referenceNumberInput = document.getElementById('id_reference_number');
    const notesTextarea = document.getElementById('id_notes');
    const submitButton = document.getElementById('save-payment-btn');
    const totalSelectedSpan = document.getElementById('total-invoice-amount');
    const totalPaymentSpan = document.getElementById('amount-received');
    const remainingAmountSpan = document.getElementById('remaining-amount');
    
    // Debug: Check if all elements are found
    console.log('DOM Elements Check:', {
        paymentForm: !!paymentForm,
        customerSelect: !!customerSelect,
        invoicesContainer: !!invoicesContainer,
        paymentDateInput: !!paymentDateInput,
        paymentAmountInput: !!paymentAmountInput,
        paymentMethodSelect: !!paymentMethodSelect,
        ledgerAccountSelect: !!ledgerAccountSelect,
        bankAccountSection: !!bankAccountSection,
        referenceNumberInput: !!referenceNumberInput,
        notesTextarea: !!notesTextarea,
        submitButton: !!submitButton,
        totalSelectedSpan: !!totalSelectedSpan,
        totalPaymentSpan: !!totalPaymentSpan,
        remainingAmountSpan: !!remainingAmountSpan
    });
    
    // Initialize payment date to today if not set
    if (paymentDateInput && !paymentDateInput.value) {
        const today = new Date().toISOString().split('T')[0];
        paymentDateInput.value = today;
    }
    
    // Customer selection change handler
    if (customerSelect) {
        customerSelect.addEventListener('change', function() {
            const customerId = this.value;
            console.log('Customer selected:', customerId);
            
            // Reset payment amount user modification flag when customer changes
            const paymentAmountInput = document.getElementById('id_amount');
            if (paymentAmountInput) {
                delete paymentAmountInput.dataset.userModified;
                paymentAmountInput.value = '';
            }
            
            if (customerId) {
                loadCustomerInvoices(customerId);
            } else {
                hideInvoiceSection();
                clearInvoiceList();
            }
        });
    }
    
    // Add event listener for payment method selection
    if (paymentMethodSelect) {
        paymentMethodSelect.addEventListener('change', function() {
            const paymentMethod = this.value;
            console.log('Payment method selected:', paymentMethod);
            
            // Show/hide bank account section
            if (bankAccountSection) {
                if (paymentMethod === 'bank') {
                    bankAccountSection.style.display = 'block';
                } else {
                    bankAccountSection.style.display = 'none';
                }
            }
            
            // Filter ledger accounts based on payment method
            filterLedgerAccounts(paymentMethod);
        });
        
        // Trigger change event on page load to set initial state
        paymentMethodSelect.dispatchEvent(new Event('change'));
    }
    
    // Payment amount input handler
        if (paymentAmountInput) {
            paymentAmountInput.addEventListener('input', function() {
                // Mark that user has manually modified the payment amount
                this.dataset.userModified = 'true';
                
                if (window.updatePaymentSummary) {
                    window.updatePaymentSummary();
                }
            });
        }
    
    // Form submission handler
    if (paymentForm) {
        paymentForm.addEventListener('submit', function(e) {
            e.preventDefault();
            console.log('Form submission attempted');
            
            if (validatePaymentForm()) {
                submitPayment();
            }
        });
    }
    
    // Load customer invoices
    function loadCustomerInvoices(customerId) {
        console.log('Loading invoices for customer:', customerId);
        
        if (!invoicesContainer) {
            console.error('Invoices container not found');
            return;
        }
        
        // Show loading state
        invoicesContainer.innerHTML = '<div class="text-center p-3"><div class="spinner-border" role="status"><span class="visually-hidden">Loading...</span></div></div>';
        
        // Fetch invoices from server
        const formData = new FormData();
        formData.append('customer_id', customerId);
        
        fetch('/accounting/customer-payments/ajax/customer-invoices/', {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Invoices loaded:', data);
            displayInvoices(data.invoices);
            showInvoiceSection();
        })
        .catch(error => {
            console.error('Error loading invoices:', error);
            invoicesContainer.innerHTML = '<div class="alert alert-danger">Error loading invoices. Please try again.</div>';
        });
    }
    
    // Display invoices in the container
    function displayInvoices(invoices) {
        if (!invoicesContainer) {
            console.error('Invoice container (tbody) not found');
            return;
        }
        
        if (!invoices || invoices.length === 0) {
            invoicesContainer.innerHTML = '<tr><td colspan="9" class="text-center">No outstanding invoices found for this customer.</td></tr>';
            return;
        }
        
        // Filter out invoices with zero or no balance due
        const invoicesWithBalance = invoices.filter(invoice => {
            const balance = parseFloat(invoice.balance_amount || invoice.balance || 0);
            return balance > 0;
        });
        
        if (invoicesWithBalance.length === 0) {
            invoicesContainer.innerHTML = '<tr><td colspan="9" class="text-center">No outstanding invoices found for this customer.</td></tr>';
            return;
        }
        
        let html = '';
        
        invoicesWithBalance.forEach(invoice => {
            html += createInvoiceRow(invoice);
        });
        
        invoicesContainer.innerHTML = html;
        
        // Reset select-all checkbox to unchecked
        const selectAllCheckbox = document.getElementById('select-all-invoices');
        if (selectAllCheckbox) {
            selectAllCheckbox.checked = false;
        }
        
        // Add event listeners to checkboxes
        const checkboxes = invoicesContainer.querySelectorAll('input[name="invoices"]');
        checkboxes.forEach(checkbox => {
            checkbox.addEventListener('change', function() {
                toggleInvoiceSelection(this);
            });
        });
        
        // Add event listeners to amount inputs
        const amountInputs = invoicesContainer.querySelectorAll('input[name="invoice_amounts"]');
        amountInputs.forEach(input => {
            input.addEventListener('input', function() {
                handleInvoiceAmountChange(this);
            });
        });
        
        // Add event listener for select-all checkbox
        if (selectAllCheckbox) {
            selectAllCheckbox.addEventListener('change', function() {
                const checkboxes = document.querySelectorAll('input[name="invoices"]:not(:disabled)');
                checkboxes.forEach(checkbox => {
                    checkbox.checked = this.checked;
                    toggleInvoiceSelection(checkbox);
                });
            });
        }
    }
    
    // Create HTML for a single invoice row
    function createInvoiceRow(invoice) {
        const balance = parseFloat(invoice.balance_amount || invoice.balance || 0);
        
        // Determine status badge class
        let statusClass = 'bg-success';
        if (invoice.status === 'pending') statusClass = 'bg-warning';
        else if (invoice.status === 'overdue') statusClass = 'bg-danger';
        else if (invoice.status === 'partial') statusClass = 'bg-info';
        
        return `
            <tr>
                <td>
                    <input type="checkbox" 
                           name="invoices" 
                           value="${invoice.id}" 
                           data-amount="${balance}">
                </td>
                <td><strong>${invoice.number || invoice.invoice_number}</strong></td>
                <td>${invoice.date || invoice.invoice_date}</td>
                <td>
                    <small class="text-muted">
                        ${invoice.items || invoice.items_summary || 'Multiple items'}
                    </small>
                </td>
                <td>AED ${parseFloat(invoice.amount || invoice.total_amount || 0).toFixed(2)}</td>
                <td>AED ${parseFloat(invoice.paid_amount || 0).toFixed(2)}</td>
                <td>
                    <span class="text-danger fw-bold">
                        AED ${balance.toFixed(2)}
                    </span>
                </td>
                <td>
                    <span class="badge ${statusClass}">
                        ${invoice.status.charAt(0).toUpperCase() + invoice.status.slice(1)}
                    </span>
                </td>
                <td>
                    <input type="number" 
                           name="invoice_amounts" 
                           class="form-control form-control-sm" 
                           min="0" 
                           max="${balance}" 
                           step="0.01" 
                           placeholder="0.00"
                           style="width:100px;"
                           disabled
                           onchange="handleInvoiceAmountChange(this)">
                </td>
            </tr>
        `;
    }
    
    console.log('Checkbox verified');
    
    // Show invoice section
    function showInvoiceSection() {
        const section = document.getElementById('invoice-list-section');
        if (section) {
            section.style.display = 'block';
        }
    }
    
    // Hide invoice section
    function hideInvoiceSection() {
        const section = document.getElementById('invoice-list-section');
        if (section) {
            section.style.display = 'none';
        }
        
        // Reset payment summary
        if (window.updatePaymentSummary) {
            window.updatePaymentSummary();
        }
    }
    
    // Toggle invoice selection
    function toggleInvoiceSelection(checkbox) {
        const row = checkbox.closest('tr');
        const amountInput = row.querySelector('input[name="invoice_amounts"]');
        const invoiceBalance = parseFloat(checkbox.dataset.amount);
        
        if (checkbox.checked) {
            // Enable amount input and auto-populate with balance
            amountInput.disabled = false;
            if (!amountInput.value || parseFloat(amountInput.value) === 0) {
                amountInput.value = invoiceBalance.toFixed(2);
            }
        } else {
            // Disable amount input and clear value
            amountInput.disabled = true;
            amountInput.value = '';
        }
        
        if (window.updatePaymentSummary) {
            window.updatePaymentSummary();
        }
    }
    
    // Update payment summary (moved to global scope)
    window.updatePaymentSummary = function() {
        const selectedCheckboxes = document.querySelectorAll('input[name="invoices"]:checked');
        let totalSelected = 0;
        
        // Calculate total from selected invoices
        selectedCheckboxes.forEach(checkbox => {
            const row = checkbox.closest('tr');
            const amountInput = row.querySelector('input[name="invoice_amounts"]');
            const amount = parseFloat(amountInput.value) || 0;
            totalSelected += amount;
        });
        
        // Update display
        const totalSelectedSpan = document.getElementById('total-invoice-amount');
        if (totalSelectedSpan) {
            totalSelectedSpan.textContent = 'AED ' + totalSelected.toFixed(2);
        }
        
        // Auto-populate payment amount with total selected amount (but keep it editable)
        const paymentAmountInput = document.getElementById('id_amount');
        if (paymentAmountInput && selectedCheckboxes.length > 0) {
            // Only auto-populate if the field is empty or if user hasn't manually modified it
            const currentValue = parseFloat(paymentAmountInput.value) || 0;
            if (currentValue === 0 || !paymentAmountInput.dataset.userModified) {
                paymentAmountInput.value = totalSelected.toFixed(2);
            }
        }
        
        // Get payment amount
        const paymentAmount = parseFloat(paymentAmountInput?.value) || 0;
        const totalPaymentSpan = document.getElementById('amount-received');
        if (totalPaymentSpan) {
            totalPaymentSpan.textContent = 'AED ' + paymentAmount.toFixed(2);
        }
        
        // Calculate remaining amount
        const remainingAmount = totalSelected - paymentAmount;
        if (remainingAmountSpan) {
            remainingAmountSpan.textContent = 'AED ' + remainingAmount.toFixed(2);
            
            // Update color based on remaining amount
            if (remainingAmount > 0) {
                remainingAmountSpan.className = 'text-success fw-bold';
            } else if (remainingAmount < 0) {
                remainingAmountSpan.className = 'text-danger fw-bold';
            } else {
                remainingAmountSpan.className = 'text-muted';
            }
        }
        
        // Show/hide remaining balances section and partial payment options
        if (selectedCheckboxes.length > 0) {
            showRemainingBalances();
            showPartialPaymentOptions();
        } else {
            const remainingBalancesSection = document.getElementById('remaining-balances-section');
            const partialPaymentSection = document.getElementById('partial-payment-section');
            if (remainingBalancesSection) {
                remainingBalancesSection.style.display = 'none';
            }
            if (partialPaymentSection) {
                partialPaymentSection.style.display = 'none';
            }
        }
    }
    
    // Validate payment form
    function validatePaymentForm() {
        console.log('Validating payment form');
        
        // Check if customer is selected
        if (!customerSelect?.value) {
            alert('Please select a customer.');
            return false;
        }
        
        // Check if at least one invoice is selected
        const selectedInvoices = document.querySelectorAll('input[name="invoices"]:checked');
        if (selectedInvoices.length === 0) {
            alert('Please select at least one invoice.');
            return false;
        }
        
        // Check if payment amount is valid
        const paymentAmount = parseFloat(paymentAmountInput?.value) || 0;
        if (paymentAmount <= 0) {
            alert('Please enter a valid payment amount.');
            return false;
        }
        
        // Check if payment method is selected
        if (!paymentMethodSelect?.value) {
            alert('Please select a payment method.');
            return false;
        }
        
        // Validate individual invoice amounts
        let totalInvoiceAmounts = 0;
        let hasValidAmounts = true;
        
        selectedInvoices.forEach(checkbox => {
            const row = checkbox.closest('tr');
            const amountInput = row.querySelector('input[name="invoice_amounts"]');
            const amount = parseFloat(amountInput.value) || 0;
            const maxAmount = parseFloat(checkbox.dataset.amount);
            
            if (amount <= 0) {
                hasValidAmounts = false;
                alert(`Please enter a valid amount for invoice ${row.querySelector('td:nth-child(2) strong').textContent}`);
                return;
            }
            
            if (amount > maxAmount) {
                hasValidAmounts = false;
                alert(`Amount for invoice ${row.querySelector('td:nth-child(2) strong').textContent} cannot exceed the balance of AED ${maxAmount.toFixed(2)}`);
                return;
            }
            
            totalInvoiceAmounts += amount;
        });
        
        if (!hasValidAmounts) {
            return false;
        }
        
        // Check if total invoice amounts don't exceed payment amount
        if (totalInvoiceAmounts > paymentAmount) {
            alert(`Total invoice amounts (AED ${totalInvoiceAmounts.toFixed(2)}) cannot exceed the payment amount (AED ${paymentAmount.toFixed(2)})`);
            return false;
        }
        
        return true;
    }
    
    // Submit payment
    function submitPayment() {
        console.log('Submitting payment');
        
        if (!submitButton) return;
        
        // Disable submit button to prevent double submission
        submitButton.disabled = true;
        submitButton.textContent = 'Processing...';
        
        // Collect form data
        const formData = new FormData();
        formData.append('customer', customerSelect?.value || '');
        formData.append('payment_date', paymentDateInput?.value || '');
        formData.append('amount', paymentAmountInput?.value || '');
        formData.append('payment_method', paymentMethodSelect?.value || '');
        formData.append('ledger_account', ledgerAccountSelect?.value || '');
        
        // Add bank account if payment method is bank
        const bankAccountSelect = document.getElementById('id_bank_account');
        if (bankAccountSelect && paymentMethodSelect?.value === 'bank') {
            formData.append('bank_account', bankAccountSelect.value || '');
        }
        
        formData.append('reference_number', referenceNumberInput?.value || '');
        formData.append('notes', notesTextarea?.value || '');
        
        // Collect partial payment option
        const partialPaymentOption = document.querySelector('input[name="partial_payment_option"]:checked');
        if (partialPaymentOption) {
            formData.append('partial_payment_option', partialPaymentOption.value);
        }
        
        // Collect selected invoices and amounts
        const selectedCheckboxes = document.querySelectorAll('input[name="invoices"]:checked');
        selectedCheckboxes.forEach(checkbox => {
            const row = checkbox.closest('tr');
            const amountInput = row.querySelector('input[name="invoice_amounts"]');
            
            // Add invoice ID and amount as separate form fields
            formData.append('invoices', checkbox.value);
            formData.append('invoice_amounts', amountInput.value || '0');
        });
        
        // Add CSRF token
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
        if (csrfToken) {
            formData.append('csrfmiddlewaretoken', csrfToken);
        }
        
        // Submit to server
        fetch('/accounting/customer-payments/create/', {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
            }
        })
        .then(response => {
            // Check if response is ok and content type is JSON
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const contentType = response.headers.get('content-type');
            if (!contentType || !contentType.includes('application/json')) {
                throw new Error('Server returned non-JSON response');
            }
            
            return response.json();
        })
        .then(data => {
            if (data.success) {
                alert('Payment recorded successfully!');
                // Redirect to payments list or reload page
                window.location.href = '/accounting/customer-payments/';
            } else {
                // Handle form validation errors
                if (data.form_errors) {
                    let errorMessage = 'Form validation failed:\n';
                    for (const [field, errors] of Object.entries(data.form_errors)) {
                        errorMessage += `${field}: ${errors.join(', ')}\n`;
                    }
                    alert(errorMessage);
                } else {
                    alert('Error: ' + (data.error || 'Unknown error occurred'));
                }
            }
        })
        .catch(error => {
            console.error('Error submitting payment:', error);
            alert('Error submitting payment. Please try again.');
        })
        .finally(() => {
            // Re-enable submit button
            submitButton.disabled = false;
            submitButton.textContent = 'Record Payment';
        });
    }
    
    // Global functions for button clicks
    window.selectAllInvoices = function() {
        const checkboxes = document.querySelectorAll('input[name="invoices"]:not(:disabled)');
        checkboxes.forEach(checkbox => {
            if (!checkbox.checked) {
                checkbox.checked = true;
                toggleInvoiceSelection(checkbox);
            }
        });
    };
    
    window.deselectAllInvoices = function() {
        const checkboxes = document.querySelectorAll('input[name="invoices"]:checked');
        checkboxes.forEach(checkbox => {
            checkbox.checked = false;
            toggleInvoiceSelection(checkbox);
        });
    };
    
    window.distributePaymentAmount = function() {
        const paymentAmount = parseFloat(paymentAmountInput?.value) || 0;
        if (paymentAmount <= 0) {
            alert('Please enter a payment amount first.');
            return;
        }
        
        const selectedCheckboxes = document.querySelectorAll('input[name="invoices"]:checked');
        if (selectedCheckboxes.length === 0) {
            alert('Please select at least one invoice first.');
            return;
        }
        
        let remainingAmount = paymentAmount;
        let processedInvoices = 0;
        
        // Distribute payment across selected invoices
        selectedCheckboxes.forEach(checkbox => {
            if (remainingAmount <= 0) return;
            
            const row = checkbox.closest('tr');
            const amountInput = row.querySelector('input[name="invoice_amounts"]');
            const invoiceBalance = parseFloat(checkbox.dataset.amount);
            
            // Calculate amount to allocate to this invoice
            const amountToAllocate = Math.min(remainingAmount, invoiceBalance);
            
            amountInput.value = amountToAllocate.toFixed(2);
            remainingAmount -= amountToAllocate;
            amountInput.disabled = false;
            processedInvoices++;
        });
        
        console.log(`Distributed AED ${paymentAmount - remainingAmount} across ${processedInvoices} invoices`);
        
        // Update the payment summary after distribution
        if (window.updatePaymentSummary) {
            window.updatePaymentSummary();
        }
    }
    
    function showRemainingBalances() {
        const remainingBalancesSection = document.getElementById('remaining-balances-section');
        const remainingBalancesList = document.getElementById('remaining-balances-list');
        
        if (!remainingBalancesSection || !remainingBalancesList) return;
        
        remainingBalancesSection.style.display = 'block';
        
        let html = '';
        let totalRemaining = 0;
        
        const selectedCheckboxes = document.querySelectorAll('input[name="invoices"]:checked');
        selectedCheckboxes.forEach(checkbox => {
            const row = checkbox.closest('tr');
            const invoiceNumber = row.querySelector('td:nth-child(2) strong')?.textContent || 'Unknown';
            const invoiceBalance = parseFloat(checkbox.dataset.amount);
            const amountToPay = parseFloat(row.querySelector('input[name="invoice_amounts"]')?.value) || 0;
            
            // Calculate remaining balance after this payment
            const remainingBalance = invoiceBalance - amountToPay;
            totalRemaining += Math.max(0, remainingBalance);
            
            if (remainingBalance > 0) {
                html += `
                    <div class="mb-2">
                        <strong>${invoiceNumber}:</strong>
                        <span class="text-danger">AED ${remainingBalance.toFixed(2)} remaining</span>
                    </div>
                `;
            } else {
                html += `
                    <div class="mb-2">
                        <strong>${invoiceNumber}:</strong>
                        <span class="text-success">Fully paid</span>
                    </div>
                `;
            }
        });
        
        if (totalRemaining > 0) {
            html += `
                <hr>
                <div class="fw-bold text-danger">
                    Total Remaining: AED ${totalRemaining.toFixed(2)}
                </div>
                <small class="text-muted">This amount will be available for future payments.</small>
            `;
        } else {
            html += `
                <hr>
                <div class="fw-bold text-success">
                    All selected invoices will be fully paid!
                </div>
            `;
        }
        
        remainingBalancesList.innerHTML = html;
    }
    
    function showPartialPaymentOptions() {
        const partialPaymentSection = document.getElementById('partial-payment-section');
        if (!partialPaymentSection) return;
        
        // Check if any invoice has partial payment (amount to pay < invoice balance)
        const selectedCheckboxes = document.querySelectorAll('input[name="invoices"]:checked');
        let hasPartialPayment = false;
        
        selectedCheckboxes.forEach(checkbox => {
            const row = checkbox.closest('tr');
            const invoiceBalance = parseFloat(checkbox.dataset.amount);
            const amountToPay = parseFloat(row.querySelector('input[name="invoice_amounts"]')?.value) || 0;
            
            if (amountToPay > 0 && amountToPay < invoiceBalance) {
                hasPartialPayment = true;
            }
        });
        
        if (hasPartialPayment) {
            partialPaymentSection.style.display = 'block';
        } else {
            partialPaymentSection.style.display = 'none';
        }
    }
    
    // Function to filter ledger accounts based on payment method
    function filterLedgerAccounts(paymentMethod) {
        if (!ledgerAccountSelect) return;
        
        console.log('Filtering ledger accounts for payment method:', paymentMethod);
        
        // Make AJAX call to get filtered ledger accounts
        fetch('/accounting/customer-payments/ajax/filter-ledger-accounts/', {
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
                data.accounts.forEach(account => {
                    const option = document.createElement('option');
                    option.value = account.id;
                    option.textContent = `${account.account_code} - ${account.name}`;
                    ledgerAccountSelect.appendChild(option);
                });
                
                console.log(`Loaded ${data.accounts.length} ledger accounts for ${paymentMethod}`);
            } else {
                console.error('Error filtering ledger accounts:', data.error);
            }
        })
        .catch(error => {
            console.error('Error filtering ledger accounts:', error);
        });
    }
    
    // Add event listener for payment amount input
    if (paymentAmountInput) {
        paymentAmountInput.addEventListener('input', function() {
            this.dataset.userModified = 'true';
            if (window.updatePaymentSummary) {
                window.updatePaymentSummary();
            }
        });
    }
    
    // Add professional ERP validation for ledger account selection
    if (ledgerAccountSelect) {
        ledgerAccountSelect.addEventListener('change', function() {
            validateLedgerAccountSelection(this);
        });
    }
    
}); // Close the DOMContentLoaded event listener

// Professional ERP Validation Functions
function validateLedgerAccountSelection(selectElement) {
    const selectedOption = selectElement.options[selectElement.selectedIndex];
    const validationContainer = getOrCreateValidationContainer(selectElement);
    
    // Clear previous validation messages
    clearValidationMessage(validationContainer);
    
    if (!selectedOption || !selectedOption.value) {
        return; // No selection, no validation needed
    }
    
    // Get account details via AJAX for real-time validation
    fetch('/chart-of-accounts/ajax/account-details/' + selectedOption.value + '/')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const account = data.account;
                const validationResult = validateAccountForCustomerPayment(account);
                
                if (!validationResult.isValid) {
                    showValidationError(validationContainer, validationResult.message, validationResult.type);
                    selectElement.classList.add('is-invalid');
                    hideAccountIndicators();
                } else {
                    showValidationSuccess(validationContainer, validationResult.message);
                    selectElement.classList.remove('is-invalid');
                    selectElement.classList.add('is-valid');
                    showAccountIndicators(account);
                }
            } else {
                showValidationError(validationContainer, 'Unable to validate account. Please try again.', 'error');
            }
        })
        .catch(error => {
            console.error('Error validating account:', error);
            showValidationError(validationContainer, 'Validation error. Please check your selection.', 'error');
        });
}

function validateAccountForCustomerPayment(account) {
    // Professional ERP validation rules for customer payments
    
    // Rule 1: Must be an ASSET account
    if (account.account_type_category !== 'ASSET') {
        return {
            isValid: false,
            message: `❌ Invalid account type. Customer payments must be posted to ASSET accounts only. Selected account "${account.account_type_name}" is a ${account.account_type_category} account.`,
            type: 'error'
        };
    }
    
    // Rule 2: Must have DEBIT or BOTH nature
    if (!['DEBIT', 'BOTH'].includes(account.account_nature)) {
        return {
            isValid: false,
            message: `❌ Invalid account nature. Customer payments require DEBIT nature accounts. Selected account has ${account.account_nature} nature.`,
            type: 'error'
        };
    }
    
    // Rule 3: Must be active
    if (!account.is_active) {
        return {
            isValid: false,
            message: '❌ Inactive account selected. Please choose an active account.',
            type: 'error'
        };
    }
    
    // Rule 4: Must not be a group account
    if (account.is_group) {
        return {
            isValid: false,
            message: '❌ Group account selected. Please choose a specific ledger account, not a group account.',
            type: 'error'
        };
    }
    
    // All validations passed
    return {
        isValid: true,
        message: `✅ Valid ASSET account with DEBIT nature selected. Professional ERP compliance verified.`,
        type: 'success'
    };
}

function getOrCreateValidationContainer(selectElement) {
    let container = selectElement.parentNode.querySelector('.ledger-validation-feedback');
    if (!container) {
        container = document.createElement('div');
        container.className = 'ledger-validation-feedback mt-1';
        selectElement.parentNode.appendChild(container);
    }
    return container;
}

function clearValidationMessage(container) {
    container.innerHTML = '';
    container.className = 'ledger-validation-feedback mt-1';
}

function showValidationError(container, message, type) {
    container.innerHTML = `
        <div class="alert alert-danger alert-sm py-1 px-2 mb-0" role="alert">
            <small><i class="bi bi-exclamation-triangle"></i> ${message}</small>
        </div>
    `;
    container.className = 'ledger-validation-feedback mt-1 validation-error';
}

function showValidationSuccess(container, message) {
    container.innerHTML = `
        <div class="alert alert-success alert-sm py-1 px-2 mb-0" role="alert">
            <small><i class="bi bi-check-circle"></i> ${message}</small>
        </div>
    `;
    container.className = 'ledger-validation-feedback mt-1 validation-success';
    
    // Auto-hide success message after 3 seconds
    setTimeout(() => {
        if (container.classList.contains('validation-success')) {
            container.innerHTML = '';
            container.className = 'ledger-validation-feedback mt-1';
        }
    }, 3000);
}

// UI Visual Indicators Functions
function showAccountIndicators(account) {
    // Show account type indicator
    const typeIndicator = document.getElementById('account-type-indicator');
    const typeText = document.getElementById('account-type-text');
    if (typeIndicator && typeText) {
        typeText.textContent = `${account.account_type_category}: ${account.account_type_name}`;
        typeIndicator.style.display = 'inline-block';
        
        // Color code based on category
        typeIndicator.className = 'badge text-dark';
        if (account.account_type_category === 'ASSET') {
            typeIndicator.classList.add('bg-info');
        } else {
            typeIndicator.classList.add('bg-warning');
        }
    }
    
    // Show account nature indicator
    const natureIndicator = document.getElementById('account-nature-indicator');
    const natureText = document.getElementById('account-nature-text');
    if (natureIndicator && natureText) {
        natureText.textContent = `${account.account_nature} Nature`;
        natureIndicator.style.display = 'inline-block';
        
        // Color code based on nature
        natureIndicator.className = 'badge';
        if (account.account_nature === 'DEBIT') {
            natureIndicator.classList.add('bg-success');
        } else {
            natureIndicator.classList.add('bg-danger');
        }
    }
    
    // Show ERP compliance indicator
    const complianceIndicator = document.getElementById('erp-compliance-indicator');
    if (complianceIndicator) {
        if (account.account_type_category === 'ASSET' && account.account_nature === 'DEBIT' && account.is_active && !account.is_group) {
            complianceIndicator.style.display = 'inline-block';
            complianceIndicator.className = 'badge bg-primary';
            complianceIndicator.innerHTML = '<i class="bi bi-shield-check"></i> ERP Compliant';
        } else {
            complianceIndicator.style.display = 'inline-block';
            complianceIndicator.className = 'badge bg-danger';
            complianceIndicator.innerHTML = '<i class="bi bi-shield-x"></i> Non-Compliant';
        }
    }
}

function hideAccountIndicators() {
    const indicators = [
        'account-type-indicator',
        'account-nature-indicator', 
        'erp-compliance-indicator'
    ];
    
    indicators.forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            element.style.display = 'none';
        }
    });
}

// Global function for inline HTML event handlers
function handleInvoiceAmountChange(input) {
    // Only update the payment summary, don't auto-sync main amount
    // Users should control the main payment amount manually
    if (window.updatePaymentSummary) {
        window.updatePaymentSummary();
    }
}