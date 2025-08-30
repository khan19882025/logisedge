// Cash Flow Statement Report JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize the application
    initCashFlowReport();
});

function initCashFlowReport() {
    // Add animation classes
    addAnimations();
    
    // Initialize form handlers
    initFormHandlers();
    
    // Initialize export functionality
    initExportHandlers();
    
    // Initialize responsive behavior
    initResponsiveBehavior();
    
    // Initialize tooltips
    initTooltips();
}

function addAnimations() {
    // Add fade-in animation to cards
    const cards = document.querySelectorAll('.card');
    cards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
            card.style.transition = 'all 0.5s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, index * 100);
    });
    
    // Add slide-up animation to tables
    const tables = document.querySelectorAll('.cash-flow-table');
    tables.forEach((table, index) => {
        table.style.opacity = '0';
        table.style.transform = 'translateY(30px)';
        
        setTimeout(() => {
            table.style.transition = 'all 0.6s ease';
            table.style.opacity = '1';
            table.style.transform = 'translateY(0)';
        }, (index + 2) * 100);
    });
}

function initFormHandlers() {
    // Quick report form handler
    const quickForm = document.getElementById('quickReportForm');
    if (quickForm) {
        quickForm.addEventListener('submit', function(e) {
            // Add loading state
            const submitBtn = this.querySelector('button[type="submit"]');
            const originalText = submitBtn.innerHTML;
            
            submitBtn.innerHTML = '<i class="bi bi-hourglass-split me-1"></i>Generating...';
            submitBtn.disabled = true;
            submitBtn.classList.add('loading');
            
            // Re-enable after a delay (in case of errors)
            setTimeout(() => {
                submitBtn.innerHTML = originalText;
                submitBtn.disabled = false;
                submitBtn.classList.remove('loading');
            }, 10000);
        });
    }
    
    // Date range validation
    const fromDateInput = document.querySelector('input[name="from_date"]');
    const toDateInput = document.querySelector('input[name="to_date"]');
    
    if (fromDateInput && toDateInput) {
        fromDateInput.addEventListener('change', validateDateRange);
        toDateInput.addEventListener('change', validateDateRange);
    }
    
    // Currency change handler
    const currencySelect = document.querySelector('select[name="currency"]');
    if (currencySelect) {
        currencySelect.addEventListener('change', function() {
            updateCurrencyDisplay(this.value);
        });
    }
}

function validateDateRange() {
    const fromDate = document.querySelector('input[name="from_date"]');
    const toDate = document.querySelector('input[name="to_date"]');
    
    if (fromDate.value && toDate.value) {
        const from = new Date(fromDate.value);
        const to = new Date(toDate.value);
        
        if (from > to) {
            showAlert('End date must be after start date', 'danger');
            toDate.value = '';
        }
        
        // Check if period is reasonable (not more than 5 years)
        const diffTime = Math.abs(to - from);
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
        
        if (diffDays > 1825) { // 5 years
            showAlert('Report period cannot exceed 5 years', 'warning');
        }
    }
}

function updateCurrencyDisplay(currencyCode) {
    // Update currency display in the UI
    const currencyElements = document.querySelectorAll('.currency-display');
    currencyElements.forEach(element => {
        element.textContent = currencyCode;
    });
}

function initExportHandlers() {
    // Export button handlers
    const exportButtons = document.querySelectorAll('.dropdown-item[href*="export"]');
    exportButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            
            const url = this.getAttribute('href');
            const format = this.textContent.trim();
            
            // Show loading state
            showAlert(`Exporting to ${format}...`, 'info');
            
            // Trigger download
            window.location.href = url;
            
            // Hide alert after delay
            setTimeout(() => {
                hideAlert();
            }, 3000);
        });
    });
    
    // Print functionality
    const printButtons = document.querySelectorAll('.btn-print');
    printButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            window.print();
        });
    });
}

function initResponsiveBehavior() {
    // Handle responsive table behavior
    const tables = document.querySelectorAll('.cash-flow-table');
    tables.forEach(table => {
        // Add horizontal scroll on small screens
        if (table.scrollWidth > table.clientWidth) {
            table.parentElement.style.overflowX = 'auto';
        }
    });
    
    // Handle mobile menu toggle
    const mobileMenuToggle = document.querySelector('.navbar-toggler');
    if (mobileMenuToggle) {
        mobileMenuToggle.addEventListener('click', function() {
            document.body.classList.toggle('menu-open');
        });
    }
}

function initTooltips() {
    // Initialize Bootstrap tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Utility Functions
function showAlert(message, type = 'info') {
    // Remove existing alerts
    hideAlert();
    
    // Create alert element
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // Add to page
    document.body.appendChild(alertDiv);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        hideAlert();
    }, 5000);
}

function hideAlert() {
    const alerts = document.querySelectorAll('.alert.position-fixed');
    alerts.forEach(alert => {
        alert.remove();
    });
}

