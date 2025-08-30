// Petty Cash Register JavaScript

// Global variables
let formsetIndex = 0;
let openingBalance = 0;

// Initialize the petty cash register
function initializePettyCashRegister() {
    initializeFormset();
    initializeDatePicker();
    initializeCalculations();
    initializeActionButtons();
    initializeKeyboardShortcuts();
    setupFormValidation();
    
    // Get opening balance
    openingBalance = parseFloat($('#openingBalance').val()) || 0;
    
    // Calculate initial balances
    updateAllBalances();
    
    console.log('Petty Cash Register initialized successfully');
}

// Initialize formset management
function initializeFormset() {
    const managementForm = $('#id_form-TOTAL_FORMS');
    if (managementForm.length) {
        formsetIndex = parseInt(managementForm.val()) || 0;
    }
    
    // Update form indices for existing rows
    $('#entriesTableBody .entry-row').each(function(index) {
        $(this).attr('data-form-index', index);
        updateFormIndices($(this), index);
    });
}

// Initialize date picker functionality
function initializeDatePicker() {
    $('#id_entry_date').on('change', function() {
        const selectedDate = $(this).val();
        if (selectedDate) {
            window.location.href = `?date=${selectedDate}`;
        }
    });
    
    // Navigation buttons
    $('.nav-prev').on('click', function() {
        navigateDate(-1);
    });
    
    $('.nav-next').on('click', function() {
        navigateDate(1);
    });
}

// Navigate to previous/next date
function navigateDate(direction) {
    const currentDate = new Date($('#id_entry_date').val());
    currentDate.setDate(currentDate.getDate() + direction);
    const newDate = currentDate.toISOString().split('T')[0];
    window.location.href = `?date=${newDate}`;
}

// Initialize calculations
function initializeCalculations() {
    // Bind amount input changes
    $(document).on('input', '.entry-row input[name$="-amount"]', function() {
        updateAllBalances();
        validateAmount($(this));
    });
    
    // Bind description input changes
    $(document).on('input', '.entry-row input[name$="-description"]', function() {
        validateDescription($(this));
    });
    
    // Bind job number input changes
    $(document).on('input', '.entry-row input[name$="-job_no"]', function() {
        validateJobNo($(this));
    });
    
    // Bind remarks input changes
    $(document).on('input', '.entry-row input[name$="-remarks"]', function() {
        validateRemarks($(this));
    });
}

// Validate amount input
function validateAmount(input) {
    const value = input.val().trim();
    const row = input.closest('.entry-row');
    
    // Remove existing error styling
    input.removeClass('is-invalid');
    row.find('.amount-error').remove();
    
    if (value && (isNaN(value) || parseFloat(value) <= 0)) {
        input.addClass('is-invalid');
        input.after('<div class="invalid-feedback amount-error">Please enter a valid positive amount</div>');
        return false;
    }
    
    return true;
}

// Validate description input
function validateDescription(input) {
    const value = input.val().trim();
    const row = input.closest('.entry-row');
    
    // Remove existing error styling
    input.removeClass('is-invalid');
    row.find('.description-error').remove();
    
    if (value.length > 0 && value.length < 3) {
        input.addClass('is-invalid');
        input.after('<div class="invalid-feedback description-error">Description must be at least 3 characters</div>');
        return false;
    }
    
    return true;
}

// Validate job number input
function validateJobNo(input) {
    const value = input.val().trim();
    const row = input.closest('.entry-row');
    
    // Remove existing error styling
    input.removeClass('is-invalid');
    row.find('.job-no-error').remove();
    
    // Job number is optional, but if provided should be valid format
    if (value && !/^[A-Za-z0-9-_]+$/.test(value)) {
        input.addClass('is-invalid');
        input.after('<div class="invalid-feedback job-no-error">Job number can only contain letters, numbers, hyphens, and underscores</div>');
        return false;
    }
    
    return true;
}

// Validate remarks input
function validateRemarks(input) {
    const value = input.val().trim();
    const row = input.closest('.entry-row');
    
    // Remove existing error styling
    input.removeClass('is-invalid');
    row.find('.remarks-error').remove();
    
    // Remarks is optional, but if provided should not be too long
    if (value && value.length > 200) {
        input.addClass('is-invalid');
        input.after('<div class="invalid-feedback remarks-error">Remarks cannot exceed 200 characters</div>');
        return false;
    }
    
    return true;
}

