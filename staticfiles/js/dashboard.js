// Dashboard JavaScript for Shipment Tracking

document.addEventListener('DOMContentLoaded', function() {
    // Initialize dashboard functionality
    initializeDashboard();
    
    // Set up real-time updates (if WebSocket is available)
    if (typeof WebSocket !== 'undefined') {
        initializeRealTimeUpdates();
    }
    
    // Initialize search functionality
    initializeSearch();
    
    // Initialize quick actions
    initializeQuickActions();
});

function initializeDashboard() {
    // Add loading states to buttons
    const buttons = document.querySelectorAll('.btn');
    buttons.forEach(button => {
        button.addEventListener('click', function() {
            if (!this.classList.contains('btn-disabled')) {
                this.classList.add('loading');
            }
        });
    });
    
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Auto-refresh statistics every 5 minutes
    setInterval(refreshStatistics, 300000);
}

function initializeRealTimeUpdates() {
    // This would connect to a WebSocket for real-time updates
    // For now, we'll simulate with polling
    setInterval(checkForUpdates, 30000); // Check every 30 seconds
}

function initializeSearch() {
    const searchForm = document.getElementById('searchForm');
    if (searchForm) {
        searchForm.addEventListener('submit', function(e) {
            e.preventDefault();
            performSearch();
        });
    }
    
    // Auto-complete for search
    const searchInput = document.querySelector('input[name="search_query"]');
    if (searchInput) {
        searchInput.addEventListener('input', debounce(function() {
            if (this.value.length >= 2) {
                fetchSearchSuggestions(this.value);
            }
        }, 300));
    }
}

function initializeQuickActions() {
    // Quick status update functionality
    const quickUpdateForms = document.querySelectorAll('.quick-update-form');
    quickUpdateForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            submitQuickUpdate(this);
        });
    });
    
    // Bulk action checkboxes
    const selectAllCheckbox = document.getElementById('selectAll');
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function() {
            const checkboxes = document.querySelectorAll('.shipment-checkbox');
            checkboxes.forEach(checkbox => {
                checkbox.checked = this.checked;
            });
            updateBulkActions();
        });
    }
    
    // Individual checkboxes
    const checkboxes = document.querySelectorAll('.shipment-checkbox');
    checkboxes.forEach(checkbox => {
        checkbox.addEventListener('change', updateBulkActions);
    });
}

function performSearch() {
    const form = document.getElementById('searchForm');
    const formData = new FormData(form);
    const searchQuery = formData.get('search_query');
    const searchType = formData.get('search_type');
    
    // Show loading state
    const searchButton = form.querySelector('button[type="submit"]');
    const originalText = searchButton.innerHTML;
    searchButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Searching...';
    searchButton.disabled = true;
    
    // Perform search via AJAX
    fetch('/shipment-tracking/search/', {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            displaySearchResults(data.results);
        } else {
            showAlert('No results found for your search.', 'warning');
        }
    })
    .catch(error => {
        console.error('Search error:', error);
        showAlert('An error occurred while searching.', 'danger');
    })
    .finally(() => {
        // Restore button state
        searchButton.innerHTML = originalText;
        searchButton.disabled = false;
    });
}

function fetchSearchSuggestions(query) {
    fetch(`/shipment-tracking/api/search-suggestions/?q=${encodeURIComponent(query)}`)
        .then(response => response.json())
        .then(data => {
            displaySearchSuggestions(data.suggestions);
        })
        .catch(error => {
            console.error('Error fetching suggestions:', error);
        });
}

function displaySearchSuggestions(suggestions) {
    const suggestionsContainer = document.getElementById('searchSuggestions');
    if (!suggestionsContainer) return;
    
    suggestionsContainer.innerHTML = '';
    
    suggestions.forEach(suggestion => {
        const div = document.createElement('div');
        div.className = 'suggestion-item';
        div.textContent = suggestion;
        div.addEventListener('click', function() {
            document.querySelector('input[name="search_query"]').value = suggestion;
            suggestionsContainer.innerHTML = '';
        });
        suggestionsContainer.appendChild(div);
    });
}

function submitQuickUpdate(form) {
    const formData = new FormData(form);
    const shipmentId = form.dataset.shipmentId;
    
    // Show loading state
    const submitButton = form.querySelector('button[type="submit"]');
    const originalText = submitButton.innerHTML;
    submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Updating...';
    submitButton.disabled = true;
    
    fetch(`/shipment-tracking/${shipmentId}/quick-update/`, {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert(data.message, 'success');
            updateShipmentStatus(shipmentId, data.new_status, data.location, data.timestamp);
        } else {
            showAlert('Failed to update status. Please try again.', 'danger');
        }
    })
    .catch(error => {
        console.error('Update error:', error);
        showAlert('An error occurred while updating.', 'danger');
    })
    .finally(() => {
        // Restore button state
        submitButton.innerHTML = originalText;
        submitButton.disabled = false;
    });
}

function updateShipmentStatus(shipmentId, newStatus, location, timestamp) {
    // Update the status display in the UI
    const statusElement = document.querySelector(`[data-shipment-id="${shipmentId}"] .status-badge`);
    if (statusElement) {
        statusElement.textContent = newStatus;
        statusElement.className = `badge badge-${newStatus.toLowerCase().replace(' ', '_')}`;
    }
    
    // Update the timeline
    addTimelineEntry(shipmentId, newStatus, location, timestamp);
    
    // Update statistics
    refreshStatistics();
}

