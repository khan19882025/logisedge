/**
 * SMS Gateway Dashboard JavaScript
 * Handles dashboard interactions, real-time updates, and dynamic functionality
 */

document.addEventListener('DOMContentLoaded', function() {
    'use strict';

    // Initialize dashboard components
    initializeDashboard();
    
    // Set up auto-refresh for real-time data
    setupAutoRefresh();
    
    // Initialize tooltips and popovers
    initializeBootstrapComponents();
    
    // Set up event listeners
    setupEventListeners();
});

/**
 * Initialize dashboard components
 */
function initializeDashboard() {
    console.log('Initializing SMS Gateway Dashboard...');
    
    // Update statistics with animation
    animateStatistics();
    
    // Initialize charts if available
    if (typeof Chart !== 'undefined') {
        initializeCharts();
    }
    
    // Set up real-time status indicators
    setupStatusIndicators();
}

/**
 * Animate statistics numbers
 */
function animateStatistics() {
    const statElements = document.querySelectorAll('.h5, .h4');
    
    statElements.forEach(element => {
        const finalValue = element.textContent;
        if (finalValue.includes('%') || finalValue.includes('s')) {
            // Skip elements with units
            return;
        }
        
        const numericValue = parseInt(finalValue.replace(/,/g, ''));
        if (!isNaN(numericValue)) {
            animateNumber(element, 0, numericValue, 1000);
        }
    });
}

/**
 * Animate number from start to end value
 */
function animateNumber(element, start, end, duration) {
    const startTime = performance.now();
    const difference = end - start;
    
    function updateNumber(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        
        // Easing function for smooth animation
        const easeOutQuart = 1 - Math.pow(1 - progress, 4);
        const current = Math.floor(start + (difference * easeOutQuart));
        
        element.textContent = current.toLocaleString();
        
        if (progress < 1) {
            requestAnimationFrame(updateNumber);
        }
    }
    
    requestAnimationFrame(updateNumber);
}

/**
 * Set up auto-refresh for real-time data
 */
function setupAutoRefresh() {
    const REFRESH_INTERVAL = 30000; // 30 seconds
    
    setInterval(() => {
        refreshDashboardData();
    }, REFRESH_INTERVAL);
}

/**
 * Refresh dashboard data via AJAX
 */
function refreshDashboardData() {
    // Show loading indicator
    showLoadingIndicator();
    
    // Fetch updated data
    fetch('/utilities/sms-gateway/api/health/')
        .then(response => response.json())
        .then(data => {
            updateDashboardData(data);
            hideLoadingIndicator();
        })
        .catch(error => {
            console.error('Error refreshing dashboard data:', error);
            hideLoadingIndicator();
        });
}

/**
 * Update dashboard with new data
 */
function updateDashboardData(data) {
    // Update gateway counts
    if (data.gateways) {
        updateElementText('.total-gateways', data.gateways.total);
        updateElementText('.active-gateways', data.gateways.active);
        updateElementText('.healthy-gateways', data.gateways.healthy);
    }
    
    // Update test statistics
    if (data.recent_tests) {
        updateElementText('.success-rate', data.recent_tests.success_rate + '%');
    }
    
    // Update timestamp
    updateLastUpdatedTime();
}

/**
 * Update element text with animation
 */
function updateElementText(selector, newValue) {
    const element = document.querySelector(selector);
    if (element) {
        const oldValue = element.textContent;
        if (oldValue !== newValue.toString()) {
            element.classList.add('updating');
            setTimeout(() => {
                element.textContent = newValue;
                element.classList.remove('updating');
            }, 200);
        }
    }
}

/**
 * Update last updated timestamp
 */
function updateLastUpdatedTime() {
    const now = new Date();
    const timeString = now.toLocaleTimeString();
    
    const timestampElement = document.querySelector('.last-updated');
    if (timestampElement) {
        timestampElement.textContent = `Last updated: ${timeString}`;
    }
}

/**
 * Set up status indicators
 */
function setupStatusIndicators() {
    const statusElements = document.querySelectorAll('.status-indicator');
    
    statusElements.forEach(element => {
        const status = element.dataset.status;
        updateStatusIndicator(element, status);
    });
}

/**
 * Update status indicator appearance
 */
function updateStatusIndicator(element, status) {
    element.classList.remove('status-healthy', 'status-unhealthy', 'status-warning');
    
    switch (status) {
        case 'success':
        case 'healthy':
            element.classList.add('status-healthy');
            element.innerHTML = '<i class="fas fa-check-circle"></i> Healthy';
            break;
        case 'failed':
        case 'unhealthy':
            element.classList.add('status-unhealthy');
            element.innerHTML = '<i class="fas fa-times-circle"></i> Unhealthy';
            break;
        case 'pending':
        case 'warning':
            element.classList.add('status-warning');
            element.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Warning';
            break;
        default:
            element.classList.add('status-unknown');
            element.innerHTML = '<i class="fas fa-question-circle"></i> Unknown';
    }
}

