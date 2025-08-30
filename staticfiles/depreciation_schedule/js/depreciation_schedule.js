// Depreciation Schedule Module JavaScript

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
    
    // Initialize asset calculator
    initializeAssetCalculator();
    
    // Initialize depreciation calculation
    initializeDepreciationCalculation();
});

// Initialize date pickers
function initializeDatePickers() {
    const dateInputs = document.querySelectorAll('input[type="date"]');
    dateInputs.forEach(input => {
        if (!input.value) {
            const today = new Date();
            const firstDay = new Date(today.getFullYear(), today.getMonth(), 1);
            const lastDay = new Date(today.getFullYear(), today.getMonth() + 1, 0);
            
            if (input.name.includes('start_date')) {
                input.value = firstDay.toISOString().split('T')[0];
            } else if (input.name.includes('end_date')) {
                input.value = lastDay.toISOString().split('T')[0];
            }
        }
    });
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

// Initialize asset calculator
function initializeAssetCalculator() {
    const calculatorForm = document.getElementById('assetCalculatorForm');
    if (calculatorForm) {
        const assetSelect = document.getElementById('id_assets');
        const startDateInput = document.getElementById('id_start_date');
        const endDateInput = document.getElementById('id_end_date');
        const resultsDiv = document.getElementById('calculatorResults');
        
        if (assetSelect && startDateInput && endDateInput) {
            // Add event listeners for real-time calculation
            [assetSelect, startDateInput, endDateInput].forEach(element => {
                element.addEventListener('change', function() {
                    if (assetSelect.value && startDateInput.value && endDateInput.value) {
                        calculateAssetDepreciation();
                    }
                });
            });
        }
    }
}

// Calculate asset depreciation
function calculateAssetDepreciation() {
    const assetSelect = document.getElementById('id_assets');
    const startDateInput = document.getElementById('id_start_date');
    const endDateInput = document.getElementById('id_end_date');
    const resultsDiv = document.getElementById('calculatorResults');
    
    if (!assetSelect || !startDateInput || !endDateInput || !resultsDiv) return;
    
    const selectedAssets = Array.from(assetSelect.selectedOptions).map(option => option.value);
    const startDate = startDateInput.value;
    const endDate = endDateInput.value;
    
    if (selectedAssets.length === 0 || !startDate || !endDate) return;
    
    // Show loading spinner
    resultsDiv.innerHTML = '<div class="text-center"><div class="loading-spinner"></div><p>Calculating depreciation...</p></div>';
    
    // Make AJAX request
    fetch(`/depreciation-schedule/api/?action=get_asset_depreciation&asset_id=${selectedAssets[0]}&start_date=${startDate}&end_date=${endDate}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayCalculatorResults(data);
            } else {
                resultsDiv.innerHTML = `<div class="alert alert-danger">Error: ${data.error}</div>`;
            }
        })
        .catch(error => {
            resultsDiv.innerHTML = `<div class="alert alert-danger">Error: ${error.message}</div>`;
        });
}

// Display calculator results
function displayCalculatorResults(data) {
    const resultsDiv = document.getElementById('calculatorResults');
    if (!resultsDiv) return;
    
    const resultsHtml = `
        <div class="card">
            <div class="card-header">
                <h6 class="mb-0">Calculation Results</h6>
            </div>
            <div class="card-body">
                <div class="row">
                    <div class="col-md-6">
                        <p><strong>Asset:</strong> ${data.asset_code} - ${data.asset_name}</p>
                        <p><strong>Depreciation Amount:</strong> $${data.depreciation_amount.toLocaleString()}</p>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    resultsDiv.innerHTML = resultsHtml;
}

// Initialize depreciation calculation
function initializeDepreciationCalculation() {
    const calculateBtn = document.getElementById('calculateDepreciationBtn');
    if (calculateBtn) {
        calculateBtn.addEventListener('click', function(e) {
            e.preventDefault();
            
            if (!confirm('Are you sure you want to calculate depreciation for this schedule? This action cannot be undone.')) {
                return;
            }
            
            // Show loading spinner
            calculateBtn.innerHTML = '<span class="loading-spinner"></span> Calculating...';
            calculateBtn.disabled = true;
            
            // Submit the form
            const form = calculateBtn.closest('form');
            if (form) {
                form.submit();
            }
        });
    }
}

// Initialize depreciation posting
function initializeDepreciationPosting() {
    const postBtn = document.getElementById('postDepreciationBtn');
    if (postBtn) {
        postBtn.addEventListener('click', function(e) {
            e.preventDefault();
            
            if (!confirm('Are you sure you want to post depreciation to the general ledger? This action cannot be undone.')) {
                return;
            }
            
            // Show loading spinner
            postBtn.innerHTML = '<span class="loading-spinner"></span> Posting...';
            postBtn.disabled = true;
            
            // Submit the form
            const form = postBtn.closest('form');
            if (form) {
                form.submit();
            }
        });
    }
}

// Filter depreciation entries
function filterDepreciationEntries() {
    const filterForm = document.getElementById('depreciationEntryFilterForm');
    if (filterForm) {
        const formData = new FormData(filterForm);
        const params = new URLSearchParams(formData);
        
        // Update URL without page reload
        const currentUrl = new URL(window.location);
        currentUrl.search = params.toString();
        window.history.pushState({}, '', currentUrl);
        
        // Reload the page to apply filters
        window.location.reload();
    }
}

// Export depreciation data
function exportDepreciationData(format) {
    const scheduleId = document.getElementById('scheduleId').value;
    if (!scheduleId) return;
    
    const url = `/depreciation-schedule/schedules/${scheduleId}/export/?format=${format}`;
    window.open(url, '_blank');
}

// Initialize data tables
function initializeDataTables() {
    const tables = document.querySelectorAll('.depreciation-table');
    tables.forEach(table => {
        // Add sorting functionality
        const headers = table.querySelectorAll('th[data-sortable]');
        headers.forEach(header => {
            header.addEventListener('click', function() {
                const column = this.cellIndex;
                const rows = Array.from(table.querySelectorAll('tbody tr'));
                const isAscending = this.classList.contains('sort-asc');
                
                // Sort rows
                rows.sort((a, b) => {
                    const aValue = a.cells[column].textContent.trim();
                    const bValue = b.cells[column].textContent.trim();
                    
                    // Handle numeric values
                    const aNum = parseFloat(aValue.replace(/[^0-9.-]+/g, ''));
                    const bNum = parseFloat(bValue.replace(/[^0-9.-]+/g, ''));
                    
                    if (!isNaN(aNum) && !isNaN(bNum)) {
                        return isAscending ? bNum - aNum : aNum - bNum;
                    }
                    
                    // Handle text values
                    return isAscending ? bValue.localeCompare(aValue) : aValue.localeCompare(bValue);
                });
                
                // Reorder rows
                const tbody = table.querySelector('tbody');
                rows.forEach(row => tbody.appendChild(row));
                
                // Update header classes
                headers.forEach(h => h.classList.remove('sort-asc', 'sort-desc'));
                this.classList.add(isAscending ? 'sort-desc' : 'sort-asc');
            });
        });
    });
}

// Initialize search functionality
function initializeSearch() {
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            const table = document.querySelector('.depreciation-table');
            const rows = table.querySelectorAll('tbody tr');
            
            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(searchTerm) ? '' : 'none';
            });
        });
    }
}

