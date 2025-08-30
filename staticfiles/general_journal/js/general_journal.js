// General Journal JavaScript

document.addEventListener('DOMContentLoaded', function() {
    initializeGeneralJournal();
});

function initializeGeneralJournal() {
    
    // Initialize submit button state
    const submitBtn = document.getElementById('submit-btn') || document.querySelector('button[type="submit"]');
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.classList.remove('btn-primary');
        submitBtn.classList.add('btn-secondary');
    }
    
    // Initialize table management
    initializeTable();
    
    // Initialize balance calculation
    initializeBalanceCalculation();
    
    // Initialize amount input validation
    initializeAmountValidation();
    
    // Initialize search functionality
    initializeSearch();
}

// Table Management
function initializeTable() {
    const addLineBtn = document.getElementById('add-line-btn');
    const linesContainer = document.getElementById('journal-lines');
    
    if (addLineBtn && linesContainer) {
        addLineBtn.addEventListener('click', function(e) {
            e.preventDefault();
            addNewLine();
        });
    }
    
    // Add delete functionality to existing delete buttons
    document.querySelectorAll('.delete-line-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            deleteLine(this);
        });
    });
}

function addNewLine() {
    const linesContainer = document.getElementById('journal-lines');
    const currentLines = linesContainer.querySelectorAll('.journal-line');
    const newLineNumber = currentLines.length + 1;
    
    // Create new row
    const newRow = document.createElement('tr');
    newRow.className = 'journal-line';
    
    // Get the first row to clone the structure
    const firstRow = currentLines[0];
    const accountSelect = firstRow.querySelector('.account-select');
    
    // Create account cell
    const accountCell = document.createElement('td');
    const newAccountSelect = accountSelect.cloneNode(true);
    newAccountSelect.name = `account_${newLineNumber}`;
    newAccountSelect.value = '';
    accountCell.appendChild(newAccountSelect);
    
    // Create debit cell
    const debitCell = document.createElement('td');
    debitCell.className = 'text-end';
    const debitInput = document.createElement('input');
    debitInput.type = 'number';
    debitInput.className = 'form-control debit-amount';
    debitInput.name = `debit_${newLineNumber}`;
    debitInput.step = '0.01';
    debitInput.min = '0';
    debitInput.placeholder = '0.00';
    debitCell.appendChild(debitInput);
    
    // Create credit cell
    const creditCell = document.createElement('td');
    creditCell.className = 'text-end';
    const creditInput = document.createElement('input');
    creditInput.type = 'number';
    creditInput.className = 'form-control credit-amount';
    creditInput.name = `credit_${newLineNumber}`;
    creditInput.step = '0.01';
    creditInput.min = '0';
    creditInput.placeholder = '0.00';
    creditCell.appendChild(creditInput);
    
    // Add cells to row
    newRow.appendChild(accountCell);
    newRow.appendChild(debitCell);
    newRow.appendChild(creditCell);
    
    // Add to container
    linesContainer.appendChild(newRow);
    
    // Add animation class
    newRow.classList.add('new-line');
    setTimeout(() => newRow.classList.remove('new-line'), 300);
    
    // Reinitialize amount validation for new line
    initializeAmountValidationForLine(newRow);
    
    // Add balance calculation event listeners to new inputs
    debitInput.addEventListener('input', calculateBalance);
    creditInput.addEventListener('input', calculateBalance);
    newAccountSelect.addEventListener('change', calculateBalance);
    
    // Update balance
    calculateBalance();
}

function deleteLine(deleteBtn) {
    const line = deleteBtn.closest('.journal-line');
    const linesContainer = document.getElementById('journal-lines');
    
    // Check if this is the last line
    const lines = linesContainer.querySelectorAll('.journal-line');
    if (lines.length <= 2) {
        alert('At least 2 lines are required for a journal entry.');
        return;
    }
    
    // Remove the line
    line.remove();
    
    // Reindex remaining forms
    reindexForms();
    
    // Update balance
    calculateBalance();
}

