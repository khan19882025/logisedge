// HR Letters & Documents Dashboard JavaScript

document.addEventListener('DOMContentLoaded', function() {
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

    // Add loading states to buttons
    const buttons = document.querySelectorAll('.btn');
    buttons.forEach(button => {
        button.addEventListener('click', function() {
            if (!this.classList.contains('disabled')) {
                this.classList.add('loading');
                const originalText = this.innerHTML;
                this.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Loading...';
                
                // Remove loading state after a delay (for demo purposes)
                setTimeout(() => {
                    this.classList.remove('loading');
                    this.innerHTML = originalText;
                }, 2000);
            }
        });
    });

    // Card hover effects
    const cards = document.querySelectorAll('.card');
    cards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-5px)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });

    // Table row hover effects
    const tableRows = document.querySelectorAll('tbody tr');
    tableRows.forEach(row => {
        row.addEventListener('mouseenter', function() {
            this.style.backgroundColor = '#f8f9fc';
        });
        
        row.addEventListener('mouseleave', function() {
            this.style.backgroundColor = '';
        });
    });

    // Status badge animations
    const badges = document.querySelectorAll('.badge');
    badges.forEach(badge => {
        badge.addEventListener('click', function() {
            this.style.transform = 'scale(1.1)';
            setTimeout(() => {
                this.style.transform = 'scale(1)';
            }, 200);
        });
    });

    // Quick action button effects
    const quickActionButtons = document.querySelectorAll('.btn-block');
    quickActionButtons.forEach(button => {
        button.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-2px)';
            this.style.boxShadow = '0 4px 8px rgba(0, 0, 0, 0.2)';
        });
        
        button.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
            this.style.boxShadow = '';
        });
    });

    // Statistics counter animation
    function animateCounters() {
        const counters = document.querySelectorAll('.h5.mb-0.font-weight-bold');
        counters.forEach(counter => {
            const target = parseInt(counter.textContent);
            const increment = target / 50;
            let current = 0;
            
            const timer = setInterval(() => {
                current += increment;
                if (current >= target) {
                    current = target;
                    clearInterval(timer);
                }
                counter.textContent = Math.floor(current);
            }, 20);
        });
    }

    // Run counter animation when page loads
    animateCounters();

    // Refresh data periodically (every 30 seconds)
    setInterval(function() {
        refreshDashboardData();
    }, 30000);

    // Function to refresh dashboard data via AJAX
    function refreshDashboardData() {
        fetch(window.location.href)
            .then(response => response.text())
            .then(html => {
                const parser = new DOMParser();
                const doc = parser.parseFromString(html, 'text/html');
                
                // Update statistics
                const newStats = doc.querySelectorAll('.h5.mb-0.font-weight-bold');
                const currentStats = document.querySelectorAll('.h5.mb-0.font-weight-bold');
                
                newStats.forEach((stat, index) => {
                    if (currentStats[index] && stat.textContent !== currentStats[index].textContent) {
                        currentStats[index].textContent = stat.textContent;
                        currentStats[index].style.animation = 'pulse 0.5s';
                        setTimeout(() => {
                            currentStats[index].style.animation = '';
                        }, 500);
                    }
                });
            })
            .catch(error => {
                console.log('Error refreshing dashboard data:', error);
            });
    }

    // Search functionality for tables
    const searchInputs = document.querySelectorAll('input[type="search"]');
    searchInputs.forEach(input => {
        input.addEventListener('keyup', function() {
            const searchTerm = this.value.toLowerCase();
            const table = this.closest('.card').querySelector('table');
            const rows = table.querySelectorAll('tbody tr');
            
            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                if (text.includes(searchTerm)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        });
    });

    // Export functionality
    const exportButtons = document.querySelectorAll('.btn-export');
    exportButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const format = this.dataset.format;
            const table = this.closest('.card').querySelector('table');
            
            if (format === 'csv') {
                exportTableToCSV(table);
            } else if (format === 'pdf') {
                exportTableToPDF(table);
            }
        });
    });

    // Export table to CSV
    function exportTableToCSV(table) {
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
        a.download = 'hr_letters_data.csv';
        a.click();
        window.URL.revokeObjectURL(url);
    }

    // Export table to PDF (placeholder)
    function exportTableToPDF(table) {
        alert('PDF export functionality would be implemented here with a library like jsPDF');
    }

    // Notification system
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

    // Keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + N for new letter
        if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
            e.preventDefault();
            const newLetterBtn = document.querySelector('a[href*="letter_create"]');
            if (newLetterBtn) {
                newLetterBtn.click();
            }
        }
        
        // Ctrl/Cmd + T for templates
        if ((e.ctrlKey || e.metaKey) && e.key === 't') {
            e.preventDefault();
            const templatesBtn = document.querySelector('a[href*="letter_template_list"]');
            if (templatesBtn) {
                templatesBtn.click();
            }
        }
        
        // Ctrl/Cmd + D for documents
        if ((e.ctrlKey || e.metaKey) && e.key === 'd') {
            e.preventDefault();
            const documentsBtn = document.querySelector('a[href*="hr_document_list"]');
            if (documentsBtn) {
                documentsBtn.click();
            }
        }
    });

    // Responsive table handling
    function handleResponsiveTables() {
        const tables = document.querySelectorAll('.table-responsive');
        tables.forEach(table => {
            const tableElement = table.querySelector('table');
            if (tableElement && tableElement.scrollWidth > table.clientWidth) {
                table.style.overflowX = 'auto';
            }
        });
    }

    // Handle window resize
    window.addEventListener('resize', function() {
        handleResponsiveTables();
    });

    // Initialize responsive tables
    handleResponsiveTables();

    // Add pulse animation CSS
    const style = document.createElement('style');
    style.textContent = `
        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.05); }
            100% { transform: scale(1); }
        }
    `;
    document.head.appendChild(style);

    // Initialize any charts or graphs (if using Chart.js or similar)
    // This is a placeholder for future chart implementations
    function initializeCharts() {
        // Chart initialization code would go here
        console.log('Charts initialized');
    }

    // Call chart initialization
    initializeCharts();
}); 