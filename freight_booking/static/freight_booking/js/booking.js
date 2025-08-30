// Freight Booking Module JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all booking functionality
    initializeBookingFeatures();
});

function initializeBookingFeatures() {
    // Initialize quotation search
    initializeQuotationSearch();
    
    // Initialize document upload
    initializeDocumentUpload();
    
    // Initialize status change
    initializeStatusChange();
    
    // Initialize charge calculations
    initializeChargeCalculations();
    
    // Initialize form validation
    initializeFormValidation();
}

// Quotation Search Functionality
function initializeQuotationSearch() {
    const quotationSearch = document.getElementById('quotation-search');
    if (quotationSearch) {
        quotationSearch.addEventListener('input', debounce(function() {
            const query = this.value.trim();
            if (query.length >= 2) {
                searchQuotations(query);
            } else {
                clearQuotationResults();
            }
        }, 300));
    }
}

function searchQuotations(query) {
    fetch(`/freight-booking/ajax/search-quotations/?q=${encodeURIComponent(query)}`)
        .then(response => response.json())
        .then(data => {
            displayQuotationResults(data.results);
        })
        .catch(error => {
            console.error('Error searching quotations:', error);
        });
}

function displayQuotationResults(results) {
    const container = document.getElementById('quotation-results');
    if (!container) return;
    
    container.innerHTML = '';
    
    if (results.length === 0) {
        container.innerHTML = '<div class="text-muted">No quotations found</div>';
        return;
    }
    
    const ul = document.createElement('ul');
    ul.className = 'list-group';
    
    results.forEach(quotation => {
        const li = document.createElement('li');
        li.className = 'list-group-item list-group-item-action';
        li.textContent = quotation.text;
        li.addEventListener('click', () => selectQuotation(quotation.id));
        ul.appendChild(li);
    });
    
    container.appendChild(ul);
}

function selectQuotation(quotationId) {
    fetch(`/freight-booking/ajax/quotation/${quotationId}/`)
        .then(response => response.json())
        .then(data => {
            fillQuotationData(data);
        })
        .catch(error => {
            console.error('Error fetching quotation details:', error);
        });
}

function fillQuotationData(data) {
    // Fill form fields with quotation data
    if (data.customer_id) {
        document.getElementById('id_customer').value = data.customer_id;
    }
    
    if (data.origin) {
        const originParts = data.origin.split(', ');
        if (originParts.length >= 2) {
            document.getElementById('id_origin_city').value = originParts[0];
            document.getElementById('id_origin_country').value = originParts[1];
        }
    }
    
    if (data.destination) {
        const destParts = data.destination.split(', ');
        if (destParts.length >= 2) {
            document.getElementById('id_destination_city').value = destParts[0];
            document.getElementById('id_destination_country').value = destParts[1];
        }
    }
    
    if (data.cargo_details) {
        document.getElementById('id_cargo_description').value = data.cargo_details;
    }
    
    if (data.weight) {
        document.getElementById('id_weight').value = data.weight;
    }
    
    if (data.volume) {
        document.getElementById('id_volume').value = data.volume;
    }
    
    if (data.packages) {
        document.getElementById('id_packages').value = data.packages;
    }
    
    if (data.currency) {
        document.getElementById('id_currency').value = data.currency;
    }
    
    if (data.total_amount) {
        document.getElementById('id_freight_cost').value = data.total_amount;
    }
    
    // Clear search results
    clearQuotationResults();
}

function clearQuotationResults() {
    const container = document.getElementById('quotation-results');
    if (container) {
        container.innerHTML = '';
    }
}

// Document Upload Functionality
function initializeDocumentUpload() {
    const fileInput = document.querySelector('input[type="file"]');
    if (fileInput) {
        fileInput.addEventListener('change', handleFileSelect);
    }
    
    // Drag and drop functionality
    const dropZone = document.querySelector('.document-upload');
    if (dropZone) {
        dropZone.addEventListener('dragover', handleDragOver);
        dropZone.addEventListener('drop', handleDrop);
        dropZone.addEventListener('dragleave', handleDragLeave);
    }
}

function handleFileSelect(event) {
    const file = event.target.files[0];
    if (file) {
        validateAndUploadFile(file);
    }
}

function handleDragOver(event) {
    event.preventDefault();
    event.currentTarget.classList.add('dragover');
}

function handleDragLeave(event) {
    event.preventDefault();
    event.currentTarget.classList.remove('dragover');
}

function handleDrop(event) {
    event.preventDefault();
    event.currentTarget.classList.remove('dragover');
    
    const files = event.dataTransfer.files;
    if (files.length > 0) {
        validateAndUploadFile(files[0]);
    }
}