// Update all running balances with professional flow logic
function updateAllBalances() {
    // Get opening balance (previous day's running balance)
    const openingBalance = parseFloat($('#openingBalance').val()) || 0;
    let runningBalance = openingBalance;
    
    $('#entriesTableBody .entry-row').each(function() {
        const amountInput = $(this).find('input[name$="-amount"]');
        const balanceCell = $(this).find('.balance-cell');
        const amount = parseFloat(amountInput.val()) || 0;
        
        if (amount > 0) {
            runningBalance -= amount; // Subtract expense from balance
        }
        
        // Update balance cell
        balanceCell.text(formatCurrency(runningBalance));
        balanceCell.attr('data-balance', runningBalance);
        
        // Store current running balance for potential next day opening balance
        $('#runningBalanceValue').val(runningBalance.toFixed(2));
        
        // Add negative class if balance is negative
        if (runningBalance < 0) {
            balanceCell.addClass('negative');
        } else {
            balanceCell.removeClass('negative');
        }
    });
    
    // Update running balance display
    $('#runningBalance').text(formatCurrency(runningBalance) + ' AED');
}

// Initialize action buttons
function initializeActionButtons() {
    // Add new entry button
    $('#addNewEntryBtn').on('click', function() {
        addNewRow();
    });
    
    // Delete entry buttons
    $(document).on('click', '.delete-entry-btn', function() {
        deleteRow($(this).closest('.entry-row'));
    });
    
    // Save button
    $('#saveBtn').on('click', function() {
        saveForm();
    });
    
    // Export buttons
    $('#exportPdfBtn').on('click', function() {
        exportToPdf();
    });
    
    $('#exportExcelBtn').on('click', function() {
        exportToExcel();
    });
    
    // Print button
    $('.print-btn').on('click', function() {
        window.print();
    });
}

// Add new row to the table
function addNewRow() {
    const tableBody = $('#entriesTableBody');
    const newRowIndex = formsetIndex;
    
    const newRow = `
        <tr class="entry-row fade-in" data-form-index="${newRowIndex}">
            <td class="fw-semibold">${newRowIndex + 1}</td>
            <td>
                <input type="text" name="form-${newRowIndex}-job_no" class="form-control" placeholder="Job No">
            </td>
            <td>
                <input type="text" name="form-${newRowIndex}-description" class="form-control" placeholder="Enter description" required>
            </td>
            <td>
                <input type="text" name="form-${newRowIndex}-amount" class="form-control" placeholder="0.00" required>
            </td>
            <td>
                <input type="text" name="form-${newRowIndex}-remarks" class="form-control" placeholder="Remarks">
            </td>
            <td class="balance-cell" data-balance="0.00">0.00</td>
            <td>
                <div class="d-flex justify-content-center gap-1">
                    <button type="button" class="btn btn-sm btn-outline-danger delete-entry-btn" title="Delete Entry">
                        <i class="bi bi-trash"></i>
                    </button>
                    <input type="hidden" name="form-${newRowIndex}-DELETE" value="">
                </div>
            </td>
        </tr>
    `;
    
    tableBody.append(newRow);
    
    // Update formset management
    formsetIndex++;
    $('#id_form-TOTAL_FORMS').val(formsetIndex);
    
    // Update row numbers
    updateRowNumbers();
    
    // Focus on the new row's description field
    tableBody.find('.entry-row:last input[name$="-description"]').focus();
    
    // Update balances
    updateAllBalances();
    
    showToast('New entry row added successfully', 'success');
}

// Delete row from table
function deleteRow(row) {
    if ($('#entriesTableBody .entry-row').length <= 1) {
        showToast('Cannot delete the last remaining row', 'warning');
        return;
    }
    
    // Mark for deletion if it's an existing entry
    const deleteInput = row.find('input[name$="-DELETE"]');
    if (deleteInput.length) {
        deleteInput.val('on');
        row.hide().addClass('deleted');
    } else {
        row.remove();
        formsetIndex--;
        $('#id_form-TOTAL_FORMS').val(formsetIndex);
    }
    
    // Update row numbers and balances
    updateRowNumbers();
    updateAllBalances();
    
    showToast('Entry marked for deletion', 'info');
}

// Update row numbers
function updateRowNumbers() {
    $('#entriesTableBody .entry-row:visible').each(function(index) {
        $(this).find('td:first').text(index + 1);
    });
}

// Update form indices for a row
function updateFormIndices(row, index) {
    row.find('input, select, textarea').each(function() {
        const name = $(this).attr('name');
        if (name) {
            const newName = name.replace(/form-\d+/, `form-${index}`);
            $(this).attr('name', newName);
        }
        
        const id = $(this).attr('id');
        if (id) {
            const newId = id.replace(/form-\d+/, `form-${index}`);
            $(this).attr('id', newId);
        }
    });
}

// Setup form validation
function setupFormValidation() {
    $('#pettyCashForm').on('submit', function(e) {
        e.preventDefault();
        
        if (validateForm()) {
            saveForm();
        }
    });
}