// Number formatting
function formatCurrency(amount, currency = 'AED') {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: currency,
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(amount);
}

function formatNumber(number) {
    return new Intl.NumberFormat('en-US', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(number);
}

// Chart functionality (if needed)
function initCharts() {
    // Check if Chart.js is available
    if (typeof Chart !== 'undefined') {
        // Create cash flow chart
        const ctx = document.getElementById('cashFlowChart');
        if (ctx) {
            new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: ['Operating', 'Investing', 'Financing'],
                    datasets: [{
                        label: 'Cash Flow',
                        data: [0, 0, 0], // Will be populated with actual data
                        backgroundColor: [
                            'rgba(40, 167, 69, 0.8)',
                            'rgba(255, 193, 7, 0.8)',
                            'rgba(23, 162, 184, 0.8)'
                        ],
                        borderColor: [
                            'rgba(40, 167, 69, 1)',
                            'rgba(255, 193, 7, 1)',
                            'rgba(23, 162, 184, 1)'
                        ],
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        }
    }
}

// Data refresh functionality
function refreshReportData() {
    const refreshBtn = document.querySelector('.btn-refresh');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Add loading state
            this.innerHTML = '<i class="bi bi-arrow-clockwise me-1"></i>Refreshing...';
            this.disabled = true;
            
            // Reload the page
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        });
    }
}

// Save report functionality
function initSaveReport() {
    const saveForm = document.querySelector('form[action*="save"]');
    if (saveForm) {
        saveForm.addEventListener('submit', function(e) {
            const submitBtn = this.querySelector('button[type="submit"]');
            const originalText = submitBtn.innerHTML;
            
            submitBtn.innerHTML = '<i class="bi bi-save me-1"></i>Saving...';
            submitBtn.disabled = true;
            
            // Re-enable after delay
            setTimeout(() => {
                submitBtn.innerHTML = originalText;
                submitBtn.disabled = false;
            }, 5000);
        });
    }
}

// Keyboard shortcuts
function initKeyboardShortcuts() {
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + P for print
        if ((e.ctrlKey || e.metaKey) && e.key === 'p') {
            e.preventDefault();
            window.print();
        }
        
        // Ctrl/Cmd + S for save
        if ((e.ctrlKey || e.metaKey) && e.key === 's') {
            e.preventDefault();
            const saveBtn = document.querySelector('form[action*="save"] button[type="submit"]');
            if (saveBtn) {
                saveBtn.click();
            }
        }
        
        // Escape to close modals
        if (e.key === 'Escape') {
            const modals = document.querySelectorAll('.modal.show');
            modals.forEach(modal => {
                const modalInstance = bootstrap.Modal.getInstance(modal);
                if (modalInstance) {
                    modalInstance.hide();
                }
            });
        }
    });
}

// Initialize all functionality
document.addEventListener('DOMContentLoaded', function() {
    initCashFlowReport();
    refreshReportData();
    initSaveReport();
    initKeyboardShortcuts();
    
    // Initialize charts if data is available
    setTimeout(initCharts, 1000);
});

// Export functions for global use
window.CashFlowReport = {
    showAlert,
    hideAlert,
    formatCurrency,
    formatNumber,
    refreshReportData
};

// Quick Report Functions
function exportQuickReport(format) {
    // Get form data
    const form = document.getElementById('quickReportForm');
    if (!form) {
        showAlert('Form not found', 'danger');
        return;
    }
    
    const formData = new FormData(form);
    formData.append('export_format', format);
    
    // Show loading state
    showAlert(`Exporting to ${format}...`, 'info');
    
    // Send AJAX request to export quick report
    fetch('/reports/cash-flow/quick/export/', {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        }
    })
    .then(response => {
        if (response.ok) {
            return response.blob();
        }
        throw new Error('Export failed');
    })
    .then(blob => {
        // Create download link
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `cash_flow_quick_report.${format.toLowerCase()}`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        showAlert(`Export to ${format} completed successfully!`, 'success');
    })
    .catch(error => {
        console.error('Export error:', error);
        showAlert('Export failed. Please try again.', 'danger');
    });
}

function saveQuickReport() {
    // Get form data
    const form = document.getElementById('quickReportForm');
    if (!form) {
        showAlert('Form not found', 'danger');
        return;
    }
    
    const formData = new FormData(form);
    formData.append('save_report', 'true');
    
    // Show loading state
    showAlert('Saving report...', 'info');
    
    // Send AJAX request to save quick report
    fetch('/reports/cash-flow/quick/save/', {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('Report saved successfully!', 'success');
            // Redirect to the saved report
            setTimeout(() => {
                window.location.href = data.redirect_url;
            }, 1500);
        } else {
            showAlert(data.error || 'Failed to save report', 'danger');
        }
    })
    .catch(error => {
        console.error('Save error:', error);
        showAlert('Failed to save report. Please try again.', 'danger');
    });
} 