function validateAndUploadFile(file) {
    // File size validation (10MB)
    const maxSize = 10 * 1024 * 1024;
    if (file.size > maxSize) {
        showAlert('File size must be under 10MB', 'danger');
        return;
    }
    
    // File type validation
    const allowedTypes = ['.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png', '.xls', '.xlsx'];
    const fileName = file.name.toLowerCase();
    const isValidType = allowedTypes.some(type => fileName.endsWith(type));
    
    if (!isValidType) {
        showAlert('File type not allowed. Allowed types: ' + allowedTypes.join(', '), 'danger');
        return;
    }
    
    // Update filename display
    const filenameDisplay = document.getElementById('filename-display');
    if (filenameDisplay) {
        filenameDisplay.textContent = file.name;
    }
}

// Status Change Functionality
function initializeStatusChange() {
    const statusForm = document.getElementById('status-form');
    if (statusForm) {
        statusForm.addEventListener('submit', handleStatusChange);
    }
}

function handleStatusChange(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const bookingId = event.target.dataset.bookingId;
    
    fetch(`/freight-booking/${bookingId}/status/`, {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': getCSRFToken()
        }
    })
    .then(response => {
        if (response.ok) {
            location.reload();
        } else {
            throw new Error('Status change failed');
        }
    })
    .catch(error => {
        console.error('Error changing status:', error);
        showAlert('Failed to change status', 'danger');
    });
}

// Charge Calculations
function initializeChargeCalculations() {
    const freightCostInput = document.getElementById('id_freight_cost');
    const additionalCostsInput = document.getElementById('id_additional_costs');
    const totalCostDisplay = document.getElementById('total-cost-display');
    
    if (freightCostInput && additionalCostsInput && totalCostDisplay) {
        [freightCostInput, additionalCostsInput].forEach(input => {
            input.addEventListener('input', calculateTotalCost);
        });
    }
}

function calculateTotalCost() {
    const freightCost = parseFloat(document.getElementById('id_freight_cost').value) || 0;
    const additionalCosts = parseFloat(document.getElementById('id_additional_costs').value) || 0;
    const totalCost = freightCost + additionalCosts;
    
    const totalCostDisplay = document.getElementById('total-cost-display');
    if (totalCostDisplay) {
        totalCostDisplay.textContent = totalCost.toFixed(2);
    }
}

// Form Validation
function initializeFormValidation() {
    const bookingForm = document.getElementById('booking-form');
    if (bookingForm) {
        bookingForm.addEventListener('submit', validateBookingForm);
    }
}

function validateBookingForm(event) {
    const pickupDate = new Date(document.getElementById('id_pickup_date').value);
    const deliveryDate = new Date(document.getElementById('id_delivery_date').value);
    
    if (pickupDate > deliveryDate) {
        event.preventDefault();
        showAlert('Pickup date cannot be after delivery date', 'danger');
        return false;
    }
    
    return true;
}

// Utility Functions
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

function getCSRFToken() {
    const token = document.querySelector('[name=csrfmiddlewaretoken]');
    return token ? token.value : '';
}

function showAlert(message, type = 'info') {
    const alertContainer = document.getElementById('alert-container');
    if (!alertContainer) return;
    
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible fade show`;
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    alertContainer.appendChild(alert);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        if (alert.parentNode) {
            alert.remove();
        }
    }, 5000);
}

// Print Functionality
function printBooking(bookingId) {
    const printWindow = window.open(`/freight-booking/${bookingId}/print/`, '_blank');
    if (printWindow) {
        printWindow.onload = function() {
            printWindow.print();
        };
    }
}

// Export Functionality
function exportBookings(format = 'csv') {
    const searchParams = new URLSearchParams(window.location.search);
    searchParams.append('export', format);
    
    window.location.href = `/freight-booking/export/?${searchParams.toString()}`;
}

// Real-time Updates (if using WebSockets)
function initializeRealTimeUpdates() {
    // This would be implemented if using WebSockets for real-time updates
    // For now, we'll use polling for status updates
    setInterval(checkBookingUpdates, 30000); // Check every 30 seconds
}

function checkBookingUpdates() {
    const bookingElements = document.querySelectorAll('[data-booking-id]');
    bookingElements.forEach(element => {
        const bookingId = element.dataset.bookingId;
        fetch(`/freight-booking/${bookingId}/status-check/`)
            .then(response => response.json())
            .then(data => {
                updateBookingStatus(bookingId, data.status);
            })
            .catch(error => {
                console.error('Error checking booking status:', error);
            });
    });
}

function updateBookingStatus(bookingId, newStatus) {
    const statusElement = document.querySelector(`[data-booking-id="${bookingId}"] .status-badge`);
    if (statusElement) {
        statusElement.className = `badge bg-${newStatus}`;
        statusElement.textContent = newStatus.charAt(0).toUpperCase() + newStatus.slice(1);
    }
}

// Initialize everything when DOM is loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeBookingFeatures);
} else {
    initializeBookingFeatures();
}
