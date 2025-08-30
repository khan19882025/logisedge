/**
 * General Ledger Report JavaScript
 * Handles interactive features, AJAX calls, and UI enhancements
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all components
    initializeVoucherLinks();
    initializeExportButtons();
    initializePrintFunctionality();
    initializeResponsiveTable();
    initializeAnimations();
    initializeDatePresets();
    initializeAccountSearch();
});

/**
 * Initialize voucher detail links
 */
function initializeVoucherLinks() {
    const voucherLinks = document.querySelectorAll('.voucher-link');
    
    voucherLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const voucherNumber = this.getAttribute('data-voucher');
            showVoucherDetails(voucherNumber);
        });
    });
}

/**
 * Show voucher details in modal
 */
function showVoucherDetails(voucherNumber) {
    const modal = new bootstrap.Modal(document.getElementById('voucherModal'));
    const modalBody = document.getElementById('voucherModalBody');
    
    // Show loading state
    modalBody.innerHTML = `
        <div class="text-center py-4">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <p class="mt-2">Loading voucher details...</p>
        </div>
    `;
    
    modal.show();
    
    // Fetch voucher details via AJAX
    fetch(`/ledger/voucher/${voucherNumber}/details/`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                modalBody.innerHTML = `
                    <div class="voucher-details">
                        <div class="row">
                            <div class="col-md-6">
                                <h6>Voucher Information</h6>
                                <table class="table table-sm">
                                    <tr><td><strong>Number:</strong></td><td>${data.voucher.ledger_number}</td></tr>
                                    <tr><td><strong>Date:</strong></td><td>${data.voucher.entry_date}</td></tr>
                                    <tr><td><strong>Status:</strong></td><td><span class="badge bg-${data.voucher.status === 'POSTED' ? 'success' : 'warning'}">${data.voucher.status}</span></td></tr>
                                    <tr><td><strong>Type:</strong></td><td>${data.voucher.entry_type}</td></tr>
                                </table>
                            </div>
                            <div class="col-md-6">
                                <h6>Account Information</h6>
                                <table class="table table-sm">
                                    <tr><td><strong>Account:</strong></td><td>${data.voucher.account_code} - ${data.voucher.account_name}</td></tr>
                                    <tr><td><strong>Amount:</strong></td><td>${data.voucher.amount}</td></tr>
                                    <tr><td><strong>Balance:</strong></td><td>${data.voucher.running_balance}</td></tr>
                                </table>
                            </div>
                        </div>
                        <div class="row mt-3">
                            <div class="col-12">
                                <h6>Description</h6>
                                <p class="text-muted">${data.voucher.description}</p>
                            </div>
                        </div>
                    </div>
                `;
            } else {
                modalBody.innerHTML = `
                    <div class="text-center py-4">
                        <i class="fas fa-exclamation-triangle text-warning fa-2x mb-3"></i>
                        <p>Unable to load voucher details.</p>
                    </div>
                `;
            }
        })
        .catch(error => {
            console.error('Error fetching voucher details:', error);
            modalBody.innerHTML = `
                <div class="text-center py-4">
                    <i class="fas fa-exclamation-triangle text-danger fa-2x mb-3"></i>
                    <p>Error loading voucher details. Please try again.</p>
                </div>
            `;
        });
}

/**
 * Initialize export buttons
 */
function initializeExportButtons() {
    const exportButtons = document.querySelectorAll('[data-export-format]');
    
    exportButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const format = this.getAttribute('data-export-format');
            const reportId = this.getAttribute('data-report-id');
            
            // Show loading state
            this.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Exporting...';
            this.disabled = true;
            
            // Trigger export (convert format to lowercase)
            window.location.href = `/reports/general-ledger/${reportId}/export/?format=${format.toLowerCase()}`;
            
            // Reset button after a delay
            setTimeout(() => {
                this.innerHTML = `<i class="fas fa-download me-1"></i>${format}`;
                this.disabled = false;
            }, 3000);
        });
    });
}

/**
 * Initialize print functionality
 */
function initializePrintFunctionality() {
    const printButton = document.querySelector('[onclick="window.print()"]');
    
    if (printButton) {
        printButton.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Show print dialog
            window.print();
        });
    }
}

/**
 * Initialize responsive table features
 */
function initializeResponsiveTable() {
    const table = document.querySelector('.ledger-table');
    
    if (table) {
        // Add horizontal scroll indicator
        const tableContainer = table.closest('.table-responsive');
        
        if (tableContainer) {
            tableContainer.addEventListener('scroll', function() {
                const isAtEnd = this.scrollLeft + this.clientWidth >= this.scrollWidth;
                const isAtStart = this.scrollLeft === 0;
                
                // Add/remove scroll indicators
                this.classList.toggle('scroll-end', isAtEnd);
                this.classList.toggle('scroll-start', isAtStart);
            });
        }
        
        // Add row highlighting on hover
        const rows = table.querySelectorAll('tbody tr');
        rows.forEach(row => {
            row.addEventListener('mouseenter', function() {
                this.style.backgroundColor = '#f8f9fa';
            });
            
            row.addEventListener('mouseleave', function() {
                this.style.backgroundColor = '';
            });
        });
    }
}

