// Asset Movement Log JavaScript

$(document).ready(function() {
    // Initialize tooltips
    $('[data-toggle="tooltip"]').tooltip();
    
    // Initialize date pickers
    $('input[type="date"]').datepicker({
        format: 'yyyy-mm-dd',
        autoclose: true,
        todayHighlight: true
    });
    
    // Initialize datetime pickers
    $('input[type="datetime-local"]').datetimepicker({
        format: 'Y-m-d H:i',
        step: 15
    });
    
    // Auto-fill current date for new movements
    if ($('#id_movement_date').length && !$('#id_movement_date').val()) {
        var now = new Date();
        var year = now.getFullYear();
        var month = String(now.getMonth() + 1).padStart(2, '0');
        var day = String(now.getDate()).padStart(2, '0');
        var hours = String(now.getHours()).padStart(2, '0');
        var minutes = String(now.getMinutes()).padStart(2, '0');
        $('#id_movement_date').val(year + '-' + month + '-' + day + 'T' + hours + ':' + minutes);
    }
    
    // Search functionality
    $('#search-input').on('keyup', function() {
        var value = $(this).val().toLowerCase();
        $('.table tbody tr').filter(function() {
            $(this).toggle($(this).text().toLowerCase().indexOf(value) > -1);
        });
    });
    
    // Filter functionality
    $('.filter-select').on('change', function() {
        var filterValue = $(this).val();
        var filterType = $(this).data('filter');
        
        if (filterValue) {
            $('.table tbody tr').hide();
            $('.table tbody tr').each(function() {
                var cellValue = $(this).find('td[data-' + filterType + ']').attr('data-' + filterType);
                if (cellValue === filterValue) {
                    $(this).show();
                }
            });
        } else {
            $('.table tbody tr').show();
        }
    });
    
    // Quick movement form
    $('#quick-movement-form').on('submit', function(e) {
        var asset = $('#id_asset').val();
        var toLocation = $('#id_to_location').val();
        
        if (!asset) {
            e.preventDefault();
            alert('Please select an asset.');
            return false;
        }
        
        if (!toLocation) {
            e.preventDefault();
            alert('Please select a destination location.');
            return false;
        }
    });
    
    // Asset selection change handler
    $('#id_asset').on('change', function() {
        var assetId = $(this).val();
        if (assetId) {
            // Fetch asset details via AJAX
            $.ajax({
                url: '/asset-movement-log/api/asset-details/',
                data: { asset_id: assetId },
                success: function(data) {
                    if (data.success) {
                        $('#id_from_location').val(data.current_location);
                        $('#id_from_user').val(data.assigned_to);
                    }
                }
            });
        }
    });
    
    // Movement type change handler
    $('#id_movement_type').on('change', function() {
        var movementType = $(this).val();
        
        // Show/hide relevant fields based on movement type
        if (movementType === 'assignment') {
            $('.to-user-field').show();
            $('.from-user-field').hide();
        } else if (movementType === 'return') {
            $('.to-user-field').hide();
            $('.from-user-field').show();
        } else {
            $('.to-user-field, .from-user-field').show();
        }
    });
    
    // Export functionality
    $('#export-form').on('submit', function(e) {
        var format = $('#id_export_format').val();
        var dateRange = $('#id_date_range').val();
        
        if (dateRange === 'custom') {
            var dateFrom = $('#id_custom_date_from').val();
            var dateTo = $('#id_custom_date_to').val();
            
            if (!dateFrom || !dateTo) {
                e.preventDefault();
                alert('Please select both start and end dates for custom range.');
                return false;
            }
        }
        
        // Show loading spinner
        $('#export-btn').html('<span class="loading-spinner"></span> Exporting...');
    });
    
    // Bulk actions
    $('.bulk-action-checkbox').on('change', function() {
        var checkedBoxes = $('.bulk-action-checkbox:checked');
        if (checkedBoxes.length > 0) {
            $('.bulk-actions').show();
        } else {
            $('.bulk-actions').hide();
        }
    });
    
    // Select all checkbox
    $('#select-all').on('change', function() {
        $('.bulk-action-checkbox').prop('checked', $(this).is(':checked'));
        $('.bulk-action-checkbox').trigger('change');
    });
    
    // Bulk delete
    $('#bulk-delete').on('click', function(e) {
        e.preventDefault();
        var checkedBoxes = $('.bulk-action-checkbox:checked');
        
        if (checkedBoxes.length === 0) {
            alert('Please select at least one movement to delete.');
            return false;
        }
        
        if (confirm('Are you sure you want to delete ' + checkedBoxes.length + ' selected movement(s)?')) {
            var movementIds = [];
            checkedBoxes.each(function() {
                movementIds.push($(this).val());
            });
            
            // Submit bulk delete form
            $('#bulk-delete-form input[name="movement_ids"]').val(movementIds.join(','));
            $('#bulk-delete-form').submit();
        }
    });
    
    // Movement status update
    $('.status-update').on('click', function(e) {
        e.preventDefault();
        var movementId = $(this).data('movement-id');
        var newStatus = $(this).data('status');
        
        $.ajax({
            url: '/asset-movement-log/api/update-status/',
            method: 'POST',
            data: {
                movement_id: movementId,
                status: newStatus,
                csrfmiddlewaretoken: $('[name=csrfmiddlewaretoken]').val()
            },
            success: function(data) {
                if (data.success) {
                    location.reload();
                } else {
                    alert('Error updating status: ' + data.error);
                }
            },
            error: function() {
                alert('Error updating status. Please try again.');
            }
        });
    });
    
    // Auto-save draft
    var autoSaveTimer;
    $('.movement-form input, .movement-form textarea, .movement-form select').on('change', function() {
        clearTimeout(autoSaveTimer);
        autoSaveTimer = setTimeout(function() {
            autoSaveDraft();
        }, 2000);
    });
    
    function autoSaveDraft() {
        var formData = $('.movement-form').serialize();
        $.ajax({
            url: '/asset-movement-log/api/save-draft/',
            method: 'POST',
            data: formData,
            success: function(data) {
                if (data.success) {
                    console.log('Draft saved successfully');
                }
            }
        });
    }
    
    // Movement validation
    $('.movement-form').on('submit', function(e) {
        var isValid = true;
        var errors = [];
        
        // Check required fields
        $(this).find('[required]').each(function() {
            if (!$(this).val()) {
                isValid = false;
                errors.push($(this).attr('name') + ' is required');
                $(this).addClass('is-invalid');
            } else {
                $(this).removeClass('is-invalid');
            }
        });
        
        // Check date validation
        var movementDate = $('#id_movement_date').val();
        var returnDate = $('#id_actual_return_date').val();
        
        if (movementDate && returnDate) {
            var movementDateTime = new Date(movementDate);
            var returnDateTime = new Date(returnDate);
            
            if (returnDateTime <= movementDateTime) {
                isValid = false;
                errors.push('Return date must be after movement date');
                $('#id_actual_return_date').addClass('is-invalid');
            }
        }
        
        if (!isValid) {
            e.preventDefault();
            alert('Please correct the following errors:\n' + errors.join('\n'));
            return false;
        }
    });
    
    // Real-time search
    var searchTimer;
    $('#search-input').on('input', function() {
        clearTimeout(searchTimer);
        var query = $(this).val();
        
        searchTimer = setTimeout(function() {
            if (query.length >= 2) {
                performSearch(query);
            } else if (query.length === 0) {
                clearSearch();
            }
        }, 300);
    });
    
    function performSearch(query) {
        $.ajax({
            url: '/asset-movement-log/api/search/',
            data: { q: query },
            success: function(data) {
                updateSearchResults(data.results);
            }
        });
    }
    
    function updateSearchResults(results) {
        var tbody = $('.table tbody');
        tbody.empty();
        
        if (results.length === 0) {
            tbody.append('<tr><td colspan="8" class="text-center">No results found</td></tr>');
        } else {
            results.forEach(function(movement) {
                var row = createMovementRow(movement);
                tbody.append(row);
            });
        }
    }
    
    function createMovementRow(movement) {
        return `
            <tr>
                <td>
                    <strong>${movement.asset_code}</strong><br>
                    <small class="text-muted">${movement.asset_name}</small>
                </td>
                <td>
                    <span class="badge badge-${movement.movement_type}">
                        ${movement.movement_type_display}
                    </span>
                </td>
                <td>${movement.from_location || '-'}</td>
                <td>${movement.to_location || '-'}</td>
                <td>${movement.movement_date}</td>
                <td>${movement.moved_by}</td>
                <td>
                    <span class="badge badge-${movement.is_completed ? 'success' : 'warning'}">
                        ${movement.is_completed ? 'Completed' : 'Pending'}
                    </span>
                </td>
                <td>
                    <div class="btn-group">
                        <a href="/asset-movement-log/movements/${movement.movement_id}/" 
                           class="btn btn-sm btn-info">
                            <i class="fas fa-eye"></i>
                        </a>
                    </div>
                </td>
            </tr>
        `;
    }
    
    function clearSearch() {
        location.reload();
    }
    
    // Initialize any additional plugins or functionality
    initializeAssetMovementLog();
});

function initializeAssetMovementLog() {
    // Add any additional initialization code here
    
    // Handle responsive table
    if ($(window).width() < 768) {
        $('.table-responsive').addClass('table-responsive-sm');
    }
    
    // Handle form validation
    $('.needs-validation').on('submit', function(e) {
        if (!this.checkValidity()) {
            e.preventDefault();
            e.stopPropagation();
        }
        $(this).addClass('was-validated');
    });
    
    // Handle modal functionality
    $('.modal-trigger').on('click', function(e) {
        e.preventDefault();
        var modalId = $(this).data('modal');
        $('#' + modalId).modal('show');
    });
    
    // Handle collapse functionality
    $('.collapse-trigger').on('click', function(e) {
        e.preventDefault();
        var target = $(this).data('target');
        $(target).collapse('toggle');
    });
}
