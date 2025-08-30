// Exit Management Dashboard JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize dashboard functionality
    initializeDashboard();
    
    // Auto-refresh statistics every 30 seconds
    setInterval(refreshStatistics, 30000);
});

function initializeDashboard() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Add click handlers for quick actions
    setupQuickActions();
    
    // Setup real-time updates
    setupRealTimeUpdates();
}

function setupQuickActions() {
    // Quick action buttons
    const quickActionButtons = document.querySelectorAll('.quick-action-btn');
    
    quickActionButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            
            const action = this.dataset.action;
            const url = this.href;
            
            // Show loading state
            this.classList.add('loading');
            this.disabled = true;
            
            // Perform action
            performQuickAction(action, url, this);
        });
    });
}

function performQuickAction(action, url, button) {
    fetch(url, {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Success', data.message, 'success');
            if (data.redirect) {
                setTimeout(() => {
                    window.location.href = data.redirect;
                }, 1000);
            }
        } else {
            showNotification('Error', data.message, 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Error', 'An error occurred while performing the action.', 'error');
    })
    .finally(() => {
        // Remove loading state
        button.classList.remove('loading');
        button.disabled = false;
    });
}

function setupRealTimeUpdates() {
    // Update statistics periodically
    const updateInterval = 30000; // 30 seconds
    
    setInterval(() => {
        updateDashboardStatistics();
    }, updateInterval);
}

function updateDashboardStatistics() {
    fetch('/exit-management/ajax/dashboard-stats/', {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            updateStatisticsDisplay(data.stats);
        }
    })
    .catch(error => {
        console.error('Error updating statistics:', error);
    });
}

function updateStatisticsDisplay(stats) {
    // Update total resignations
    const totalElement = document.querySelector('.total-resignations');
    if (totalElement && stats.total_resignations !== undefined) {
        totalElement.textContent = stats.total_resignations;
    }
    
    // Update pending resignations
    const pendingElement = document.querySelector('.pending-resignations');
    if (pendingElement && stats.pending_resignations !== undefined) {
        pendingElement.textContent = stats.pending_resignations;
    }
    
    // Update active clearances
    const activeElement = document.querySelector('.active-clearances');
    if (activeElement && stats.active_clearances !== undefined) {
        activeElement.textContent = stats.active_clearances;
    }
    
    // Update total gratuity
    const gratuityElement = document.querySelector('.total-gratuity');
    if (gratuityElement && stats.total_gratuity_paid !== undefined) {
        gratuityElement.textContent = `AED ${parseFloat(stats.total_gratuity_paid).toFixed(2)}`;
    }
}

function refreshStatistics() {
    // Refresh the entire dashboard
    location.reload();
}

function showNotification(title, message, type) {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `alert alert-${type === 'success' ? 'success' : 'danger'} alert-dismissible fade show position-fixed`;
    notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    
    notification.innerHTML = `
        <strong>${title}</strong><br>
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

// Chart configuration and updates
function updateCharts(data) {
    if (window.attritionChart && data.monthly_attrition) {
        updateAttritionChart(data.monthly_attrition);
    }
    
    if (window.reasonsChart && data.exit_reasons) {
        updateReasonsChart(data.exit_reasons);
    }
}

function updateAttritionChart(data) {
    const labels = data.map(item => item.month);
    const values = data.map(item => item.count);
    
    window.attritionChart.data.labels = labels;
    window.attritionChart.data.datasets[0].data = values;
    window.attritionChart.update();
}

function updateReasonsChart(data) {
    const labels = data.map(item => item.exit_type__name);
    const values = data.map(item => item.count);
    
    window.reasonsChart.data.labels = labels;
    window.reasonsChart.data.datasets[0].data = values;
    window.reasonsChart.update();
}

// Export functionality
function exportDashboardData(format) {
    const url = `/exit-management/export-dashboard/?format=${format}`;
    
    fetch(url, {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
        }
    })
    .then(response => {
        if (response.ok) {
            return response.blob();
        }
        throw new Error('Export failed');
    })
    .then(blob => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `exit-management-dashboard.${format}`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    })
    .catch(error => {
        console.error('Export error:', error);
        showNotification('Error', 'Failed to export dashboard data.', 'error');
    });
}

// Search functionality
function setupSearch() {
    const searchInput = document.getElementById('dashboard-search');
    if (searchInput) {
        searchInput.addEventListener('input', debounce(function() {
            const query = this.value.trim();
            if (query.length >= 2) {
                performSearch(query);
            } else if (query.length === 0) {
                clearSearch();
            }
        }, 300));
    }
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

function performSearch(query) {
    fetch(`/exit-management/search/?q=${encodeURIComponent(query)}`, {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            displaySearchResults(data.results);
        }
    })
    .catch(error => {
        console.error('Search error:', error);
    });
}

function displaySearchResults(results) {
    const resultsContainer = document.getElementById('search-results');
    if (!resultsContainer) return;
    
    if (results.length === 0) {
        resultsContainer.innerHTML = '<p class="text-muted">No results found.</p>';
        return;
    }
    
    let html = '<div class="list-group">';
    results.forEach(result => {
        html += `
            <a href="${result.url}" class="list-group-item list-group-item-action">
                <div class="d-flex w-100 justify-content-between">
                    <h6 class="mb-1">${result.title}</h6>
                    <small class="text-muted">${result.type}</small>
                </div>
                <p class="mb-1">${result.description}</p>
            </a>
        `;
    });
    html += '</div>';
    
    resultsContainer.innerHTML = html;
}

function clearSearch() {
    const resultsContainer = document.getElementById('search-results');
    if (resultsContainer) {
        resultsContainer.innerHTML = '';
    }
}

// Utility functions
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-AE', {
        style: 'currency',
        currency: 'AED'
    }).format(amount);
}

function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString('en-AE', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

function formatDateTime(dateString) {
    return new Date(dateString).toLocaleString('en-AE', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Initialize when DOM is loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeDashboard);
} else {
    initializeDashboard();
} 