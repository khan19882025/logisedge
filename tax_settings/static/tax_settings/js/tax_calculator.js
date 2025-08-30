// Tax Calculator JavaScript

$(document).ready(function() {
    initializeTaxCalculator();
    initializeRealTimeCalculation();
    initializeFormValidation();
    initializeKeyboardShortcuts();
});

function initializeTaxCalculator() {
    // Handle form submission
    $('#taxCalculatorForm').on('submit', function(e) {
        e.preventDefault();
        calculateTax();
    });
    
    // Auto-calculate on input change
    $('#id_taxable_amount, #id_tax_rate').on('input change', function() {
        if ($('#id_taxable_amount').val() && $('#id_tax_rate').val()) {
            calculateTax();
        }
    });
}

function calculateTax() {
    const taxableAmount = parseFloat($('#id_taxable_amount').val()) || 0;
    const taxRateId = $('#id_tax_rate').val();
    const currency = $('#id_currency').val();
    
    if (!taxableAmount || !taxRateId) {
        showError('Please enter both taxable amount and select a tax rate.');
        return;
    }
    
    // Show loading state
    showLoading();
    
    // Get tax rate details
    const selectedOption = $('#id_tax_rate option:selected');
    const taxRateName = selectedOption.text();
    const taxRatePercentage = parseFloat(selectedOption.data('percentage')) || 0;
    
    // Calculate tax amount
    const taxAmount = (taxableAmount * taxRatePercentage) / 100;
    const totalAmount = taxableAmount + taxAmount;
    
    // Display result
    displayCalculationResult({
        taxable_amount: taxableAmount,
        tax_rate_name: taxRateName,
        tax_rate_percentage: taxRatePercentage,
        tax_amount: taxAmount,
        total_amount: totalAmount,
        currency: currency
    });
    
    // Hide loading
    hideLoading();
    
    // Add success animation
    addSuccessAnimation();
}

function displayCalculationResult(result) {
    const resultHtml = `
        <div class="calculation-result calculation-success">
            <div class="row">
                <div class="col-md-6">
                    <div class="result-item">
                        <label>Taxable Amount:</label>
                        <span class="amount">${result.currency} ${result.taxable_amount.toFixed(2)}</span>
                    </div>
                    <div class="result-item">
                        <label>Tax Rate:</label>
                        <span class="rate">${result.tax_rate_name} (${result.tax_rate_percentage}%)</span>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="result-item">
                        <label>Tax Amount:</label>
                        <span class="tax-amount">${result.currency} ${result.tax_amount.toFixed(2)}</span>
                    </div>
                    <div class="result-item">
                        <label>Total Amount:</label>
                        <span class="total-amount">${result.currency} ${result.total_amount.toFixed(2)}</span>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    $('#calculatorResult').html(resultHtml);
    
    // Add animation
    $('#calculatorResult').addClass('fade-in');
    setTimeout(() => {
        $('#calculatorResult').removeClass('fade-in');
    }, 500);
}

function showLoading() {
    $('#calculatorResult').html(`
        <div class="text-center">
            <div class="spinner-border text-primary" role="status">
                <span class="sr-only">Calculating...</span>
            </div>
            <p class="mt-2 text-muted">Calculating tax amount...</p>
        </div>
    `);
}

function hideLoading() {
    // Loading is hidden when result is displayed
}

function showError(message) {
    $('#calculatorResult').html(`
        <div class="alert alert-danger">
            <i class="fas fa-exclamation-triangle"></i>
            ${message}
        </div>
    `);
}

function addSuccessAnimation() {
    $('.calculation-result').addClass('success-pulse');
    setTimeout(() => {
        $('.calculation-result').removeClass('success-pulse');
    }, 1000);
}

function initializeRealTimeCalculation() {
    let calculationTimeout;
    
    $('#id_taxable_amount, #id_tax_rate').on('input', function() {
        clearTimeout(calculationTimeout);
        
        calculationTimeout = setTimeout(() => {
            const taxableAmount = parseFloat($('#id_taxable_amount').val()) || 0;
            const taxRateId = $('#id_tax_rate').val();
            
            if (taxableAmount > 0 && taxRateId) {
                calculateTax();
            }
        }, 500); // Delay calculation by 500ms after user stops typing
    });
}

function initializeFormValidation() {
    // Validate taxable amount
    $('#id_taxable_amount').on('input', function() {
        const value = parseFloat($(this).val());
        if (value < 0) {
            $(this).addClass('is-invalid');
            $(this).next('.invalid-feedback').text('Taxable amount cannot be negative.');
        } else {
            $(this).removeClass('is-invalid');
        }
    });
    
    // Validate tax rate selection
    $('#id_tax_rate').on('change', function() {
        if (!$(this).val()) {
            $(this).addClass('is-invalid');
        } else {
            $(this).removeClass('is-invalid');
        }
    });
}

function initializeKeyboardShortcuts() {
    $(document).on('keydown', function(e) {
        // Ctrl/Cmd + Enter to calculate
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            e.preventDefault();
            calculateTax();
        }
        
        // Escape to clear form
        if (e.key === 'Escape') {
            $('#taxCalculatorForm')[0].reset();
            $('#calculatorResult').html(`
                <div class="text-center text-muted">
                    <i class="fas fa-calculator fa-3x mb-3"></i>
                    <p>Enter values and click "Calculate Tax" to see the result.</p>
                </div>
            `);
        }
    });
}

// Utility functions
function formatCurrency(amount, currency = 'AED') {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: currency
    }).format(amount);
}

function roundToDecimals(number, decimals = 2) {
    return Math.round(number * Math.pow(10, decimals)) / Math.pow(10, decimals);
}

// Tax rate reference functionality
function initializeTaxRateReference() {
    $('.tax-rate-card').on('click', function() {
        const percentage = $(this).find('.rate-percentage').text();
        const label = $(this).find('.rate-label').text();
        
        // Find matching tax rate in dropdown
        const option = $(`#id_tax_rate option:contains("${percentage}")`).first();
        if (option.length) {
            $('#id_tax_rate').val(option.val()).trigger('change');
            
            // Show feedback
            showNotification(`Selected ${label} tax rate (${percentage})`, 'success');
        }
    });
}

