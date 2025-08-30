// Petty Cash Register JavaScript - Professional Design
$(document).ready(function() {
    initializePettyCashRegister();
});

function initializePettyCashRegister() {
    // Initialize date picker
    initializeDatePicker();
    
    // Initialize form validation
    initializeFormValidation();
    
    // Initialize running balance calculations
    initializeRunningBalance();
    
    // Initialize action buttons
    initializeActionButtons();
    
    // Initialize keyboard shortcuts
    initializeKeyboardShortcuts();
    
    // Add animations
    addAnimations();
    
    // Calculate initial balances
    calculateRunningBalances();
}

function initializeDatePicker() {
    // Date picker change handler
    $('#id_entry_date').on('change', function() {
        const selectedDate = $(this).val();
        if (selectedDate) {
            // Update URL with new date
            const currentUrl = new URL(window.location);
            currentUrl.searchParams.set('date', selectedDate);
            window.location.href = currentUrl.toString();
        }
    });
    
    // Previous/Next day navigation
    $('.nav-prev').on('click', function() {
        navigateToDate('prev');
    });
    
    $('.nav-next').on('click', function() {
        navigateToDate('next');
    });
}

function navigateToDate(direction) {
    const currentDate = $('#id_entry_date').val();
    if (!currentDate) return;
    
    const date = new Date(currentDate);
    if (direction === 'prev') {
        date.setDate(date.getDate() - 1);
    } else {
        date.setDate(date.getDate() + 1);
    }
    
    const newDate = date.toISOString().split('T')[0];
    const currentUrl = new URL(window.location);
    currentUrl.searchParams.set('date', newDate);
    window.location.href = currentUrl.toString();
}

function initializeFormValidation() {
    // Real-time validation for amount fields
    $(document).on('input', 'input[name*="amount"]', function() {
        validateAmount($(this));
        calculateRunningBalances();
    });
    
    // Real-time validation for description fields
    $(document).on('input', 'input[name*="description"]', function() {
        validateDescription($(this));
    });
    
    // Form submission validation
    $('#pettyCashForm').on('submit', function(e) {
        if (!validateForm()) {
            e.preventDefault();
            return false;
        }
    });
}

function validateAmount(input) {
    const value = parseFloat(input.val()) || 0;
    
    // Allow zero amounts (empty entries)
    if (value < 0) {
        input.addClass('is-invalid');
        showFieldError(input, 'Amount cannot be negative');
        return false;
    } else {
        input.removeClass('is-invalid');
        hideFieldError(input);
        return true;
    }
}

function validateDescription(input) {
    const value = input.val().trim();
    const amount = parseFloat(input.closest('tr').find('input[name*="amount"]').val()) || 0;
    
    // Only require description if amount is greater than 0
    if (!value && amount > 0) {
        input.addClass('is-invalid');
        showFieldError(input, 'Description is required for entries with amount');
        return false;
    } else {
        input.removeClass('is-invalid');
        hideFieldError(input);
        return true;
    }
}

function validateForm() {
    let isValid = true;
    
    // Clear previous errors
    $('.is-invalid').removeClass('is-invalid');
    $('.field-error').remove();
    
    // Only validate rows that have data
    $('#entriesTableBody .entry-row').each(function() {
        const row = $(this);
        const amountInput = row.find('input[name*="amount"]');
        const descriptionInput = row.find('input[name*="description"]');
        const amount = parseFloat(amountInput.val()) || 0;
        const description = descriptionInput.val().trim();
        
        // Skip validation for completely empty rows
        if (amount === 0 && !description) {
            return true; // continue to next row
        }
        
        // Validate amount if present
        if (amount > 0 && !validateAmount(amountInput)) {
            isValid = false;
        }
        
        // Validate description if amount is present
        if (amount > 0 && !validateDescription(descriptionInput)) {
            isValid = false;
        }
    });
    
    return isValid;
}

function showFieldError(input, message) {
    const errorDiv = input.siblings('.field-error');
    if (errorDiv.length === 0) {
        input.after(`<div class="field-error text-danger small mt-1">${message}</div>`);
    } else {
        errorDiv.text(message);
    }
}

function hideFieldError(input) {
    input.siblings('.field-error').remove();
}

function initializeRunningBalance() {
    // Calculate balances on amount change
    $(document).on('input', 'input[name*="amount"]', function() {
        calculateRunningBalances();
    });
    
    // Calculate balances on opening balance change
    $(document).on('input', 'input[name="opening_balance"]', function() {
        const newOpeningBalance = $(this).val() || '0.00';
        $('#openingBalance').val(newOpeningBalance);
        calculateRunningBalances();
    });
    
    // Recalculate when rows are added or deleted
    $(document).on('click', '.delete-entry-btn', function() {
        setTimeout(() => calculateRunningBalances(), 100);
    });
}