function reindexForms() {
    const lines = document.querySelectorAll('.journal-line');
    lines.forEach((line, index) => {
        const lineNumber = index + 1;
        
        // Update account select name
        const accountSelect = line.querySelector('.account-select');
        if (accountSelect) {
            accountSelect.name = `account_${lineNumber}`;
        }
        
        // Update debit input name
        const debitInput = line.querySelector('.debit-amount');
        if (debitInput) {
            debitInput.name = `debit_${lineNumber}`;
        }
        
        // Update credit input name
        const creditInput = line.querySelector('.credit-amount');
        if (creditInput) {
            creditInput.name = `credit_${lineNumber}`;
        }
    });
}

// Balance Calculation
function initializeBalanceCalculation() {
    console.log('Initializing balance calculation...');
    const debitInputs = document.querySelectorAll('.debit-amount');
    const creditInputs = document.querySelectorAll('.credit-amount');
    const accountSelects = document.querySelectorAll('.account-select');
    
    console.log('Found debit inputs:', debitInputs.length);
    console.log('Found credit inputs:', creditInputs.length);
    console.log('Found account selects:', accountSelects.length);
    
    debitInputs.forEach(input => {
        input.addEventListener('input', calculateBalance);
    });
    
    creditInputs.forEach(input => {
        input.addEventListener('input', calculateBalance);
    });
    
    // Add event listeners to account selects
    accountSelects.forEach(select => {
        select.addEventListener('change', calculateBalance);
    });
    
    // Initial calculation
    console.log('Running initial balance calculation...');
    calculateBalance();
}

function calculateBalance() {
    console.log('Calculating balance...');
    let totalDebit = 0;
    let totalCredit = 0;
    
    // Calculate totals
    document.querySelectorAll('.debit-amount').forEach(input => {
        const value = parseFloat(input.value) || 0;
        totalDebit += value;
    });
    
    document.querySelectorAll('.credit-amount').forEach(input => {
        const value = parseFloat(input.value) || 0;
        totalCredit += value;
    });
    
    // Update display
    const totalDebitElement = document.getElementById('total-debit');
    const totalCreditElement = document.getElementById('total-credit');
    const balanceIndicator = document.getElementById('balance-indicator');
    
    if (totalDebitElement) {
        totalDebitElement.textContent = totalDebit.toFixed(2);
    }
    
    if (totalCreditElement) {
        totalCreditElement.textContent = totalCredit.toFixed(2);
    }
    
    // Update balance indicator
    if (balanceIndicator) {
        const difference = Math.abs(totalDebit - totalCredit);
        if (difference < 0.01) {
            balanceIndicator.textContent = 'BALANCED';
            balanceIndicator.className = 'balance-indicator balanced';
        } else {
            balanceIndicator.textContent = `UNBALANCED (${difference.toFixed(2)})`;
            balanceIndicator.className = 'balance-indicator unbalanced';
        }
    }
    
    // Update form validation
    updateFormValidation(totalDebit, totalCredit);
}

