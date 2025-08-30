// Tax Invoice Module JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize date pickers
    initializeDatePickers();
    
    // Initialize form validation
    initializeFormValidation();
    
    // Initialize calculator
    initializeCalculator();
    
    // Initialize search functionality
    initializeSearch();
});

// Date Picker Initialization
function initializeDatePickers() {
    const dateInputs = document.querySelectorAll('input[type="date"]');
    dateInputs.forEach(input => {
        if (!input.value) {
            input.value = new Date().toISOString().split('T')[0];
        }
    });
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
}

// Calculator Functionality
function initializeCalculator() {
    const calculatorForm = document.getElementById('calculatorForm');
    if (calculatorForm) {
        calculatorForm.addEventListener('submit', function(e) {
            e.preventDefault();
            calculateTax();
        });
    }
}

// Tax Calculation
function calculateTax() {
    const amount = parseFloat(document.getElementById('id_amount').value) || 0;
    const vatRate = parseFloat(document.getElementById('id_vat_rate').value) || 0;
    const calculationType = document.getElementById('id_calculation_type').value;
    
    let result = {};
    
    if (calculationType === 'exclusive') {
        // Add VAT to amount
        const vatAmount = amount * (vatRate / 100);
        const totalAmount = amount + vatAmount;
        result = {
            original_amount: amount,
            vat_rate: vatRate,
            vat_amount: vatAmount,
            total_amount: totalAmount,
            calculation_type: 'VAT Exclusive'
        };
    } else {
        // Extract VAT from amount
        const vatAmount = amount * (vatRate / (100 + vatRate));
        const taxableAmount = amount - vatAmount;
        result = {
            original_amount: amount,
            vat_rate: vatRate,
            vat_amount: vatAmount,
            taxable_amount: taxableAmount,
            calculation_type: 'VAT Inclusive'
        };
    }
    
    displayCalculationResult(result);
}

// Display Calculation Result
function displayCalculationResult(result) {
    const resultDiv = document.getElementById('calculationResult');
    if (resultDiv) {
        resultDiv.innerHTML = `
            <div class="alert alert-info">
                <h6>Calculation Result</h6>
                <div class="row">
                    <div class="col-md-6">
                        <p><strong>Original Amount:</strong> ${result.original_amount.toFixed(2)}</p>
                        <p><strong>VAT Rate:</strong> ${result.vat_rate}%</p>
                        <p><strong>VAT Amount:</strong> ${result.vat_amount.toFixed(2)}</p>
                    </div>
                    <div class="col-md-6">
                        ${result.total_amount ? `<p><strong>Total Amount:</strong> ${result.total_amount.toFixed(2)}</p>` : ''}
                        ${result.taxable_amount ? `<p><strong>Taxable Amount:</strong> ${result.taxable_amount.toFixed(2)}</p>` : ''}
                        <p><strong>Type:</strong> ${result.calculation_type}</p>
                    </div>
                </div>
            </div>
        `;
        resultDiv.style.display = 'block';
    }
}

// Search Functionality
function initializeSearch() {
    const searchInput = document.querySelector('input[name="search"]');
    if (searchInput) {
        let searchTimeout;
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                performSearch(this.value);
            }, 500);
        });
    }
}

// Perform Search
function performSearch(query) {
    if (query.length < 2) return;
    
    const currentUrl = new URL(window.location);
    currentUrl.searchParams.set('search', query);
    window.location.href = currentUrl.toString();
}

// Invoice Item Management
function addInvoiceItem() {
    const itemForms = document.getElementById('itemForms');
    const formCount = document.getElementById('id_items-TOTAL_FORMS');
    const currentCount = parseInt(formCount.value);
    
    // Clone the first item form
    const firstForm = itemForms.querySelector('.item-form');
    const newForm = firstForm.cloneNode(true);
    
    // Update form indices
    newForm.innerHTML = newForm.innerHTML.replace(/items-\d+-/g, `items-${currentCount}-`);
    
    // Clear the new form
    newForm.querySelectorAll('input[type="text"], input[type="number"]').forEach(input => {
        input.value = '';
    });
    
    // Add the new form
    itemForms.appendChild(newForm);
    formCount.value = currentCount + 1;
    
    // Recalculate totals
    calculateTotals();
}