/**
 * Initialize animations
 */
function initializeAnimations() {
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
    
    // Add slide-in animation to table rows
    const tableRows = document.querySelectorAll('.ledger-table tbody tr');
    tableRows.forEach((row, index) => {
        row.style.opacity = '0';
        row.style.transform = 'translateX(-20px)';
        
        setTimeout(() => {
            row.style.transition = 'all 0.3s ease';
            row.style.opacity = '1';
            row.style.transform = 'translateX(0)';
        }, 500 + (index * 50));
    });
}

/**
 * Initialize date preset functionality
 */
function initializeDatePresets() {
    const datePreset = document.getElementById('date-preset');
    const fromDate = document.getElementById('from-date');
    const toDate = document.getElementById('to-date');
    
    if (datePreset && fromDate && toDate) {
        datePreset.addEventListener('change', function() {
            const preset = this.value;
            const today = new Date();
            
            let startDate, endDate;
            
            switch (preset) {
                case 'today':
                    startDate = endDate = today;
                    break;
                case 'yesterday':
                    startDate = endDate = new Date(today.getTime() - 24 * 60 * 60 * 1000);
                    break;
                case 'this_week':
                    const dayOfWeek = today.getDay();
                    const diff = today.getDate() - dayOfWeek + (dayOfWeek === 0 ? -6 : 1);
                    startDate = new Date(today.setDate(diff));
                    endDate = today;
                    break;
                case 'last_week':
                    const lastWeekStart = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000);
                    const dayOfLastWeek = lastWeekStart.getDay();
                    const diffLastWeek = lastWeekStart.getDate() - dayOfLastWeek + (dayOfLastWeek === 0 ? -6 : 1);
                    startDate = new Date(lastWeekStart.setDate(diffLastWeek));
                    endDate = new Date(startDate.getTime() + 6 * 24 * 60 * 60 * 1000);
                    break;
                case 'this_month':
                    startDate = new Date(today.getFullYear(), today.getMonth(), 1);
                    endDate = today;
                    break;
                case 'last_month':
                    startDate = new Date(today.getFullYear(), today.getMonth() - 1, 1);
                    endDate = new Date(today.getFullYear(), today.getMonth(), 0);
                    break;
                case 'this_quarter':
                    const quarter = Math.floor(today.getMonth() / 3);
                    startDate = new Date(today.getFullYear(), quarter * 3, 1);
                    endDate = today;
                    break;
                case 'last_quarter':
                    const lastQuarter = Math.floor(today.getMonth() / 3) - 1;
                    if (lastQuarter < 0) {
                        startDate = new Date(today.getFullYear() - 1, 9, 1);
                        endDate = new Date(today.getFullYear() - 1, 11, 31);
                    } else {
                        startDate = new Date(today.getFullYear(), lastQuarter * 3, 1);
                        endDate = new Date(today.getFullYear(), (lastQuarter + 1) * 3, 0);
                    }
                    break;
                case 'this_year':
                    startDate = new Date(today.getFullYear(), 0, 1);
                    endDate = today;
                    break;
                case 'last_year':
                    startDate = new Date(today.getFullYear() - 1, 0, 1);
                    endDate = new Date(today.getFullYear() - 1, 11, 31);
                    break;
                default:
                    return; // Custom range - don't change dates
            }
            
            // Format dates for input fields
            fromDate.value = formatDateForInput(startDate);
            toDate.value = formatDateForInput(endDate);
        });
    }
}

/**
 * Initialize account search functionality
 */
function initializeAccountSearch() {
    const accountSelect = document.querySelector('select[name="account"]');
    
    if (accountSelect) {
        // Initialize Select2 if available
        if (typeof $.fn.select2 !== 'undefined') {
            $(accountSelect).select2({
                placeholder: 'Select Account',
                allowClear: true,
                ajax: {
                    url: '/reports/general-ledger/ajax/accounts/',
                    dataType: 'json',
                    delay: 250,
                    data: function(params) {
                        return {
                            search: params.term
                        };
                    },
                    processResults: function(data) {
                        return {
                            results: data.results
                        };
                    },
                    cache: true
                }
            });
        }
    }
}

/**
 * Format date for input field
 */
function formatDateForInput(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

/**
 * Format currency values
 */
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'AED',
        minimumFractionDigits: 2
    }).format(amount);
}

/**
 * Show notification message
 */
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 5000);
}

/**
 * Add loading state to element
 */
function addLoadingState(element) {
    element.classList.add('loading');
    element.style.position = 'relative';
}

/**
 * Remove loading state from element
 */
function removeLoadingState(element) {
    element.classList.remove('loading');
}

/**
 * Debounce function for performance
 */
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

/**
 * Throttle function for performance
 */
function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// Export functions for global use
window.GeneralLedgerReport = {
    showNotification,
    addLoadingState,
    removeLoadingState,
    formatCurrency,
    debounce,
    throttle
};