// Validate entire form
function validateForm() {
    let isValid = true;
    
    // Validate all amount fields
    $('#entriesTableBody .entry-row:visible input[name$="-amount"]').each(function() {
        if (!validateAmount($(this))) {
            isValid = false;
        }
    });
    
    // Validate all description fields
    $('#entriesTableBody .entry-row:visible input[name$="-description"]').each(function() {
        if (!validateDescription($(this))) {
            isValid = false;
        }
    });
    
    // Validate all job number fields
    $('#entriesTableBody .entry-row:visible input[name$="-job_no"]').each(function() {
        if (!validateJobNo($(this))) {
            isValid = false;
        }
    });
    
    // Validate all remarks fields
    $('#entriesTableBody .entry-row:visible input[name$="-remarks"]').each(function() {
        if (!validateRemarks($(this))) {
            isValid = false;
        }
    });
    
    return isValid;
}

// Save form via AJAX
function saveForm() {
    if (!validateForm()) {
        showToast('Please fix validation errors before saving', 'error');
        return;
    }
    
    const formData = new FormData($('#pettyCashForm')[0]);
    
    $.ajax({
        url: window.location.href,
        type: 'POST',
        data: formData,
        processData: false,
        contentType: false,
        beforeSend: function() {
            $('#saveBtn').prop('disabled', true).html('<i class="bi bi-hourglass-split me-2"></i>Saving...');
        },
        success: function(response) {
            showToast('Petty cash entries saved successfully', 'success');
            // Reload page to refresh data
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        },
        error: function(xhr) {
            console.error('Save error:', xhr);
            showToast('Error saving entries. Please try again.', 'error');
        },
        complete: function() {
            $('#saveBtn').prop('disabled', false).html('<i class="bi bi-check-lg me-2"></i>Save');
        }
    });
}

// Export to PDF
function exportToPdf() {
    const selectedDate = $('#id_entry_date').val();
    const url = `/petty_cash/export/pdf/?date=${selectedDate}`;
    window.open(url, '_blank');
    showToast('PDF export initiated', 'info');
}

// Export to Excel
function exportToExcel() {
    const selectedDate = $('#id_entry_date').val();
    const url = `/petty_cash/export/excel/?date=${selectedDate}`;
    window.open(url, '_blank');
    showToast('Excel export initiated', 'info');
}

// Initialize keyboard shortcuts
function initializeKeyboardShortcuts() {
    $(document).on('keydown', function(e) {
        // Ctrl/Cmd + Enter to save
        if ((e.ctrlKey || e.metaKey) && e.keyCode === 13) {
            e.preventDefault();
            saveForm();
        }
        
        // Ctrl/Cmd + N to add new row
        if ((e.ctrlKey || e.metaKey) && e.keyCode === 78) {
            e.preventDefault();
            addNewRow();
        }
        
        // Escape to clear current input
        if (e.keyCode === 27) {
            $(document.activeElement).blur();
        }
    });
}

// Utility function to format currency
function formatCurrency(amount) {
    return parseFloat(amount).toFixed(2);
}

// Get CSRF token
function getCSRFToken() {
    return $('[name=csrfmiddlewaretoken]').val();
}

// Show toast notification
function showToast(message, type = 'info') {
    const toastId = 'toast-' + Date.now();
    const iconMap = {
        'success': 'bi-check-circle-fill',
        'error': 'bi-exclamation-triangle-fill',
        'warning': 'bi-exclamation-triangle-fill',
        'info': 'bi-info-circle-fill'
    };
    
    const bgMap = {
        'success': 'bg-success',
        'error': 'bg-danger',
        'warning': 'bg-warning',
        'info': 'bg-info'
    };
    
    const toast = `
        <div id="${toastId}" class="toast align-items-center text-white ${bgMap[type]} border-0" role="alert">
            <div class="d-flex">
                <div class="toast-body">
                    <i class="bi ${iconMap[type]} me-2"></i>
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        </div>
    `;
    
    $('.toast-container').append(toast);
    
    const toastElement = new bootstrap.Toast(document.getElementById(toastId));
    toastElement.show();
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        $(`#${toastId}`).remove();
    }, 5000);
}

// Auto-save functionality (optional)
let autoSaveTimeout;
function setupAutoSave() {
    $(document).on('input', '#entriesTableBody input', function() {
        clearTimeout(autoSaveTimeout);
        autoSaveTimeout = setTimeout(() => {
            if (validateForm()) {
                saveForm();
            }
        }, 2000); // Auto-save after 2 seconds of inactivity
    });
}

// Initialize when document is ready
$(document).ready(function() {
    initializePettyCashRegister();
    // Uncomment the line below to enable auto-save
    // setupAutoSave();
});