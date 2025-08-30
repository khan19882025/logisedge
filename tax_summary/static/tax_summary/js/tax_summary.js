// Tax Summary App JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize date pickers
    initializeDatePickers();
    
    // Initialize form validation
    initializeFormValidation();
    
    // Initialize search functionality
    initializeSearch();
    
    // Initialize charts if Chart.js is available
    if (typeof Chart !== 'undefined') {
        initializeCharts();
    }
});

// Initialize date pickers
function initializeDatePickers() {
    const dateInputs = document.querySelectorAll('input[type="date"]');
    dateInputs.forEach(input => {
        // Set default values if empty
        if (!input.value) {
            const today = new Date();
            const formattedDate = today.toISOString().split('T')[0];
            input.value = formattedDate;
        }
        
        // Add change event listener
        input.addEventListener('change', function() {
            validateDateRange();
        });
    });
}

// Validate date range
function validateDateRange() {
    const startDate = document.getElementById('start_date');
    const endDate = document.getElementById('end_date');
    
    if (startDate && endDate && startDate.value && endDate.value) {
        const start = new Date(startDate.value);
        const end = new Date(endDate.value);
        
        if (start >= end) {
            endDate.setCustomValidity('End date must be after start date');
            showAlert('End date must be after start date', 'warning');
        } else {
            endDate.setCustomValidity('');
        }
    }
}

// Initialize form validation
function initializeFormValidation() {
    const forms = document.querySelectorAll('.needs-validation');
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });
}

// Initialize search functionality
function initializeSearch() {
    const searchInput = document.getElementById('search');
    if (searchInput) {
        let searchTimeout;
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                performSearch(this.value);
            }, 500);
        });
    }
}

// Perform search
function performSearch(query) {
    if (query.length < 2) return;
    
    // Show loading indicator
    showLoading();
    
    // Make AJAX request to search API
    fetch(`/tax-summary/api/search/?q=${encodeURIComponent(query)}`)
        .then(response => response.json())
        .then(data => {
            hideLoading();
            updateSearchResults(data);
        })
        .catch(error => {
            hideLoading();
            console.error('Search error:', error);
        });
}

// Update search results
function updateSearchResults(data) {
    const resultsContainer = document.getElementById('search-results');
    if (!resultsContainer) return;
    
    if (data.results && data.results.length > 0) {
        let html = '';
        data.results.forEach(result => {
            html += `
                <div class="search-result-item">
                    <h6>${result.report_name}</h6>
                    <p class="text-muted">${result.start_date} - ${result.end_date}</p>
                </div>
            `;
        });
        resultsContainer.innerHTML = html;
        resultsContainer.style.display = 'block';
    } else {
        resultsContainer.innerHTML = '<p class="text-muted">No results found</p>';
        resultsContainer.style.display = 'block';
    }
}

// Initialize charts
function initializeCharts() {
    const monthlyChart = document.getElementById('monthlyChart');
    if (monthlyChart) {
        const ctx = monthlyChart.getContext('2d');
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
                datasets: [{
                    label: 'Input Tax',
                    data: [12, 19, 3, 5, 2, 3, 7, 8, 9, 10, 11, 12],
                    borderColor: 'rgb(75, 192, 192)',
                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                    tension: 0.1
                }, {
                    label: 'Output Tax',
                    data: [8, 15, 7, 12, 9, 6, 11, 13, 15, 14, 16, 18],
                    borderColor: 'rgb(255, 99, 132)',
                    backgroundColor: 'rgba(255, 99, 132, 0.2)',
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                    },
                    title: {
                        display: true,
                        text: 'Monthly Tax Summary'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }
}

// Show loading indicator
function showLoading() {
    const loadingDiv = document.createElement('div');
    loadingDiv.id = 'loading-indicator';
    loadingDiv.className = 'loading-overlay';
    loadingDiv.innerHTML = `
        <div class="loading-spinner">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
        </div>
    `;
    document.body.appendChild(loadingDiv);
}

// Hide loading indicator
function hideLoading() {
    const loadingDiv = document.getElementById('loading-indicator');
    if (loadingDiv) {
        loadingDiv.remove();
    }
}

// Show alert
function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    const container = document.querySelector('.container-fluid');
    if (container) {
        container.insertBefore(alertDiv, container.firstChild);
        
        // Auto dismiss after 5 seconds
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    }
}

// Export functionality
function exportReport(reportId, format) {
    showLoading();
    
    fetch(`/tax-summary/reports/${reportId}/export/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            export_format: format
        })
    })
    .then(response => response.json())
    .then(data => {
        hideLoading();
        if (data.success) {
            showAlert('Report exported successfully!', 'success');
            // Trigger download if file URL is provided
            if (data.file_url) {
                window.open(data.file_url, '_blank');
            }
        } else {
            showAlert('Export failed: ' + data.error, 'danger');
        }
    })
    .catch(error => {
        hideLoading();
        showAlert('Export failed: ' + error.message, 'danger');
    });
}

// Get CSRF token
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

// Filter functionality
function applyFilters() {
    const form = document.getElementById('filter-form');
    if (form) {
        const formData = new FormData(form);
        const params = new URLSearchParams(formData);
        window.location.search = params.toString();
    }
}

// Clear filters
function clearFilters() {
    const form = document.getElementById('filter-form');
    if (form) {
        form.reset();
        window.location.search = '';
    }
}

// Generate report
function generateReport(reportId) {
    if (confirm('Are you sure you want to generate this report? This will process all transactions for the selected date range.')) {
        showLoading();
        
        fetch(`/tax-summary/reports/${reportId}/generate/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        })
        .then(response => response.json())
        .then(data => {
            hideLoading();
            if (data.success) {
                showAlert('Report generated successfully!', 'success');
                setTimeout(() => {
                    window.location.reload();
                }, 1500);
            } else {
                showAlert('Generation failed: ' + data.error, 'danger');
            }
        })
        .catch(error => {
            hideLoading();
            showAlert('Generation failed: ' + error.message, 'danger');
        });
    }
}

// Delete report
function deleteReport(reportId) {
    if (confirm('Are you sure you want to delete this report? This action cannot be undone.')) {
        fetch(`/tax-summary/reports/${reportId}/delete/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showAlert('Report deleted successfully!', 'success');
                setTimeout(() => {
                    window.location.href = '/tax-summary/reports/';
                }, 1500);
            } else {
                showAlert('Deletion failed: ' + data.error, 'danger');
            }
        })
        .catch(error => {
            showAlert('Deletion failed: ' + error.message, 'danger');
        });
    }
}

// Add CSS for loading overlay
const style = document.createElement('style');
style.textContent = `
    .loading-overlay {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.5);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 9999;
    }
    
    .loading-spinner {
        background: white;
        padding: 2rem;
        border-radius: 10px;
        box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
    }
    
    .search-result-item {
        padding: 0.5rem;
        border-bottom: 1px solid #e9ecef;
        cursor: pointer;
    }
    
    .search-result-item:hover {
        background-color: #f8f9fa;
    }
`;
document.head.appendChild(style);