function calculateRunningBalances() {
    // Use actual ledger balance as the starting point
    const actualLedgerBalance = parseFloat($('#actualLedgerBalance').val()) || 0;
    let runningBalance = actualLedgerBalance;
    
    // Update each row's balance
    $('#entriesTableBody .entry-row').each(function(index) {
        const row = $(this);
        const amount = parseFloat(row.find('input[name*="amount"]').val()) || 0;
        
        // For petty cash, amounts are debits (expenses), so subtract from balance
        runningBalance -= amount;
        
        // Update balance cell
        const balanceCell = row.find('.balance-cell');
        balanceCell.text(formatCurrency(runningBalance));
        balanceCell.attr('data-balance', runningBalance.toFixed(2));
        
        // Color coding for balance
        if (runningBalance < 0) {
            balanceCell.addClass('negative').removeClass('positive');
        } else {
            balanceCell.addClass('positive').removeClass('negative');
        }
    });
    
    // Update running balance display
    $('#runningBalance').text(formatCurrency(runningBalance));
    
    // Update running balance color
    if (runningBalance < 0) {
        $('#runningBalance').addClass('text-danger').removeClass('text-success');
    } else {
        $('#runningBalance').addClass('text-success').removeClass('text-danger');
    }
}

function initializeActionButtons() {
    // Remove existing handlers to prevent duplicates
    $('#addNewEntryBtn').off('click');
    $('#saveBtn').off('click');
    $('#exportPdfBtn').off('click');
    $('#exportExcelBtn').off('click');
    $('.print-btn').off('click');
    $(document).off('click', '.delete-entry-btn');
    
    // Add new entry button
    $('#addNewEntryBtn').on('click', function() {
        addNewEntry();
    });
    
    // Delete entry buttons
    $(document).on('click', '.delete-entry-btn', function() {
        deleteEntry($(this));
    });
    
    // Save button
    $('#saveBtn').on('click', function() {
        savePettyCash();
    });
    
    // Export PDF button
    $('#exportPdfBtn').on('click', function() {
        exportToPDF();
    });
    
    // Export Excel button
    $('#exportExcelBtn').on('click', function() {
        exportToExcel();
    });
    
    // Print button
    $('.print-btn').on('click', function() {
        printSummary();
    });
}

function addNewEntry() {
    const tbody = $('#entriesTableBody');
    const totalForms = parseInt($('#id_entries-TOTAL_FORMS').val());
    const newFormNum = totalForms;
    
    // Get the template row (first row or create a new one)
    let templateRow;
    if (tbody.find('.entry-row').length > 0) {
        templateRow = tbody.find('.entry-row').first().clone();
    } else {
        // Create a new row if no existing rows
        templateRow = createNewEntryRow(newFormNum);
    }
    
    // Update form indices
    templateRow.find('input, select, textarea').each(function() {
        const name = $(this).attr('name');
        const id = $(this).attr('id');
        
        if (name) {
            $(this).attr('name', name.replace(/-\d+-/, `-${newFormNum}-`));
        }
        if (id) {
            $(this).attr('id', id.replace(/-\d+-/, `-${newFormNum}-`));
        }
    });
    
    // Clear values
    templateRow.find('input[type="text"], input[type="number"], textarea').val('');
    templateRow.find('input[type="checkbox"]').prop('checked', false);
    templateRow.find('select').prop('selectedIndex', 0);
    
    // Update serial number
    templateRow.find('td:first').text(newFormNum + 1);
    
    // Reset balance
    templateRow.find('.balance-cell').text('0.00').attr('data-balance', '0.00');
    
    // Update form index attribute
    templateRow.attr('data-form-index', newFormNum);
    
    // Add to table
    tbody.append(templateRow);
    
    // Update total forms count
    $('#id_entries-TOTAL_FORMS').val(newFormNum + 1);
    
    // Add animation
    templateRow.addClass('slide-in');
    
    // Focus on job number field
    templateRow.find('input[name*="job_no"]').focus();
    
    // Recalculate balances
    calculateRunningBalances();
    
    // Update serial numbers
    updateSerialNumbers();
}