/**
 * Initialize Bootstrap components
 */
function initializeBootstrapComponents() {
    // Initialize tooltips
    if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
    
    // Initialize popovers
    if (typeof bootstrap !== 'undefined' && bootstrap.Popover) {
        const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
        popoverTriggerList.map(function (popoverTriggerEl) {
            return new bootstrap.Popover(popoverTriggerEl);
        });
    }
}

/**
 * Set up event listeners
 */
function setupEventListeners() {
    // Gateway test buttons
    const testButtons = document.querySelectorAll('.test-gateway-btn');
    testButtons.forEach(button => {
        button.addEventListener('click', handleGatewayTest);
    });
    
    // Refresh buttons
    const refreshButtons = document.querySelectorAll('.refresh-data-btn');
    refreshButtons.forEach(button => {
        button.addEventListener('click', refreshDashboardData);
    });
    
    // Search functionality
    const searchInput = document.querySelector('.search-input');
    if (searchInput) {
        searchInput.addEventListener('input', handleSearch);
    }
    
    // Filter functionality
    const filterSelects = document.querySelectorAll('.filter-select');
    filterSelects.forEach(select => {
        select.addEventListener('change', handleFilter);
    });
}

/**
 * Handle gateway test button clicks
 */
function handleGatewayTest(event) {
    event.preventDefault();
    
    const button = event.currentTarget;
    const gatewayId = button.dataset.gatewayId;
    
    if (!gatewayId) {
        console.error('No gateway ID found');
        return;
    }
    
    // Show loading state
    button.disabled = true;
    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Testing...';
    
    // Perform test
    testGateway(gatewayId)
        .then(result => {
            showTestResult(result);
            button.innerHTML = '<i class="fas fa-vial"></i> Test Gateway';
        })
        .catch(error => {
            showErrorMessage('Gateway test failed: ' + error.message);
            button.innerHTML = '<i class="fas fa-vial"></i> Test Gateway';
        })
        .finally(() => {
            button.disabled = false;
        });
}

/**
 * Test a specific gateway
 */
async function testGateway(gatewayId) {
    const response = await fetch(`/utilities/sms-gateway/gateways/${gatewayId}/test/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken(),
        },
        body: JSON.stringify({
            test_connection: true,
            test_authentication: true,
            test_message_send: false,
            test_unicode: false,
            test_rate_limits: false,
        })
    });
    
    if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    return await response.json();
}

/**
 * Show test result
 */
function showTestResult(result) {
    const alertContainer = document.querySelector('.alert-container') || createAlertContainer();
    
    let alertClass = 'alert-info';
    let icon = 'fas fa-info-circle';
    
    if (result.success) {
        alertClass = 'alert-success';
        icon = 'fas fa-check-circle';
    } else if (result.error) {
        alertClass = 'alert-danger';
        icon = 'fas fa-times-circle';
    }
    
    const alertHtml = `
        <div class="alert ${alertClass} alert-dismissible fade show" role="alert">
            <i class="${icon}"></i>
            <strong>Gateway Test Result:</strong> ${result.message || 'Test completed'}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    alertContainer.innerHTML = alertHtml + alertContainer.innerHTML;
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        const alert = alertContainer.querySelector('.alert');
        if (alert) {
            alert.remove();
        }
    }, 5000);
}

/**
 * Create alert container if it doesn't exist
 */
function createAlertContainer() {
    const container = document.createElement('div');
    container.className = 'alert-container';
    container.style.position = 'fixed';
    container.style.top = '20px';
    container.style.right = '20px';
    container.style.zIndex = '9999';
    container.style.maxWidth = '400px';
    
    document.body.appendChild(container);
    return container;
}

/**
 * Show error message
 */
