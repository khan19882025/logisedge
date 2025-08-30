// Chart of Accounts JavaScript

$(document).ready(function() {
    // Initialize all Chart of Accounts functionality
    initializeCOA();
});

function initializeCOA() {
    // Initialize search functionality
    initializeSearch();
    
    // Initialize form handling
    initializeForms();
    
    // Initialize hierarchy tree
    initializeHierarchy();
    
    // Initialize AJAX functionality
    initializeAJAX();
    
    // Initialize tooltips
    initializeTooltips();
}

// Search and Filter Functionality
function initializeSearch() {
    // Real-time search
    $('#search-term').on('input', function() {
        const searchTerm = $(this).val();
        if (searchTerm.length >= 2) {
            performSearch();
        } else if (searchTerm.length === 0) {
            clearSearch();
        }
    });
    
    // Filter changes
    $('.coa-search-panel select').on('change', function() {
        performSearch();
    });
    
    // Search button click
    $('.btn-search').on('click', function(e) {
        e.preventDefault();
        performSearch();
    });
    
    // Clear search
    $('.btn-clear-search').on('click', function(e) {
        e.preventDefault();
        clearSearch();
    });
}

function performSearch() {
    const searchData = {
        search_term: $('#search-term').val(),
        search_by: $('#search-by').val(),
        account_type: $('#account-type').val(),
        category: $('#category').val(),
        is_active: $('#is-active').val(),
        is_group: $('#is-group').val()
    };
    
    // Show loading state
    showLoading();
    
    $.ajax({
        url: window.location.pathname,
        method: 'GET',
        data: searchData,
        success: function(response) {
            // Update the table content
            updateTableContent(response);
            hideLoading();
        },
        error: function(xhr, status, error) {
            hideLoading();
            showError('Search failed. Please try again.');
        }
    });
}

function clearSearch() {
    $('#search-term').val('');
    $('#search-by').val('name');
    $('#account-type').val('');
    $('#category').val('');
    $('#is-active').val('');
    $('#is-group').val('');
    
    // Reload the page to show all accounts
    window.location.reload();
}

function updateTableContent(response) {
    // Extract table content from response
    const tableContent = $(response).find('.coa-table tbody').html();
    $('.coa-table tbody').html(tableContent);
    
    // Update pagination if present
    const pagination = $(response).find('.pagination').html();
    if (pagination) {
        $('.pagination').html(pagination);
    }
}

// Form Handling
function initializeForms() {
    // Parent account autocomplete
    initializeParentAccountAutocomplete();
    
    // Account code validation
    initializeAccountCodeValidation();
    
    // Dynamic form fields
    initializeDynamicFields();
    
    // Form submission handling
    initializeFormSubmission();
}

function initializeParentAccountAutocomplete() {
    $('#parent-account-code').autocomplete({
        source: function(request, response) {
            $.ajax({
                url: '/chart-of-accounts/ajax/parent-accounts/',
                method: 'GET',
                data: { q: request.term },
                success: function(data) {
                    response(data.results);
                }
            });
        },
        minLength: 2,
        select: function(event, ui) {
            $(this).val(ui.item.id);
            return false;
        }
    }).autocomplete("instance")._renderItem = function(ul, item) {
        return $("<li>")
            .append("<div><strong>" + item.id + "</strong><br>" + item.text.split(' - ')[1] + "</div>")
            .appendTo(ul);
    };
}

function initializeAccountCodeValidation() {
    $('#account-code').on('blur', function() {
        const accountCode = $(this).val();
        const currentId = $('#account-id').val(); // Hidden field for edit mode
        
        if (accountCode) {
            validateAccountCode(accountCode, currentId);
        }
    });
}

function validateAccountCode(accountCode, currentId) {
    $.ajax({
        url: '/chart-of-accounts/ajax/validate-account-code/',
        method: 'POST',
        data: {
            account_code: accountCode,
            current_id: currentId,
            csrfmiddlewaretoken: $('[name=csrfmiddlewaretoken]').val()
        },
        success: function(response) {
            if (response.valid) {
                showFieldSuccess('#account-code', 'Account code is available');
            } else {
                showFieldError('#account-code', response.error);
            }
        },
        error: function() {
            showFieldError('#account-code', 'Validation failed. Please try again.');
        }
    });
}