function createNewEntryRow(formIndex) {
    return $(`
        <tr class="entry-row" data-form-index="${formIndex}">
            <td class="fw-semibold">${formIndex + 1}</td>
            <td>
                <input type="text" name="entries-${formIndex}-job_no" id="id_entries-${formIndex}-job_no" class="form-control" placeholder="Job No.">
            </td>
            <td>
                <input type="text" name="entries-${formIndex}-description" id="id_entries-${formIndex}-description" class="form-control" placeholder="Description" required>
            </td>
            <td>
                <input type="number" name="entries-${formIndex}-amount" id="id_entries-${formIndex}-amount" class="form-control amount-input" step="0.01" min="0.01" placeholder="0.00">
            </td>
            <td>
                <input type="text" name="entries-${formIndex}-notes" id="id_entries-${formIndex}-notes" class="form-control" placeholder="Notes (optional)">
            </td>
            <td class="balance-cell" data-balance="0.00">0.00</td>
            <td>
                <div class="d-flex justify-content-center gap-1">
                    <button type="button" class="btn btn-sm btn-outline-danger delete-entry-btn" title="Delete Entry">
                        <i class="bi bi-trash"></i>
                    </button>
                    <input type="checkbox" name="entries-${formIndex}-DELETE" id="id_entries-${formIndex}-DELETE" style="display: none;">
                </div>
                <!-- Hidden fields -->
                <input type="hidden" name="entries-${formIndex}-entry_time" id="id_entries-${formIndex}-entry_time" value="12:00:00">
                <input type="hidden" name="entries-${formIndex}-paid_by" id="id_entries-${formIndex}-paid_by" value="Cash">
                <input type="hidden" name="entries-${formIndex}-attachment" id="id_entries-${formIndex}-attachment" value="">
            </td>
        </tr>
    `);
}

function deleteEntry(button) {
    const row = button.closest('.entry-row');
    const deleteCheckbox = row.find('input[name*="DELETE"]');
    
    if (deleteCheckbox.length > 0) {
        // Mark for deletion
        deleteCheckbox.prop('checked', true);
        row.addClass('table-danger').fadeOut(300);
    } else {
        // Remove immediately
        row.fadeOut(300, function() {
            $(this).remove();
            updateSerialNumbers();
            calculateRunningBalances();
        });
    }
    
    setTimeout(() => {
        updateSerialNumbers();
        calculateRunningBalances();
    }, 350);
}

function updateSerialNumbers() {
    $('#entriesTableBody .entry-row:visible').each(function(index) {
        $(this).find('td:first').text(index + 1);
    });
}

// Global flag to prevent duplicate submissions
let isSaving = false;

function savePettyCash() {
    // Prevent duplicate submissions
    if (isSaving) {
        return;
    }
    
    // Clear any previous error messages
    $('.alert').remove();
    
    if (!validateForm()) {
        showError('Please fix the validation errors before saving.');
        return;
    }
    
    // Set saving flag and show loading state
    isSaving = true;
    const saveBtn = $('#saveBtn');
    const originalText = saveBtn.html();
    saveBtn.html('<i class="bi bi-hourglass-split me-2"></i>Saving...').prop('disabled', true);
    
    // Submit form via AJAX
    const formData = new FormData($('#pettyCashForm')[0]);
    
    $.ajax({
        url: window.location.href,
        method: 'POST',
        data: formData,
        processData: false,
        contentType: false,
        success: function(response) {
            showSuccess('Petty cash entries saved successfully!');
            // Reload the page to show updated data
            setTimeout(() => {
                location.reload();
            }, 1500);
        },
        error: function(xhr) {
            console.error('Save error:', xhr);
            let errorMessage = 'Failed to save petty cash entries. Please try again.';
            
            if (xhr.status === 400) {
                try {
                    const response = JSON.parse(xhr.responseText);
                    if (response.errors) {
                        errorMessage = 'Validation errors: ' + Object.values(response.errors).join(', ');
                    } else {
                        errorMessage = 'Please check your entries for errors.';
                    }
                } catch (e) {
                    errorMessage = 'Please check your entries for errors.';
                }
            } else if (xhr.status === 403) {
                errorMessage = 'You do not have permission to save entries.';
            } else if (xhr.status === 500) {
                errorMessage = 'Server error occurred. Please try again later.';
            }
            
            showError(errorMessage);
        },
        complete: function() {
            // Reset saving flag and restore button state
            isSaving = false;
            saveBtn.html(originalText).prop('disabled', false);
        }
    });
}