function showNotification(message, type = 'info') {
    const notification = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="close" data-dismiss="alert" aria-label="Close">
                <span aria-hidden="true">&times;</span>
            </button>
        </div>
    `;
    
    // Add notification to page
    $('.container-fluid').prepend(notification);
    
    // Auto-dismiss after 3 seconds
    setTimeout(() => {
        $('.alert').fadeOut();
    }, 3000);
}

// Print functionality
function printCalculation() {
    const printWindow = window.open('', '_blank');
    const calculationResult = $('#calculatorResult').html();
    
    printWindow.document.write(`
        <html>
            <head>
                <title>Tax Calculation Result</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 20px; }
                    .calculation-result { border: 1px solid #ddd; padding: 20px; margin: 20px 0; }
                    .result-item { margin: 10px 0; }
                    .result-item label { font-weight: bold; }
                    .total-amount { font-size: 1.2em; font-weight: bold; color: #1cc88a; }
                </style>
            </head>
            <body>
                <h1>Tax Calculation Result</h1>
                ${calculationResult}
                <p><small>Generated on ${new Date().toLocaleString()}</small></p>
            </body>
        </html>
    `);
    
    printWindow.document.close();
    printWindow.print();
}

// Export functionality
function exportCalculation() {
    const taxableAmount = $('#id_taxable_amount').val();
    const taxRate = $('#id_tax_rate option:selected').text();
    const currency = $('#id_currency').val();
    
    if (!taxableAmount || !taxRate) {
        showError('Please complete a calculation before exporting.');
        return;
    }
    
    const data = {
        taxable_amount: taxableAmount,
        tax_rate: taxRate,
        currency: currency,
        timestamp: new Date().toISOString()
    };
    
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `tax_calculation_${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// Initialize everything when document is ready
$(document).ready(function() {
    initializeTaxCalculator();
    initializeRealTimeCalculation();
    initializeFormValidation();
    initializeKeyboardShortcuts();
    initializeTaxRateReference();
    
    // Add print and export buttons
    addActionButtons();
});

function addActionButtons() {
    const actionButtons = `
        <div class="row mt-3">
            <div class="col-12">
                <div class="btn-group" role="group">
                    <button type="button" class="btn btn-outline-secondary" onclick="printCalculation()">
                        <i class="fas fa-print"></i> Print
                    </button>
                    <button type="button" class="btn btn-outline-secondary" onclick="exportCalculation()">
                        <i class="fas fa-download"></i> Export
                    </button>
                    <button type="button" class="btn btn-outline-secondary" onclick="clearForm()">
                        <i class="fas fa-eraser"></i> Clear
                    </button>
                </div>
            </div>
        </div>
    `;
    
    $('#taxCalculatorForm').after(actionButtons);
}

function clearForm() {
    $('#taxCalculatorForm')[0].reset();
    $('#calculatorResult').html(`
        <div class="text-center text-muted">
            <i class="fas fa-calculator fa-3x mb-3"></i>
            <p>Enter values and click "Calculate Tax" to see the result.</p>
        </div>
    `);
    showNotification('Form cleared successfully', 'info');
}