function updateFormValidation(totalDebit, totalCredit) {
    const submitBtn = document.getElementById('submit-btn') || document.querySelector('button[type="submit"]');
    const difference = Math.abs(totalDebit - totalCredit);
    
    // Check if at least one account is selected
    const accountSelects = document.querySelectorAll('.account-select');
    let hasSelectedAccount = false;
    accountSelects.forEach(select => {
        if (select.value && select.value !== '') {
            hasSelectedAccount = true;
        }
    });
    
    // Create or update validation status indicator
    let validationStatus = document.getElementById('validation-status');
    if (!validationStatus) {
        validationStatus = document.createElement('div');
        validationStatus.id = 'validation-status';
        validationStatus.style.cssText = 'margin: 15px 0; padding: 12px; border-radius: 8px; font-size: 14px;';
        
        // Insert after the journal entries table
        const journalTable = document.querySelector('.table-responsive');
        if (journalTable && journalTable.parentElement) {
            journalTable.parentElement.insertBefore(validationStatus, journalTable.nextSibling);
        } else {
            // Fallback: insert before submit button if table not found
            const submitBtnContainer = submitBtn.parentElement;
            submitBtnContainer.insertBefore(validationStatus, submitBtn);
        }
    }
    
    console.log('Submit button found:', !!submitBtn);
    console.log('Difference:', difference);
    console.log('Has selected account:', hasSelectedAccount);
    console.log('Account selects count:', accountSelects.length);
    console.log('Conditions - Difference < 0.01:', difference < 0.01, 'Debit > 0:', totalDebit > 0, 'Credit > 0:', totalCredit > 0, 'Has account:', hasSelectedAccount);
    
    const isBalanced = difference < 0.01;
    const hasDebit = totalDebit > 0;
    const hasCredit = totalCredit > 0;
    
    if (submitBtn) {
        if (isBalanced && hasDebit && hasCredit && hasSelectedAccount) {
            submitBtn.disabled = false;
            submitBtn.removeAttribute('disabled');
            submitBtn.classList.remove('btn-secondary');
            submitBtn.classList.add('btn-primary');
            submitBtn.style.pointerEvents = 'auto';
            submitBtn.style.opacity = '1';
            
            validationStatus.innerHTML = '<i class="bi bi-check-circle-fill text-success me-2"></i>Ready to submit! All validation checks passed.';
            validationStatus.className = 'validation-status text-success';
        } else {

            submitBtn.disabled = true;
            submitBtn.setAttribute('disabled', 'disabled');
            submitBtn.classList.remove('btn-primary');
            submitBtn.classList.add('btn-secondary');
            submitBtn.style.pointerEvents = 'none';
            submitBtn.style.opacity = '0.6';
            
            let message = '';
            if (!hasSelectedAccount) {
                message = 'Please select accounts for your journal entries.';
            } else if (!hasDebit || !hasCredit) {
                message = 'Please enter both debit and credit amounts.';
            } else if (!isBalanced) {
                message = 'Please ensure debits and credits are balanced.';
            }
            
            validationStatus.innerHTML = '<i class="bi bi-info-circle text-info me-2"></i>' + message;
            validationStatus.className = 'validation-status text-info';
        }
    }
}

// Amount Input Validation
function initializeAmountValidation() {
    document.querySelectorAll('.debit-amount, .credit-amount').forEach(input => {
        initializeAmountValidationForInput(input, input.classList.contains('debit-amount') ? 'debit' : 'credit');
    });
}

function initializeAmountValidationForInput(input, type) {
    input.addEventListener('input', function() {
        const value = this.value;
        
        // Allow only numbers and decimal point
        const cleanValue = value.replace(/[^0-9.]/g, '');
        
        // Ensure only one decimal point
        const parts = cleanValue.split('.');
        if (parts.length > 2) {
            this.value = parts[0] + '.' + parts.slice(1).join('');
        } else {
            this.value = cleanValue;
        }
        
        // Limit to 2 decimal places
        if (parts.length === 2 && parts[1].length > 2) {
            this.value = parts[0] + '.' + parts[1].substring(0, 2);
        }
        
        // Clear the other amount field when one is entered
        const otherType = type === 'debit' ? 'credit' : 'debit';
        const otherInput = this.closest('.journal-line').querySelector(`.${otherType}-amount`);
        if (otherInput && this.value && parseFloat(this.value) > 0) {
            otherInput.value = '';
        }
    });
}

function initializeAmountValidationForLine(line) {
    const debitInput = line.querySelector('.debit-amount');
    const creditInput = line.querySelector('.credit-amount');
    
    if (debitInput) {
        initializeAmountValidationForInput(debitInput, 'debit');
    }
    
    if (creditInput) {
        initializeAmountValidationForInput(creditInput, 'credit');
    }
}

// Search Functionality
function initializeSearch() {
    const searchForm = document.querySelector('.search-form');
    if (searchForm) {
        const searchInput = searchForm.querySelector('input[name="search_query"]');
        const searchType = searchForm.querySelector('select[name="search_type"]');
        
        // Auto-submit on search type change if query exists
        if (searchType && searchInput) {
            searchType.addEventListener('change', function() {
                if (searchInput.value.trim()) {
                    searchForm.submit();
                }
            });
        }
    }
}

// Utility Functions
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'AED'
    }).format(amount);
}

function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
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