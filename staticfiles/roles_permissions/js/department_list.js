// Department List JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Auto-submit search form on input change
    const searchInput = document.getElementById('search');
    if (searchInput) {
        let searchTimeout;
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                if (this.value.length >= 2 || this.value.length === 0) {
                    this.closest('form').submit();
                }
            }, 500);
        });
    }

    // Set page size function
    window.setPageSize = function(size) {
        const url = new URL(window.location);
        url.searchParams.set('page_size', size);
        url.searchParams.delete('page'); // Reset to first page
        window.location.href = url.toString();
    };

    // Export departments function
    window.exportDepartments = function() {
        const button = event.target.closest('button');
        const originalText = button.innerHTML;
        
        // Show loading state
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Exporting...';
        button.disabled = true;
        
        // Get current search parameters
        const url = new URL(window.location);
        url.searchParams.set('export', 'true');
        
        // Create a temporary link to trigger download
        const link = document.createElement('a');
        link.href = url.toString();
        link.download = 'departments.csv';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        // Reset button after a short delay
        setTimeout(() => {
            button.innerHTML = originalText;
            button.disabled = false;
        }, 2000);
    };

    // Table row click handler for better UX
    const tableRows = document.querySelectorAll('#departmentsTable tbody tr');
    tableRows.forEach(row => {
        row.addEventListener('click', function(e) {
            // Don't trigger if clicking on action buttons
            if (e.target.closest('.btn-group') || e.target.closest('a')) {
                return;
            }
            
            // Find the view details link and click it
            const viewLink = this.querySelector('a[href*="detail"]');
            if (viewLink) {
                viewLink.click();
            }
        });
        
        // Add cursor pointer to rows
        row.style.cursor = 'pointer';
    });

    // Keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + F to focus search
        if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
            e.preventDefault();
            const searchInput = document.getElementById('search');
            if (searchInput) {
                searchInput.focus();
                searchInput.select();
            }
        }
        
        // Escape to clear search
        if (e.key === 'Escape') {
            const searchInput = document.getElementById('search');
            if (searchInput && searchInput.value) {
                searchInput.value = '';
                searchInput.closest('form').submit();
            }
        }
    });

    // Add loading states to buttons
    const buttons = document.querySelectorAll('.btn');
    buttons.forEach(button => {
        button.addEventListener('click', function() {
            if (!this.disabled && !this.classList.contains('btn-link')) {
                this.classList.add('loading');
                setTimeout(() => {
                    this.classList.remove('loading');
                }, 1000);
            }
        });
    });

    // Enhanced table functionality
    const table = document.getElementById('departmentsTable');
    if (table) {
        // Add zebra striping
        const rows = table.querySelectorAll('tbody tr');
        rows.forEach((row, index) => {
            if (index % 2 === 1) {
                row.classList.add('table-striped');
            }
        });

        // Add hover effect
        rows.forEach(row => {
            row.addEventListener('mouseenter', function() {
                this.style.backgroundColor = '#f8f9fc';
            });
            
            row.addEventListener('mouseleave', function() {
                this.style.backgroundColor = '';
            });
        });
    }

    // Show notification function
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

    // Make showNotification available globally
    window.showNotification = showNotification;

    // Handle form submission feedback
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function() {
            const submitButton = this.querySelector('button[type="submit"]');
            if (submitButton) {
                const originalText = submitButton.innerHTML;
                submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
                submitButton.disabled = true;
                
                // Reset button after form submission (if not redirected)
                setTimeout(() => {
                    submitButton.innerHTML = originalText;
                    submitButton.disabled = false;
                }, 3000);
            }
        });
    });

    // Add confirmation for delete buttons
    const deleteButtons = document.querySelectorAll('a[href*="delete"]');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to delete this department? This action cannot be undone.')) {
                e.preventDefault();
            }
        });
    });

    // Responsive table handling
    function handleResponsiveTable() {
        const table = document.getElementById('departmentsTable');
        if (table && window.innerWidth < 768) {
            // Add horizontal scroll indicator
            if (!table.querySelector('.scroll-indicator')) {
                const indicator = document.createElement('div');
                indicator.className = 'scroll-indicator text-center text-muted mb-2';
                indicator.innerHTML = '<i class="fas fa-arrows-alt-h"></i> Scroll horizontally to see more columns';
                table.parentNode.insertBefore(indicator, table);
            }
        }
    }

    // Call on load and resize
    handleResponsiveTable();
    window.addEventListener('resize', handleResponsiveTable);

    // Add smooth scrolling for pagination
    const paginationLinks = document.querySelectorAll('.pagination a');
    paginationLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            // Smooth scroll to top
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });
    });

    console.log('Department list page initialized successfully');
});