function addTimelineEntry(shipmentId, status, location, timestamp) {
    const timeline = document.querySelector('.timeline');
    if (!timeline) return;
    
    const timelineItem = document.createElement('div');
    timelineItem.className = 'timeline-item';
    timelineItem.innerHTML = `
        <div class="timeline-marker bg-${status.toLowerCase().replace(' ', '_')}"></div>
        <div class="timeline-content">
            <h6 class="timeline-title">
                <a href="/shipment-tracking/${shipmentId}/">${shipmentId}</a>
            </h6>
            <p class="timeline-text">
                <strong>${status}</strong><br>
                <small class="text-muted">
                    <i class="fas fa-map-marker-alt"></i> ${location}<br>
                    <i class="fas fa-clock"></i> ${timestamp}
                </small>
            </p>
        </div>
    `;
    
    // Add to the beginning of the timeline
    timeline.insertBefore(timelineItem, timeline.firstChild);
    
    // Remove old entries if there are too many
    const items = timeline.querySelectorAll('.timeline-item');
    if (items.length > 10) {
        timeline.removeChild(items[items.length - 1]);
    }
}

function updateBulkActions() {
    const checkedBoxes = document.querySelectorAll('.shipment-checkbox:checked');
    const bulkActionsContainer = document.getElementById('bulkActions');
    
    if (checkedBoxes.length > 0) {
        bulkActionsContainer.style.display = 'block';
        document.getElementById('selectedCount').textContent = checkedBoxes.length;
    } else {
        bulkActionsContainer.style.display = 'none';
    }
}

function performBulkAction(action) {
    const checkedBoxes = document.querySelectorAll('.shipment-checkbox:checked');
    const shipmentIds = Array.from(checkedBoxes).map(cb => cb.value);
    
    if (shipmentIds.length === 0) {
        showAlert('Please select at least one shipment.', 'warning');
        return;
    }
    
    if (!confirm(`Are you sure you want to ${action} ${shipmentIds.length} shipment(s)?`)) {
        return;
    }
    
    // Show loading state
    const actionButton = document.querySelector(`[data-action="${action}"]`);
    const originalText = actionButton.innerHTML;
    actionButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
    actionButton.disabled = true;
    
    fetch('/shipment-tracking/bulk-action/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            action: action,
            shipment_ids: shipmentIds
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert(data.message, 'success');
            location.reload(); // Refresh the page to show updated data
        } else {
            showAlert(data.message, 'danger');
        }
    })
    .catch(error => {
        console.error('Bulk action error:', error);
        showAlert('An error occurred while processing the bulk action.', 'danger');
    })
    .finally(() => {
        // Restore button state
        actionButton.innerHTML = originalText;
        actionButton.disabled = false;
    });
}

function refreshStatistics() {
    fetch('/shipment-tracking/api/statistics/')
        .then(response => response.json())
        .then(data => {
            updateStatisticsDisplay(data);
        })
        .catch(error => {
            console.error('Error refreshing statistics:', error);
        });
}

function updateStatisticsDisplay(data) {
    // Update statistics cards
    document.getElementById('totalShipments').textContent = data.total_shipments;
    document.getElementById('deliveredShipments').textContent = data.delivered_shipments;
    document.getElementById('inTransitShipments').textContent = data.in_transit_shipments;
    document.getElementById('onHoldShipments').textContent = data.on_hold_shipments;
    
    // Update chart if it exists
    if (window.statusChart) {
        window.statusChart.data.datasets[0].data = data.status_distribution.map(s => s.count);
        window.statusChart.update();
    }
}

function checkForUpdates() {
    // Check for new status updates
    fetch('/shipment-tracking/api/recent-updates/')
        .then(response => response.json())
        .then(data => {
            if (data.updates && data.updates.length > 0) {
                data.updates.forEach(update => {
                    addTimelineEntry(update.shipment_id, update.status, update.location, update.timestamp);
                });
                
                // Show notification
                showNotification('New status updates available');
            }
        })
        .catch(error => {
            console.error('Error checking for updates:', error);
        });
}

function showAlert(message, type) {
    const alertContainer = document.getElementById('alertContainer');
    if (!alertContainer) return;
    
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible fade show`;
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    alertContainer.appendChild(alert);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        if (alert.parentNode) {
            alert.remove();
        }
    }, 5000);
}

function showNotification(message) {
    // Check if browser supports notifications
    if ('Notification' in window && Notification.permission === 'granted') {
        new Notification('Shipment Tracking', {
            body: message,
            icon: '/static/img/logo.png'
        });
    }
    
    // Also show in-page notification
    const notification = document.createElement('div');
    notification.className = 'toast';
    notification.innerHTML = `
        <div class="toast-header">
            <strong class="me-auto">Shipment Tracking</strong>
            <button type="button" class="btn-close" data-bs-dismiss="toast"></button>
        </div>
        <div class="toast-body">
            ${message}
        </div>
    `;
    
    const toastContainer = document.getElementById('toastContainer');
    if (toastContainer) {
        toastContainer.appendChild(notification);
        const toast = new bootstrap.Toast(notification);
        toast.show();
    }
}

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

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Export functions for use in other scripts
window.ShipmentTracking = {
    performSearch,
    submitQuickUpdate,
    performBulkAction,
    refreshStatistics,
    showAlert,
    showNotification
};