function exportToPDF() {
    const selectedDate = $('#id_entry_date').val();
    const url = `/accounting/petty-cash/export/pdf/?date=${selectedDate}`;
    
    // Show loading state
    const exportBtn = $('#exportPdfBtn');
    const originalText = exportBtn.html();
    exportBtn.html('<i class="bi bi-hourglass-split me-2"></i>Generating...').prop('disabled', true);
    
    // Create a temporary link to download the PDF
    const link = document.createElement('a');
    link.href = url;
    link.download = `petty-cash-${selectedDate}.pdf`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    // Restore button state
    setTimeout(() => {
        exportBtn.html(originalText).prop('disabled', false);
        showSuccess('PDF export initiated!');
    }, 1000);
}

function exportToExcel() {
    const selectedDate = $('#id_entry_date').val();
    const url = `/accounting/petty-cash/export/excel/?date=${selectedDate}`;
    
    // Show loading state
    const exportBtn = $('#exportExcelBtn');
    const originalText = exportBtn.html();
    exportBtn.html('<i class="bi bi-hourglass-split me-2"></i>Generating...').prop('disabled', true);
    
    // Create a temporary link to download the Excel file
    const link = document.createElement('a');
    link.href = url;
    link.download = `petty-cash-${selectedDate}.xlsx`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    // Restore button state
    setTimeout(() => {
        exportBtn.html(originalText).prop('disabled', false);
        showSuccess('Excel export initiated!');
    }, 1000);
}

function printSummary() {
    window.print();
}

function initializeKeyboardShortcuts() {
    // Remove existing keydown handlers to prevent duplicates
    $(document).off('keydown.pettycash');
    
    $(document).on('keydown.pettycash', function(e) {
        // Ctrl/Cmd + S to save
        if ((e.ctrlKey || e.metaKey) && e.key === 's') {
            e.preventDefault();
            savePettyCash();
        }
        
        // Ctrl/Cmd + N to add new entry
        if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
            e.preventDefault();
            addNewEntry();
        }
        
        // Ctrl/Cmd + P to print
        if ((e.ctrlKey || e.metaKey) && e.key === 'p') {
            e.preventDefault();
            printSummary();
        }
    });
}

function addAnimations() {
    // Add fade-in animation to sections
    $('.register-header, .date-selector-section, .ledger-info, .entries-section, .action-buttons').addClass('fade-in');
    
    // Add hover effects to table rows
    $(document).on('mouseenter', '.entry-row', function() {
        $(this).addClass('table-hover');
    }).on('mouseleave', '.entry-row', function() {
        $(this).removeClass('table-hover');
    });
}

// Utility Functions
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-AE', {
        style: 'currency',
        currency: 'AED',
        minimumFractionDigits: 2
    }).format(amount).replace('AED', '').trim() + ' AED';
}

function getCSRFToken() {
    return $('[name=csrfmiddlewaretoken]').val();
}

function showSuccess(message) {
    // Create success toast
    const toast = $(`
        <div class="toast toast-success" role="alert">
            <div class="toast-header">
                <i class="bi bi-check-circle text-success me-2"></i>
                <strong class="me-auto">Success</strong>
                <button type="button" class="btn-close" data-bs-dismiss="toast"></button>
            </div>
            <div class="toast-body">${message}</div>
        </div>
    `);
    
    $('.toast-container').append(toast);
    new bootstrap.Toast(toast[0]).show();
}

function showError(message) {
    // Create error toast
    const toast = $(`
        <div class="toast toast-error" role="alert">
            <div class="toast-header">
                <i class="bi bi-exclamation-triangle text-danger me-2"></i>
                <strong class="me-auto">Error</strong>
                <button type="button" class="btn-close" data-bs-dismiss="toast"></button>
            </div>
            <div class="toast-body">${message}</div>
        </div>
    `);
    
    $('.toast-container').append(toast);
    new bootstrap.Toast(toast[0]).show();
}

function showInfo(message) {
    // Create info toast
    const toast = $(`
        <div class="toast toast-info" role="alert">
            <div class="toast-header">
                <i class="bi bi-info-circle text-info me-2"></i>
                <strong class="me-auto">Info</strong>
                <button type="button" class="btn-close" data-bs-dismiss="toast"></button>
            </div>
            <div class="toast-body">${message}</div>
        </div>
    `);
    
    $('.toast-container').append(toast);
    new bootstrap.Toast(toast[0]).show();
}

// CSS Animations
const style = document.createElement('style');
style.textContent = `
    .fade-in {
        animation: fadeIn 0.5s ease-in;
    }
    
    .slide-in {
        animation: slideIn 0.3s ease-out;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    @keyframes slideIn {
        from { opacity: 0; transform: translateX(-20px); }
        to { opacity: 1; transform: translateX(0); }
    }
    
    .table-hover {
        background-color: #f8f9fa !important;
        transition: background-color 0.2s ease;
    }
`;
document.head.appendChild(style);