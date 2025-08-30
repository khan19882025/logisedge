// Disciplinary & Grievance Dashboard JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize dashboard functionality
    initializeDashboard();
    
    // Add animation classes to cards
    addCardAnimations();
    
    // Initialize tooltips
    initializeTooltips();
    
    // Initialize real-time updates
    initializeRealTimeUpdates();
});

function initializeDashboard() {
    console.log('Initializing Disciplinary & Grievance Dashboard...');
    
    // Add loading states to buttons
    addLoadingStates();
    
    // Initialize status update functionality
    initializeStatusUpdates();
    
    // Initialize search functionality
    initializeSearch();
    
    // Initialize export functionality
    initializeExport();
}

function addCardAnimations() {
    // Add fade-in animation to cards
    const cards = document.querySelectorAll('.card');
    cards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
            card.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, index * 100);
    });
}

function initializeTooltips() {
    // Initialize Bootstrap tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

function addLoadingStates() {
    // Add loading state to buttons when clicked
    const buttons = document.querySelectorAll('.btn');
    buttons.forEach(button => {
        button.addEventListener('click', function() {
            if (!this.classList.contains('btn-disabled')) {
                const originalText = this.innerHTML;
                this.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Loading...';
                this.classList.add('btn-disabled');
                
                // Re-enable button after 3 seconds (for demo purposes)
                setTimeout(() => {
                    this.innerHTML = originalText;
                    this.classList.remove('btn-disabled');
                }, 3000);
            }
        });
    });
}

function initializeStatusUpdates() {
    // Add click handlers for status update buttons
    const statusButtons = document.querySelectorAll('[data-status-update]');
    statusButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            
            const grievanceId = this.getAttribute('data-grievance-id');
            const newStatus = this.getAttribute('data-status');
            
            updateGrievanceStatus(grievanceId, newStatus);
        });
    });
}

