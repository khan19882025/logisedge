// Approval Workflow Dashboard JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize dashboard functionality
    initDashboard();
});

function initDashboard() {
    // Initialize tooltips
    initTooltips();
    
    // Initialize data tables
    initDataTables();
    
    // Initialize real-time updates
    initRealTimeUpdates();
    
    // Initialize progress rings
    initProgressRings();
}

function initTooltips() {
    // Initialize Bootstrap tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

function initDataTables() {
    // Initialize DataTables for better table functionality
    const tables = document.querySelectorAll('.table');
    tables.forEach(function(table) {
        if (table.classList.contains('data-table')) {
            $(table).DataTable({
                responsive: true,
                pageLength: 10,
                order: [[0, 'desc']],
                language: {
                    search: "Search:",
                    lengthMenu: "Show _MENU_ entries",
                    info: "Showing _START_ to _END_ of _TOTAL_ entries",
                    paginate: {
                        first: "First",
                        previous: "Previous",
                        next: "Next",
                        last: "Last"
                    }
                }
            });
        }
    });
}

function initRealTimeUpdates() {
    // Set up real-time updates for dashboard stats
    setInterval(function() {
        updateDashboardStats();
    }, 30000); // Update every 30 seconds
}

function updateDashboardStats() {
    fetch('/approval-workflow/api/stats/')
        .then(response => response.json())
        .then(data => {
            // Update statistics cards
            updateStatCard('total-pending', data.total_pending);
            updateStatCard('my-pending', data.my_pending);
            updateStatCard('overdue-count', data.overdue_count);
            updateStatCard('approved-today', data.approved_today);
        })
        .catch(error => {
            console.error('Error updating dashboard stats:', error);
        });
}

function updateStatCard(cardId, value) {
    const card = document.getElementById(cardId);
    if (card) {
        const currentValue = card.textContent;
        if (currentValue != value) {
            // Add animation for value change
            card.style.transform = 'scale(1.1)';
            setTimeout(() => {
                card.textContent = value;
                card.style.transform = 'scale(1)';
            }, 150);
        }
    }
}

function initProgressRings() {
    // Initialize progress rings for approval progress
    const progressRings = document.querySelectorAll('.progress-ring');
    progressRings.forEach(function(ring) {
        const progress = ring.dataset.progress || 0;
        const circle = ring.querySelector('.progress-ring__progress');
        if (circle) {
            const radius = circle.r.baseVal.value;
            const circumference = radius * 2 * Math.PI;
            circle.style.strokeDasharray = `${circumference} ${circumference}`;
            circle.style.strokeDashoffset = circumference - (progress / 100) * circumference;
        }
    });
}

// Approval action functions
function approveRequest(requestId, action) {
    if (confirm(`Are you sure you want to ${action} this request?`)) {
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = `/approval-workflow/requests/${requestId}/approve/`;
        
        const actionInput = document.createElement('input');
        actionInput.type = 'hidden';
        actionInput.name = 'action';
        actionInput.value = action;
        
        const csrfInput = document.createElement('input');
        csrfInput.type = 'hidden';
        csrfInput.name = 'csrfmiddlewaretoken';
        csrfInput.value = getCookie('csrftoken');
        
        form.appendChild(actionInput);
        form.appendChild(csrfInput);
        document.body.appendChild(form);
        form.submit();
    }
}

// Utility function to get CSRF token
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

// Notification functions
function markNotificationAsRead(notificationId) {
    fetch(`/approval-workflow/notifications/${notificationId}/mark-read/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json',
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const notification = document.querySelector(`[data-notification-id="${notificationId}"]`);
            if (notification) {
                notification.classList.add('read');
            }
        }
    })
    .catch(error => {
        console.error('Error marking notification as read:', error);
    });
}

// Search and filter functionality
function initSearchFilters() {
    const searchInput = document.getElementById('search-requests');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            const tableRows = document.querySelectorAll('.table tbody tr');
            
            tableRows.forEach(function(row) {
                const text = row.textContent.toLowerCase();
                if (text.includes(searchTerm)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        });
    }
}

// Bulk actions
function initBulkActions() {
    const selectAllCheckbox = document.getElementById('select-all-requests');
    const requestCheckboxes = document.querySelectorAll('.request-checkbox');
    const bulkActionForm = document.getElementById('bulk-action-form');
    
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function() {
            requestCheckboxes.forEach(function(checkbox) {
                checkbox.checked = this.checked;
            });
            updateBulkActionButtons();
        });
    }
    
    requestCheckboxes.forEach(function(checkbox) {
        checkbox.addEventListener('change', function() {
            updateBulkActionButtons();
        });
    });
}

function updateBulkActionButtons() {
    const checkedBoxes = document.querySelectorAll('.request-checkbox:checked');
    const bulkButtons = document.querySelectorAll('.bulk-action-btn');
    
    bulkButtons.forEach(function(button) {
        if (checkedBoxes.length > 0) {
            button.disabled = false;
        } else {
            button.disabled = true;
        }
    });
}

// Export functionality
function exportRequests(format) {
    const selectedRequests = Array.from(document.querySelectorAll('.request-checkbox:checked'))
        .map(checkbox => checkbox.value);
    
    if (selectedRequests.length === 0) {
        alert('Please select at least one request to export.');
        return;
    }
    
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = `/approval-workflow/requests/export/${format}/`;
    
    const requestsInput = document.createElement('input');
    requestsInput.type = 'hidden';
    requestsInput.name = 'request_ids';
    requestsInput.value = selectedRequests.join(',');
    
    const csrfInput = document.createElement('input');
    csrfInput.type = 'hidden';
    csrfInput.name = 'csrfmiddlewaretoken';
    csrfInput.value = getCookie('csrftoken');
    
    form.appendChild(requestsInput);
    form.appendChild(csrfInput);
    document.body.appendChild(form);
    form.submit();
}

// Initialize all functions when page loads
document.addEventListener('DOMContentLoaded', function() {
    initSearchFilters();
    initBulkActions();
});