function showErrorMessage(message) {
    const alertContainer = document.querySelector('.alert-container') || createAlertContainer();
    
    const alertHtml = `
        <div class="alert alert-danger alert-dismissible fade show" role="alert">
            <i class="fas fa-exclamation-triangle"></i>
            <strong>Error:</strong> ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    alertContainer.innerHTML = alertHtml + alertContainer.innerHTML;
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        const alert = alertContainer.querySelector('.alert');
        if (alert) {
            alert.remove();
        }
    }, 5000);
}

/**
 * Handle search input
 */
function handleSearch(event) {
    const searchTerm = event.target.value.toLowerCase();
    const tableRows = document.querySelectorAll('tbody tr');
    
    tableRows.forEach(row => {
        const text = row.textContent.toLowerCase();
        if (text.includes(searchTerm)) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
}

/**
 * Handle filter changes
 */
function handleFilter(event) {
    const filterValue = event.target.value;
    const filterType = event.target.dataset.filterType;
    
    // Implement filter logic based on filter type
    console.log(`Filtering by ${filterType}: ${filterValue}`);
    
    // Refresh data with filter
    refreshDashboardData();
}

/**
 * Show loading indicator
 */
function showLoadingIndicator() {
    const dashboard = document.querySelector('.container-fluid');
    if (dashboard) {
        dashboard.classList.add('loading');
    }
}

/**
 * Hide loading indicator
 */
function hideLoadingIndicator() {
    const dashboard = document.querySelector('.container-fluid');
    if (dashboard) {
        dashboard.classList.remove('loading');
    }
}

/**
 * Get CSRF token from cookies
 */
function getCSRFToken() {
    const name = 'csrftoken';
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

/**
 * Initialize charts if Chart.js is available
 */
function initializeCharts() {
    // Gateway health chart
    const healthCtx = document.getElementById('gatewayHealthChart');
    if (healthCtx) {
        new Chart(healthCtx, {
            type: 'doughnut',
            data: {
                labels: ['Healthy', 'Unhealthy', 'Warning'],
                datasets: [{
                    data: [12, 19, 3],
                    backgroundColor: [
                        '#1cc88a',
                        '#e74a3b',
                        '#f6c23e'
                    ],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }
    
    // Message delivery chart
    const deliveryCtx = document.getElementById('messageDeliveryChart');
    if (deliveryCtx) {
        new Chart(deliveryCtx, {
            type: 'line',
            data: {
                labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                datasets: [{
                    label: 'Delivery Rate',
                    data: [95, 97, 96, 98, 99, 97],
                    borderColor: '#4e73df',
                    backgroundColor: 'rgba(78, 115, 223, 0.1)',
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100
                    }
                }
            }
        });
    }
}

/**
 * Export dashboard data
 */
function exportDashboardData(format = 'csv') {
    const data = collectDashboardData();
    
    switch (format) {
        case 'csv':
            exportToCSV(data);
            break;
        case 'json':
            exportToJSON(data);
            break;
        case 'pdf':
            exportToPDF(data);
            break;
        default:
            console.error('Unsupported export format:', format);
    }
}

/**
 * Collect dashboard data for export
 */
function collectDashboardData() {
    return {
        timestamp: new Date().toISOString(),
        statistics: {
            total_gateways: document.querySelector('.total-gateways')?.textContent,
            active_gateways: document.querySelector('.active-gateways')?.textContent,
            healthy_gateways: document.querySelector('.healthy-gateways')?.textContent,
            success_rate: document.querySelector('.success-rate')?.textContent
        },
        gateway_health: Array.from(document.querySelectorAll('tbody tr')).map(row => {
            const cells = row.querySelectorAll('td');
            return {
                gateway: cells[0]?.textContent?.trim(),
                status: cells[1]?.textContent?.trim(),
                response_time: cells[2]?.textContent?.trim(),
                success_rate: cells[3]?.textContent?.trim()
            };
        })
    };
}

/**
 * Export data to CSV
 */
function exportToCSV(data) {
    const csvContent = convertToCSV(data);
    downloadFile(csvContent, 'sms_gateway_dashboard.csv', 'text/csv');
}

/**
 * Export data to JSON
 */
function exportToJSON(data) {
    const jsonContent = JSON.stringify(data, null, 2);
    downloadFile(jsonContent, 'sms_gateway_dashboard.json', 'application/json');
}

/**
 * Export data to PDF (placeholder)
 */
function exportToPDF(data) {
    console.log('PDF export not implemented yet');
    // This would require a PDF library like jsPDF
}

/**
 * Convert data to CSV format
 */
function convertToCSV(data) {
    // Implementation depends on data structure
    // This is a simplified version
    let csv = 'Timestamp,Total Gateways,Active Gateways,Healthy Gateways,Success Rate\n';
    csv += `${data.timestamp},${data.statistics.total_gateways},${data.statistics.active_gateways},${data.statistics.healthy_gateways},${data.statistics.success_rate}\n`;
    
    csv += '\nGateway,Status,Response Time,Success Rate\n';
    data.gateway_health.forEach(row => {
        csv += `${row.gateway},${row.status},${row.response_time},${row.success_rate}\n`;
    });
    
    return csv;
}

/**
 * Download file
 */
function downloadFile(content, filename, mimeType) {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
}

// Global error handler
window.addEventListener('error', function(event) {
    console.error('Global error:', event.error);
    showErrorMessage('An unexpected error occurred. Please check the console for details.');
});

// Unhandled promise rejection handler
window.addEventListener('unhandledrejection', function(event) {
    console.error('Unhandled promise rejection:', event.reason);
    showErrorMessage('An unexpected error occurred. Please check the console for details.');
});