function initializeDynamicFields() {
    // Show/hide parent account field based on is_group
    $('#is-group').on('change', function() {
        const isGroup = $(this).is(':checked');
        if (isGroup) {
            $('#parent-account-field').hide();
            $('#parent-account-code').val('');
        } else {
            $('#parent-account-field').show();
        }
    });
    
    // Account type change handler
    $('#account-type').on('change', function() {
        const accountTypeId = $(this).val();
        if (accountTypeId) {
            updateAccountNatureOptions(accountTypeId);
        }
    });
}

function updateAccountNatureOptions(accountTypeId) {
    $.ajax({
        url: '/chart-of-accounts/ajax/account-type-nature/',
        method: 'GET',
        data: { account_type_id: accountTypeId },
        success: function(response) {
            const natureSelect = $('#account-nature');
            natureSelect.empty();
            
            response.natures.forEach(function(nature) {
                natureSelect.append(
                    $('<option></option>')
                        .val(nature.value)
                        .text(nature.label)
                );
            });
        }
    });
}

function initializeFormSubmission() {
    $('.coa-form').on('submit', function(e) {
        // Validate form before submission
        if (!validateForm($(this))) {
            e.preventDefault();
            return false;
        }
        
        // Show loading state
        showFormLoading($(this));
    });
}

function validateForm(form) {
    let isValid = true;
    
    // Clear previous errors
    form.find('.is-invalid').removeClass('is-invalid');
    form.find('.invalid-feedback').remove();
    
    // Required field validation
    form.find('[required]').each(function() {
        if (!$(this).val()) {
            $(this).addClass('is-invalid');
            $(this).after('<div class="invalid-feedback">This field is required.</div>');
            isValid = false;
        }
    });
    
    // Account code format validation
    const accountCode = form.find('#account-code').val();
    if (accountCode && !/^\d+$/.test(accountCode)) {
        form.find('#account-code').addClass('is-invalid');
        form.find('#account-code').after('<div class="invalid-feedback">Account code must contain only numbers.</div>');
        isValid = false;
    }
    
    return isValid;
}

// Hierarchy Tree Functionality
function initializeHierarchy() {
    // Expand/collapse tree nodes
    $('.account-tree-toggle').on('click', function(e) {
        e.preventDefault();
        const node = $(this).closest('.account-tree-node');
        const children = node.find('.account-tree-children');
        
        if (children.is(':visible')) {
            children.slideUp();
            $(this).find('i').removeClass('bi-chevron-down').addClass('bi-chevron-right');
        } else {
            children.slideDown();
            $(this).find('i').removeClass('bi-chevron-right').addClass('bi-chevron-down');
        }
    });
    
    // Load children dynamically
    $('.account-tree-node[data-has-children="true"]').on('click', function() {
        const nodeId = $(this).data('node-id');
        if (!$(this).hasClass('loaded')) {
            loadAccountChildren(nodeId, $(this));
        }
    });
}

function loadAccountChildren(parentId, parentNode) {
    $.ajax({
        url: '/chart-of-accounts/ajax/account-children/',
        method: 'GET',
        data: { parent_id: parentId },
        success: function(response) {
            const childrenContainer = parentNode.find('.account-tree-children');
            childrenContainer.html(response.html);
            parentNode.addClass('loaded');
        },
        error: function() {
            showError('Failed to load child accounts.');
        }
    });
}

// AJAX Functionality
function initializeAJAX() {
    // Account status toggle
    $('.account-status-toggle').on('change', function() {
        const accountId = $(this).data('account-id');
        const isActive = $(this).is(':checked');
        
        updateAccountStatus(accountId, isActive);
    });
    
    // Quick edit functionality
    $('.quick-edit-account').on('click', function(e) {
        e.preventDefault();
        const accountId = $(this).data('account-id');
        openQuickEditModal(accountId);
    });
    
    // Delete confirmation
    $('.delete-account').on('click', function(e) {
        e.preventDefault();
        const accountId = $(this).data('account-id');
        const accountName = $(this).data('account-name');
        
        if (confirm(`Are you sure you want to delete account "${accountName}"?`)) {
            deleteAccount(accountId);
        }
    });
}

function updateAccountStatus(accountId, isActive) {
    $.ajax({
        url: `/chart-of-accounts/ajax/accounts/${accountId}/status/`,
        method: 'POST',
        data: {
            is_active: isActive,
            csrfmiddlewaretoken: $('[name=csrfmiddlewaretoken]').val()
        },
        success: function(response) {
            if (response.success) {
                showSuccess(`Account status updated successfully.`);
            } else {
                showError('Failed to update account status.');
            }
        },
        error: function() {
            showError('Failed to update account status.');
        }
    });
}