// Calculate Invoice Totals
function calculateTotals() {
    let subtotal = 0;
    let totalVat = 0;
    
    // Calculate totals for each item
    document.querySelectorAll('.item-form').forEach(function(form) {
        const quantity = parseFloat(form.querySelector('input[name*="quantity"]').value) || 0;
        const unitPrice = parseFloat(form.querySelector('input[name*="unit_price"]').value) || 0;
        const vatPercentage = parseFloat(form.querySelector('input[name*="vat_percentage"]').value) || 0;
        
        const itemTotal = quantity * unitPrice;
        const itemVat = itemTotal * (vatPercentage / 100);
        const itemGrandTotal = itemTotal + itemVat;
        
        // Update item total display
        const totalField = form.querySelector('input[id*="itemTotal"]');
        if (totalField) {
            totalField.value = itemGrandTotal.toFixed(2);
        }
        
        subtotal += itemTotal;
        totalVat += itemVat;
    });
    
    const grandTotal = subtotal + totalVat;
    
    // Update totals display
    const subtotalElement = document.getElementById('subtotal');
    const totalVatElement = document.getElementById('totalVat');
    const grandTotalElement = document.getElementById('grandTotal');
    
    if (subtotalElement) subtotalElement.textContent = subtotal.toFixed(2);
    if (totalVatElement) totalVatElement.textContent = totalVat.toFixed(2);
    if (grandTotalElement) grandTotalElement.textContent = grandTotal.toFixed(2);
}

// Export Functionality
function exportInvoice(format) {
    const invoiceId = document.querySelector('[data-invoice-id]')?.dataset.invoiceId;
    if (!invoiceId) {
        alert('Invoice ID not found');
        return;
    }
    
    const url = `/tax-invoice/invoices/${invoiceId}/export/`;
    const formData = new FormData();
    formData.append('export_format', format);
    formData.append('csrfmiddlewaretoken', document.querySelector('[name=csrfmiddlewaretoken]').value);
    
    fetch(url, {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Export completed successfully');
        } else {
            alert('Export failed: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Export error:', error);
        alert('Export failed');
    });
}

// Print Invoice
function printInvoice() {
    window.print();
}

// Email Invoice
function emailInvoice() {
    const emailModal = new bootstrap.Modal(document.getElementById('emailModal'));
    emailModal.show();
}

// Send Email
function sendEmail() {
    const emailTo = document.getElementById('emailTo').value;
    const emailSubject = document.getElementById('emailSubject').value;
    const emailMessage = document.getElementById('emailMessage').value;
    
    if (!emailTo) {
        alert('Please enter an email address');
        return;
    }
    
    const invoiceId = document.querySelector('[data-invoice-id]')?.dataset.invoiceId;
    if (!invoiceId) {
        alert('Invoice ID not found');
        return;
    }
    
    const formData = new FormData();
    formData.append('email_to', emailTo);
    formData.append('email_subject', emailSubject);
    formData.append('email_message', emailMessage);
    formData.append('csrfmiddlewaretoken', document.querySelector('[name=csrfmiddlewaretoken]').value);
    
    fetch(`/tax-invoice/invoices/${invoiceId}/export/`, {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Email sent successfully');
            bootstrap.Modal.getInstance(document.getElementById('emailModal')).hide();
        } else {
            alert('Email failed: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Email error:', error);
        alert('Email failed');
    });
}

// Template Preview
function previewTemplate(templateId) {
    const previewModal = new bootstrap.Modal(document.getElementById('previewModal'));
    const previewContent = document.getElementById('previewContent');
    
    // Load template preview
    fetch(`/tax-invoice/templates/${templateId}/preview/`)
        .then(response => response.text())
        .then(html => {
            previewContent.innerHTML = html;
            previewModal.show();
        })
        .catch(error => {
            console.error('Preview error:', error);
            alert('Failed to load preview');
        });
}

// Settings Management
function saveSettings() {
    const settingsForm = document.getElementById('settingsForm');
    if (settingsForm) {
        settingsForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            fetch('/tax-invoice/settings/', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Settings saved successfully');
                } else {
                    alert('Settings save failed: ' + data.error);
                }
            })
            .catch(error => {
                console.error('Settings error:', error);
                alert('Settings save failed');
            });
        });
    }
}

// Utility Functions
function formatCurrency(amount, currency = 'AED') {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: currency
    }).format(amount);
}

function formatDate(date) {
    return new Intl.DateTimeFormat('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    }).format(new Date(date));
}

// Event Listeners
document.addEventListener('click', function(e) {
    // Add item button
    if (e.target.id === 'addItem') {
        e.preventDefault();
        addInvoiceItem();
    }
    
    // Calculate totals on input change
    if (e.target.name && (e.target.name.includes('quantity') || e.target.name.includes('unit_price') || e.target.name.includes('vat_percentage'))) {
        calculateTotals();
    }
});

// Initialize on page load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeTaxInvoice);
} else {
    initializeTaxInvoice();
}

function initializeTaxInvoice() {
    // Initialize all components
    initializeDatePickers();
    initializeFormValidation();
    initializeCalculator();
    initializeSearch();
    saveSettings();
    
    // Calculate totals if on invoice form
    if (document.querySelector('.item-form')) {
        calculateTotals();
    }
}