function updateGrievanceStatus(grievanceId, newStatus) {
    // Show loading state
    const button = document.querySelector(`[data-grievance-id="${grievanceId}"]`);
    const originalText = button.innerHTML;
    button.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Updating...';
    button.disabled = true;
    
    // Make AJAX request to update status
    fetch(`/disciplinary-grievance/api/grievances/${grievanceId}/status/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            status: newStatus
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update the status badge
            const statusBadge = document.querySelector(`[data-grievance-status="${grievanceId}"]`);
            if (statusBadge) {
                statusBadge.textContent = data.status;
                statusBadge.className = `badge badge-${newStatus}`;
            }
            
            // Show success message
            showNotification('Status updated successfully!', 'success');
        } else {
            showNotification('Failed to update status: ' + data.error, 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('An error occurred while updating status', 'error');
    })
    .finally(() => {
        // Restore button state
        button.innerHTML = originalText;
        button.disabled = false;
    });
}

function initializeSearch() {
    // Add search functionality to tables
    const searchInputs = document.querySelectorAll('.table-search');
    searchInputs.forEach(input => {
        input.addEventListener('keyup', function() {
            const searchTerm = this.value.toLowerCase();
            const tableId = this.getAttribute('data-table');
            const table = document.getElementById(tableId);
            
            if (table) {
                const rows = table.querySelectorAll('tbody tr');
                rows.forEach(row => {
                    const text = row.textContent.toLowerCase();
                    if (text.includes(searchTerm)) {
                        row.style.display = '';
                    } else {
                        row.style.display = 'none';
                    }
                });
            }
        });
    });
}

function initializeExport() {
    // Add export functionality
    const exportButtons = document.querySelectorAll('[data-export]');
    exportButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            
            const exportType = this.getAttribute('data-export');
            const tableId = this.getAttribute('data-table');
            
            exportTable(tableId, exportType);
        });
    });
}

function exportTable(tableId, exportType) {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    if (exportType === 'csv') {
        exportToCSV(table);
    } else if (exportType === 'pdf') {
        exportToPDF(table);
    }
}

function exportToCSV(table) {
    const rows = table.querySelectorAll('tr');
    let csv = [];
    
    rows.forEach(row => {
        const cols = row.querySelectorAll('td, th');
        const rowData = [];
        cols.forEach(col => {
            rowData.push('"' + col.textContent.replace(/"/g, '""') + '"');
        });
        csv.push(rowData.join(','));
    });
    
    const csvContent = csv.join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'disciplinary_grievance_data.csv';
    a.click();
    window.URL.revokeObjectURL(url);
}

function exportToPDF(table) {
    // This would require a PDF library like jsPDF
    // For now, we'll show a notification
    showNotification('PDF export functionality requires additional setup', 'info');
}

function initializeRealTimeUpdates() {
    // Set up real-time updates every 30 seconds
    setInterval(() => {
        updateDashboardStats();
    }, 30000);
}

function updateDashboardStats() {
    // Make AJAX request to get updated statistics
    fetch('/disciplinary-grievance/api/dashboard-stats/')
        .then(response => response.json())
        .then(data => {
            // Update statistics cards
            updateStatCard('total-grievances', data.total_grievances);
            updateStatCard('open-grievances', data.open_grievances);
            updateStatCard('resolved-grievances', data.resolved_grievances);
            updateStatCard('total-disciplinary-cases', data.total_disciplinary_cases);
            updateStatCard('open-disciplinary-cases', data.open_disciplinary_cases);
            updateStatCard('pending-appeals', data.pending_appeals);
        })
        .catch(error => {
            console.error('Error updating dashboard stats:', error);
        });
}

function updateStatCard(cardId, newValue) {
    const card = document.getElementById(cardId);
    if (card) {
        const valueElement = card.querySelector('.h5');
        if (valueElement) {
            const currentValue = parseInt(valueElement.textContent);
            if (currentValue !== newValue) {
                // Animate the value change
                animateValueChange(valueElement, currentValue, newValue);
            }
        }
    }
}

function animateValueChange(element, startValue, endValue) {
    const duration = 1000;
    const startTime = performance.now();
    
    function updateValue(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        
        const currentValue = Math.floor(startValue + (endValue - startValue) * progress);
        element.textContent = currentValue;
        
        if (progress < 1) {
            requestAnimationFrame(updateValue);
        }
    }
    
    requestAnimationFrame(updateValue);
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

// Utility functions for data formatting
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

function formatDateTime(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Chart initialization (if using charts)
function initializeCharts() {
    // This would initialize any charts if needed
    // Example: grievance trends, case distribution, etc.
    console.log('Charts initialized');
}

// Filter functionality
function filterTable(tableId, filterType, filterValue) {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    const rows = table.querySelectorAll('tbody tr');
    rows.forEach(row => {
        const cell = row.querySelector(`[data-${filterType}]`);
        if (cell) {
            const value = cell.getAttribute(`data-${filterType}`);
            if (filterValue === 'all' || value === filterValue) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        }
    });
}

// Sort functionality
function sortTable(tableId, columnIndex, sortType = 'string') {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    
    rows.sort((a, b) => {
        const aValue = a.cells[columnIndex].textContent.trim();
        const bValue = b.cells[columnIndex].textContent.trim();
        
        if (sortType === 'number') {
            return parseFloat(aValue) - parseFloat(bValue);
        } else if (sortType === 'date') {
            return new Date(aValue) - new Date(bValue);
        } else {
            return aValue.localeCompare(bValue);
        }
    });
    
    // Clear and re-append sorted rows
    rows.forEach(row => tbody.appendChild(row));
}

// Print functionality
function printTable(tableId) {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    const printWindow = window.open('', '_blank');
    printWindow.document.write(`
        <html>
            <head>
                <title>Disciplinary & Grievance Report</title>
                <style>
                    table { border-collapse: collapse; width: 100%; }
                    th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                    th { background-color: #f2f2f2; }
                    @media print { body { margin: 0; } }
                </style>
            </head>
            <body>
                <h2>Disciplinary & Grievance Report</h2>
                ${table.outerHTML}
            </body>
        </html>
    `);
    printWindow.document.close();
    printWindow.print();
}

// Export functions for different formats
function exportToExcel(tableId) {
    // This would require a library like SheetJS
    showNotification('Excel export requires additional setup', 'info');
}

// Initialize all functionality when page loads
window.addEventListener('load', function() {
    // Add any additional initialization here
    console.log('Dashboard fully loaded');
}); 