// Initialize pagination
function initializePagination() {
    const paginationLinks = document.querySelectorAll('.pagination a');
    paginationLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const url = this.href;
            window.location.href = url;
        });
    });
}

// Initialize modal functionality
function initializeModals() {
    const modalTriggers = document.querySelectorAll('[data-bs-toggle="modal"]');
    modalTriggers.forEach(trigger => {
        trigger.addEventListener('click', function(e) {
            e.preventDefault();
            const targetModal = document.querySelector(this.getAttribute('data-bs-target'));
            if (targetModal) {
                const modal = new bootstrap.Modal(targetModal);
                modal.show();
            }
        });
    });
}

// Initialize form submission with confirmation
function initializeFormConfirmation() {
    const forms = document.querySelectorAll('form[data-confirm]');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const confirmMessage = this.getAttribute('data-confirm');
            if (confirmMessage && !confirm(confirmMessage)) {
                e.preventDefault();
            }
        });
    });
}

// Initialize auto-save functionality
function initializeAutoSave() {
    const autoSaveForms = document.querySelectorAll('form[data-auto-save]');
    autoSaveForms.forEach(form => {
        const inputs = form.querySelectorAll('input, textarea, select');
        let timeout;
        
        inputs.forEach(input => {
            input.addEventListener('input', function() {
                clearTimeout(timeout);
                timeout = setTimeout(() => {
                    // Save form data to localStorage
                    const formData = new FormData(form);
                    const data = {};
                    for (let [key, value] of formData.entries()) {
                        data[key] = value;
                    }
                    localStorage.setItem(`autosave_${form.id}`, JSON.stringify(data));
                }, 1000);
            });
        });
    });
}

// Initialize responsive tables
function initializeResponsiveTables() {
    const tables = document.querySelectorAll('.table-responsive');
    tables.forEach(table => {
        const wrapper = document.createElement('div');
        wrapper.className = 'table-responsive';
        table.parentNode.insertBefore(wrapper, table);
        wrapper.appendChild(table);
    });
}

// Initialize print functionality
function initializePrint() {
    const printButtons = document.querySelectorAll('.print-btn');
    printButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            window.print();
        });
    });
}

// Initialize export functionality
function initializeExport() {
    const exportButtons = document.querySelectorAll('.export-btn');
    exportButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const format = this.getAttribute('data-format');
            const scheduleId = this.getAttribute('data-schedule-id');
            if (format && scheduleId) {
                exportDepreciationData(format);
            }
        });
    });
}

// Initialize all functionality
function initializeAll() {
    initializeDatePickers();
    initializeFormValidation();
    initializeAssetCalculator();
    initializeDepreciationCalculation();
    initializeDepreciationPosting();
    initializeDataTables();
    initializeSearch();
    initializePagination();
    initializeModals();
    initializeFormConfirmation();
    initializeAutoSave();
    initializeResponsiveTables();
    initializePrint();
    initializeExport();
}

// Call initializeAll when DOM is loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeAll);
} else {
    initializeAll();
}