function openQuickEditModal(accountId) {
    $.ajax({
        url: `/chart-of-accounts/ajax/accounts/${accountId}/details/`,
        method: 'GET',
        success: function(response) {
            // Populate modal with account details
            $('#quick-edit-modal').find('.modal-body').html(response.html);
            $('#quick-edit-modal').modal('show');
        },
        error: function() {
            showError('Failed to load account details.');
        }
    });
}

function deleteAccount(accountId) {
    $.ajax({
        url: `/chart-of-accounts/accounts/${accountId}/delete/`,
        method: 'POST',
        data: {
            csrfmiddlewaretoken: $('[name=csrfmiddlewaretoken]').val()
        },
        success: function(response) {
            if (response.success) {
                showSuccess('Account deleted successfully.');
                // Remove the row from the table
                $(`[data-account-id="${accountId}"]`).closest('tr').fadeOut();
            } else {
                showError(response.error || 'Failed to delete account.');
            }
        },
        error: function() {
            showError('Failed to delete account.');
        }
    });
}

// Utility Functions
function showLoading() {
    $('.coa-loading').show();
    $('.coa-table').addClass('loading');
}

function hideLoading() {
    $('.coa-loading').hide();
    $('.coa-table').removeClass('loading');
}

function showFormLoading(form) {
    const submitBtn = form.find('button[type="submit"]');
    submitBtn.prop('disabled', true);
    submitBtn.html('<i class="bi bi-hourglass-split"></i> Saving...');
}

function showSuccess(message) {
    // Create success alert
    const alert = $(`
        <div class="alert alert-success alert-dismissible fade show" role="alert">
            <i class="bi bi-check-circle"></i> ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `);
    
    // Add to page
    $('.container').prepend(alert);
    
    // Auto-dismiss after 5 seconds
    setTimeout(function() {
        alert.alert('close');
    }, 5000);
}

function showError(message) {
    // Create error alert
    const alert = $(`
        <div class="alert alert-danger alert-dismissible fade show" role="alert">
            <i class="bi bi-exclamation-triangle"></i> ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `);
    
    // Add to page
    $('.container').prepend(alert);
    
    // Auto-dismiss after 8 seconds
    setTimeout(function() {
        alert.alert('close');
    }, 8000);
}

function showFieldSuccess(fieldSelector, message) {
    const field = $(fieldSelector);
    field.removeClass('is-invalid').addClass('is-valid');
    field.siblings('.invalid-feedback').remove();
    field.siblings('.valid-feedback').remove();
    field.after(`<div class="valid-feedback">${message}</div>`);
}

function showFieldError(fieldSelector, message) {
    const field = $(fieldSelector);
    field.removeClass('is-valid').addClass('is-invalid');
    field.siblings('.invalid-feedback').remove();
    field.siblings('.valid-feedback').remove();
    field.after(`<div class="invalid-feedback">${message}</div>`);
}

function initializeTooltips() {
    // Initialize Bootstrap tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Export functionality
function exportAccounts(format) {
    const searchParams = new URLSearchParams(window.location.search);
    searchParams.append('format', format);
    
    window.location.href = `/chart-of-accounts/export-csv/?${searchParams.toString()}`;
}

// Print functionality
function printAccounts() {
    window.print();
}

// Keyboard shortcuts
$(document).on('keydown', function(e) {
    // Ctrl/Cmd + F for search
    if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
        e.preventDefault();
        $('#search-term').focus();
    }
    
    // Ctrl/Cmd + N for new account
    if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
        e.preventDefault();
        window.location.href = '/chart-of-accounts/accounts/create/';
    }
    
    // Escape to clear search
    if (e.key === 'Escape') {
        $('#search-term').val('');
        clearSearch();
    }
});

// Responsive table handling
function initializeResponsiveTable() {
    const table = $('.coa-table');
    
    if (table.length && window.innerWidth < 768) {
        // Make table responsive on mobile
        table.addClass('table-responsive');
        
        // Add horizontal scroll indicator
        if (table[0].scrollWidth > table[0].clientWidth) {
            table.after('<div class="text-muted small mt-2"><i class="bi bi-arrow-left-right"></i> Scroll horizontally to see more columns</div>');
        }
    }
}

// Initialize responsive table on load and resize
$(window).on('resize', initializeResponsiveTable);
initializeResponsiveTable(); 