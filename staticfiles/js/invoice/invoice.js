// Invoice App JavaScript
console.log('🚀 Invoice JavaScript loaded - Version 1.3');

let invoiceAppInitialized = false;
let selectedJobsData = new Map(); // Track data for all selected jobs
let availableServices = []; // Store available services for description dropdown
let availableVendors = []; // Store available vendors for vendor dropdown
let availablePaymentSources = []; // Store available payment sources for payment source dropdown

document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, initializing invoice app...');
    
    // Initialize invoice functionality
    if (!invoiceAppInitialized) {
        initializeInvoiceApp();
        invoiceAppInitialized = true;
    }
    
    // Initialize additional functionality
    initializeSearchAndFilter();
    initializeTableActions();
    initializeVendorHandling();
});

function initializeInvoiceApp() {
    console.log('🔄 Initializing invoice app...');
    
    // Customer autocomplete
    initializeCustomerAutocomplete();
    
    // Simple sequential loading with better error handling
    console.log('🔄 Loading data...');
    
    // Step 1: Load vendors
    fetchVendors()
        .then((data) => {
            console.log('✅ Vendors loaded successfully');
            
            // Step 2: Load payment sources
            return fetchPaymentSources();
        })
        .then(() => {
            console.log('✅ Payment sources loaded successfully');
            
            // Step 3: Load services
            return fetchServices();
        })
        .then(() => {
            console.log('✅ Services loaded successfully');
            
            // Step 4: Initialize everything
            console.log('🔄 Initializing components...');
            initializeInvoiceItemsTable();
            
            // Step 5: Create initial row with loaded data
            if (availableVendors && availableVendors.length > 0) {
                console.log('✅ Creating initial row');
                createInitialRow();
                refreshVendorDropdowns();
            } else {
                console.log('⚠️ No vendors available, creating row anyway');
                createInitialRow();
            }
        })
        .catch(error => {
            console.error('❌ Error during data loading:', error);
            console.log('🔄 Continuing with minimal initialization...');
            
            // Continue anyway with what we have
            initializeInvoiceItemsTable();
            createInitialRow();
        });
    
    // Initialize other components
    initializeFormValidation();
    initializePrintFunctionality();
    initializeFormSubmission();
    initializeVendorHandling();
}

// Customer Autocomplete
function initializeCustomerAutocomplete() {
    const customerSelect = document.getElementById('id_customer');
    if (customerSelect) {
        customerSelect.addEventListener('change', function() {
            const customerId = this.value;
            if (customerId) {
                fetchCustomerDetails(customerId);
                fetchCustomerJobs(customerId);
            } else {
                // Clear jobs when no customer is selected
                clearJobsSelect();
                clearJobFields();
                selectedJobsData.clear(); // Clear selected jobs data
            }
        });
    }
}

function fetchCustomerDetails(customerId) {
    fetch(`/invoicing/invoice/ajax/get-customer-details/?customer_id=${customerId}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                console.error('Error:', data.error);
                return;
            }
            
            // Populate billing fields
            const billToField = document.getElementById('id_bill_to');
            const billToAddressField = document.getElementById('id_bill_to_address');
            
            if (billToField && !billToField.value) {
                billToField.value = data.customer_name;
            }
            if (billToAddressField && !billToAddressField.value) {
                billToAddressField.value = data.address;
            }
        })
        .catch(error => {
            console.error('Error fetching customer details:', error);
        });
}

function fetchCustomerJobs(customerId) {
    fetch(`/invoicing/invoice/ajax/get-customer-jobs/?customer_id=${customerId}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                console.error('Error:', data.error);
                return;
            }
            
            populateJobsSelect(data.jobs);
        })
        .catch(error => {
            console.error('Error fetching customer jobs:', error);
        });
}

function populateJobsSelect(jobs) {
    // Find the jobs container
    const container = document.getElementById('jobs-container');
    if (!container) return;
    
    // Clear existing options
    container.innerHTML = '';
    selectedJobsData.clear(); // Clear selected jobs data when customer changes
    
    // Add jobs as checkboxes
    jobs.forEach(job => {
        const div = document.createElement('div');
        div.className = 'form-check';
        div.innerHTML = `
            <input class="form-check-input job-checkbox" type="checkbox" name="jobs" value="${job.id}" id="job_${job.id}" data-job-id="${job.id}">
            <label class="form-check-label" for="job_${job.id}">
                ${job.job_code} - ${job.description}
            </label>
        `;
        container.appendChild(div);
    });
    
    // Add event listeners to job checkboxes
    addJobCheckboxListeners();
}

function addJobCheckboxListeners() {
    const jobCheckboxes = document.querySelectorAll('.job-checkbox');
    jobCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            if (this.checked) {
                // When a job is selected, fetch its details and populate fields
                fetchJobDetails(this.dataset.jobId);
            } else {
                // When a job is deselected, remove its data and recalculate
                selectedJobsData.delete(this.dataset.jobId);
                updateFieldsFromSelectedJobs();
            }
        });
    });
}

function fetchJobDetails(jobId) {
    console.log('fetchJobDetails called for jobId:', jobId);
    fetch(`/invoicing/invoice/ajax/get-job-details/?job_id=${jobId}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                console.error('Error:', data.error);
                return;
            }
            
            console.log('Job details received:', data);
            console.log('Items field in job data:', data.items);
            
            // Store job data
            selectedJobsData.set(jobId, data);
            
            // Update fields based on all selected jobs
            updateFieldsFromSelectedJobs();
        })
        .catch(error => {
            console.error('Error fetching job details:', error);
        });
}

function updateFieldsFromSelectedJobs() {
    console.log('updateFieldsFromSelectedJobs called');
    console.log('selectedJobsData size:', selectedJobsData.size);
    
    if (selectedJobsData.size === 0) {
        console.log('No selected jobs, clearing fields');
        clearJobFields();
        return;
    }
    
    // Get all job data
    const jobsData = Array.from(selectedJobsData.values());
    console.log('Jobs data:', jobsData);
    
    // Define fields to check (excluding items and total_qty which need special handling)
    const fields = [
        'bl_number', 'ed_number', 'container_number', 
        'origin', 'destination', 'shipper', 'consignee'
    ];
    
    // Handle regular fields
    fields.forEach(fieldName => {
        const values = jobsData.map(job => job[fieldName]).filter(val => val && val.trim() !== '');
        
        if (values.length === 0) {
            // No values found, clear the field
            clearField(fieldName);
        } else if (values.length === 1) {
            // Only one value, use it
            setFieldValue(fieldName, values[0]);
        } else {
            // Multiple values, check if they're all the same
            const uniqueValues = [...new Set(values)];
            if (uniqueValues.length === 1) {
                // All values are the same, use one
                setFieldValue(fieldName, uniqueValues[0]);
            } else {
                // Different values, show all separated by commas
                setFieldValue(fieldName, uniqueValues.join(', '));
            }
        }
    });
    
    // Handle Items field specially
    console.log('Calling handleItemsField with jobsData:', jobsData);
    handleItemsField(jobsData);
    
    // Handle Total Qty field specially
    handleTotalQtyField(jobsData);
}

function handleItemsField(jobsData) {
    console.log('handleItemsField called with jobsData:', jobsData);
    
    // Collect all item names from all selected jobs
    const allItems = new Set();
    
    jobsData.forEach(job => {
        console.log('Processing job:', job);
        if (job.items && job.items.trim() !== '') {
            console.log('Job has items:', job.items);
            // Split items by comma and add each item to the set
            const items = job.items.split(',').map(item => item.trim()).filter(item => item !== '');
            items.forEach(item => allItems.add(item));
        } else {
            console.log('Job has no items or empty items');
        }
    });
    
    console.log('All collected items:', Array.from(allItems));
    
    // Set the items field with all unique items
    const itemsField = document.getElementById('id_items_count');
    if (itemsField) {
        if (allItems.size > 0) {
            const itemsValue = Array.from(allItems).join(', ');
            itemsField.value = itemsValue;
            console.log('Set items_count field to:', itemsValue);
        } else {
            itemsField.value = '';
            console.log('Cleared items_count field');
        }
    } else {
        console.error('items_count field not found');
    }
}

function handleTotalQtyField(jobsData) {
    // Sum up total quantities from all selected jobs
    let totalQty = 0;
    
    jobsData.forEach(job => {
        if (job.total_qty && !isNaN(parseFloat(job.total_qty))) {
            totalQty += parseFloat(job.total_qty);
        }
    });
    
    // Set the total qty field
    const totalQtyField = document.getElementById('id_total_qty');
    if (totalQtyField) {
        totalQtyField.value = totalQty.toFixed(2);
    }
}

function setFieldValue(fieldName, value) {
    const fieldId = `id_${fieldName}`;
    const field = document.getElementById(fieldId);
    if (field) {
        field.value = value;
    }
}

function clearField(fieldName) {
    const fieldId = `id_${fieldName}`;
    const field = document.getElementById(fieldId);
    if (field) {
        field.value = '';
    }
}

function populateJobFields(jobData) {
    // This function is now replaced by updateFieldsFromSelectedJobs()
    // Keeping for backward compatibility but it's not used
}

function clearJobFields() {
    // Clear BL Number
    const blField = document.getElementById('id_bl_number');
    if (blField) {
        blField.value = '';
    }
    
    // Clear ED Number
    const edField = document.getElementById('id_ed_number');
    if (edField) {
        edField.value = '';
    }
    
    // Clear Container Number
    const containerField = document.getElementById('id_container_number');
    if (containerField) {
        containerField.value = '';
    }
    
    // Clear Items (names)
    const itemsField = document.getElementById('id_items_count');
    if (itemsField) {
        itemsField.value = '';
    }
    
    // Clear Total Qty
    const totalQtyField = document.getElementById('id_total_qty');
    if (totalQtyField) {
        totalQtyField.value = '';
    }
    
    // Clear Origin
    const originField = document.getElementById('id_origin');
    if (originField) {
        originField.value = '';
    }
    
    // Clear Destination
    const destinationField = document.getElementById('id_destination');
    if (destinationField) {
        destinationField.value = '';
    }
    
    // Clear Shipper
    const shipperField = document.getElementById('id_shipper');
    if (shipperField) {
        shipperField.value = '';
    }
    
    // Clear Consignee
    const consigneeField = document.getElementById('id_consignee');
    if (consigneeField) {
        consigneeField.value = '';
    }
}

function clearJobsSelect() {
    const container = document.getElementById('jobs-container');
    if (container) {
        container.innerHTML = '';
    }
    selectedJobsData.clear(); // Clear selected jobs data
}

// Invoice Items Table Functionality
function initializeInvoiceItemsTable() {
    const tbody = document.getElementById('invoice-items-tbody');
    if (!tbody) return;
    
    // Check if we're editing an existing invoice with invoice items data
    const hiddenField = document.getElementById('id_invoice_items');
    if (hiddenField && hiddenField.value) {
        try {
            const existingItems = JSON.parse(hiddenField.value);
            if (existingItems && Array.isArray(existingItems) && existingItems.length > 0) {
                console.log('Found existing invoice items:', existingItems);
                populateInvoiceItemsTable(existingItems);
                return; // Don't create initial row if we have existing data
            }
        } catch (e) {
            console.error('Error parsing existing invoice items:', e);
        }
    }
    
    // Create initial row if no existing data
    // Note: This will be called after vendors are loaded in initializeInvoiceApp
    if (availableVendors && availableVendors.length > 0) {
        createInitialRow();
    } else {
        console.log('Vendors not loaded yet, will create initial row later');
    }
    
    // Add event listener for "Add Item" button
    const addItemBtn = document.getElementById('add-item-btn');
    if (addItemBtn) {
        addItemBtn.addEventListener('click', addInvoiceItem);
    }
}

function createInitialRow() {
    const tbody = document.getElementById('invoice-items-tbody');
    if (tbody && tbody.children.length === 0) {
        console.log('Creating initial row with services:', availableServices.length);
        console.log('Available vendors when creating initial row:', availableVendors);
        addInvoiceItem();
    }
}

function addInvoiceItem() {
    const tbody = document.getElementById('invoice-items-tbody');
    if (!tbody) return;
    
    const rowCount = tbody.children.length;
    const newRow = document.createElement('tr');
    
    // Generate vendor options BEFORE creating the row
    const vendorOptions = generateVendorOptions();
    
    newRow.innerHTML = `
        <td>
            <span class="sr-no">${rowCount + 1}</span>
        </td>
        <td>
            <select class="form-select form-control-sm description-select">
                <option value="">Select service</option>
                ${generateServiceOptions()}
            </select>
        </td>
        <td>
            <input type="number" class="form-control form-control-sm cost-qty" min="0" step="0.01" placeholder="0.00">
        </td>
        <td>
            <input type="number" class="form-control form-control-sm cost-rate" min="0" step="0.01" placeholder="0.00">
        </td>
        <td>
            <input type="number" class="form-control form-control-sm cost-amount" min="0" step="0.01" placeholder="0.00" readonly>
        </td>
        <td>
            <input type="number" class="form-control form-control-sm cost-vat" min="0" step="0.01" placeholder="0.00">
        </td>
        <td>
            <input type="number" class="form-control form-control-sm cost-total" min="0" step="0.01" placeholder="0.00" readonly>
        </td>
        <td>
            <select class="form-select form-control-sm vendor-select">
                ${vendorOptions}
            </select>
        </td>
        <td>
            <input type="number" class="form-control form-control-sm sale-qty" min="0" step="0.01" placeholder="0.00">
        </td>
        <td>
            <input type="number" class="form-control form-control-sm sale-rate" min="0" step="0.01" placeholder="0.00">
        </td>
        <td>
            <input type="number" class="form-control form-control-sm sale-amount" min="0" step="0.01" placeholder="0.00" readonly>
        </td>
        <td>
            <input type="number" class="form-control form-control-sm sale-vat" min="0" step="0.01" placeholder="0.00">
        </td>
        <td>
            <input type="number" class="form-control form-control-sm sale-total" min="0" step="0.01" placeholder="0.00" readonly>
        </td>
        <td>
            <input type="text" class="form-control form-control-sm remark" placeholder="Remark">
        </td>
        <td>
            <button type="button" class="btn btn-danger btn-sm remove-item-btn">
                <i class="bi bi-trash"></i>
            </button>
        </td>
    `;
    
    tbody.appendChild(newRow);
    
    // Add event listeners to the new row
    addRowEventListeners(newRow);
    
    // Update serial numbers
    updateSerialNumbers();
    
    // Calculate totals
    calculateTotals();
}

function generateServiceOptions() {
    console.log('Generating service options. Available services:', availableServices);
    
    if (!availableServices || availableServices.length === 0) {
        console.log('No services available');
        return '<option value="">No services available</option>';
    }
    
    const options = availableServices.map(service => 
        `<option value="${service.id}">${service.service_code} - ${service.service_name}</option>`
    ).join('');
    
    console.log('Generated options:', options);
    return options;
}

function generateVendorOptions() {
    // Always start with a default option
    let options = '<option value="">Select account</option>';
    
    if (!availableVendors && !availablePaymentSources) {
        options += '<option value="" disabled>Loading data...</option>';
        return options;
    }
    
    // Add vendors (show only account names)
    if (availableVendors && availableVendors.length > 0) {
        availableVendors.forEach((vendor, index) => {
            if (vendor && vendor.id && vendor.display_name) {
                options += `<option value="${vendor.id}" data-type="vendor">${vendor.display_name}</option>`;
            }
        });
    }
    
    // Add payment sources (show only account names)
    if (availablePaymentSources && availablePaymentSources.length > 0) {
        availablePaymentSources.forEach((source, index) => {
            if (source && source.id && source.name) {
                options += `<option value="payment_source_${source.id}" data-type="payment_source">${source.name}</option>`;
            }
        });
    }
    
    // If no options were added (only default option), add a message
    if (options === '<option value="">Select account</option>') {
        options += '<option value="" disabled>No options available</option>';
    }
    
    return options;
}

function removeInvoiceItem(button) {
    const row = button.closest('tr');
    const tbody = document.getElementById('invoice-items-tbody');
    
    if (tbody.children.length > 1) {
        row.remove();
        updateSerialNumbers();
        calculateTotals();
    } else {
        alert('At least one item is required.');
    }
}

function addRowEventListeners(row) {
    // Cost calculations
    const costQty = row.querySelector('.cost-qty');
    const costRate = row.querySelector('.cost-rate');
    const costAmount = row.querySelector('.cost-amount');
    const costVat = row.querySelector('.cost-vat');
    const costTotal = row.querySelector('.cost-total');
    
    // Sale calculations
    const saleQty = row.querySelector('.sale-qty');
    const saleRate = row.querySelector('.sale-rate');
    const saleAmount = row.querySelector('.sale-amount');
    const saleVat = row.querySelector('.sale-vat');
    const saleTotal = row.querySelector('.sale-total');
    
    // Service select dropdown
    const serviceSelect = row.querySelector('.description-select');
    
    // Vendor select dropdown
    const vendorSelect = row.querySelector('.vendor-select');

    // Remark field for Tab functionality
    const remarkField = row.querySelector('.remark');
    
    // Cost calculation listeners
    [costQty, costRate].forEach(field => {
        if (field) {
            field.addEventListener('input', () => calculateRowCosts(row));
        }
    });
    
    // Sale calculation listeners
    [saleQty, saleRate].forEach(field => {
        if (field) {
            field.addEventListener('input', () => calculateRowSales(row));
        }
    });
    
    // Service select listener
    if (serviceSelect) {
        serviceSelect.addEventListener('change', function() {
            const selectedServiceId = this.value;
            if (selectedServiceId) {
                // Find the selected service data
                const selectedService = availableServices.find(service => service.id == selectedServiceId);
                if (selectedService) {
                    // Store the selected service data in the row for VAT calculations
                    row.dataset.selectedService = JSON.stringify(selectedService);
                    
                    // Add visual indicator for VAT status
                    if (!selectedService.has_vat) {
                        row.classList.add('vat-free');
                        row.title = 'VAT Free Service';
                    } else {
                        row.classList.remove('vat-free');
                        row.title = 'Subject to 5% VAT';
                    }
                    
                    // Auto-populate cost rate
                    const costRateField = row.querySelector('.cost-rate');
                    if (costRateField) {
                        costRateField.value = selectedService.cost_price.toFixed(2);
                    }
                    
                    // Auto-populate sale rate
                    const saleRateField = row.querySelector('.sale-rate');
                    if (saleRateField) {
                        saleRateField.value = selectedService.sale_price.toFixed(2);
                    }
                    
                    // Trigger calculations
                    calculateRowCosts(row);
                    calculateRowSales(row);
                }
            } else {
                // Clear the selected service data
                delete row.dataset.selectedService;
                row.classList.remove('vat-free');
                row.title = '';
            }
        });
    }
    
    // Add event listeners to the new row
    if (vendorSelect) {
        vendorSelect.addEventListener('change', function() {
            const selectedValue = this.value;
            const selectedOption = this.options[this.selectedIndex];
            
            if (selectedValue && selectedOption) {
                const dataType = selectedOption.getAttribute('data-type');
                const displayText = selectedOption.text;
                
                console.log(`Selected ${dataType}: ${displayText}`);
                
                // You can add specific logic here based on the type
                if (dataType === 'payment_source') {
                    // Handle payment source selection
                    console.log('Payment source selected - this could trigger specific business logic');
                } else if (dataType === 'vendor') {
                    // Handle vendor selection
                    console.log('Vendor selected - this could trigger vendor-specific logic');
                }
            }
        });
    }
    
    // Tab functionality for remark field
    if (remarkField) {
        remarkField.addEventListener('keydown', function(e) {
            if (e.key === 'Tab' && !e.shiftKey) {
                e.preventDefault();
                
                // Always add a new row when Tab is pressed on remark field
                const newRow = addInvoiceItem();
                const firstInput = newRow.querySelector('input:not([readonly])');
                if (firstInput) {
                    firstInput.focus();
                }
            }
        });
    }
}

function calculateRowCosts(row) {
    const qty = parseFloat(row.querySelector('.cost-qty')?.value) || 0;
    const rate = parseFloat(row.querySelector('.cost-rate')?.value) || 0;
    
    // Get VAT rate from selected service, default to 5% if no service selected or has_vat is true
    let vatRate = 5; // Default 5% VAT
    if (row.dataset.selectedService) {
        try {
            const selectedService = JSON.parse(row.dataset.selectedService);
            vatRate = selectedService.has_vat ? 5 : 0; // 5% if has_vat is true, 0% if false
            console.log(`Cost calculation for ${selectedService.service_name}: VAT rate = ${vatRate}%`);
        } catch (e) {
            console.error('Error parsing selected service data:', e);
        }
    }
    
    const amount = qty * rate;
    const vat = amount * (vatRate / 100);
    const total = amount + vat;
    
    const amountField = row.querySelector('.cost-amount');
    const vatField = row.querySelector('.cost-vat');
    const totalField = row.querySelector('.cost-total');
    
    if (amountField) amountField.value = amount.toFixed(2);
    if (vatField) vatField.value = vat.toFixed(2);
    if (totalField) totalField.value = total.toFixed(2);
    
    calculateTotals();
}

function calculateRowSales(row) {
    const qty = parseFloat(row.querySelector('.sale-qty')?.value) || 0;
    const rate = parseFloat(row.querySelector('.sale-rate')?.value) || 0;
    
    // Get VAT rate from selected service, default to 5% if no service selected or has_vat is true
    let vatRate = 5; // Default 5% VAT
    if (row.dataset.selectedService) {
        try {
            const selectedService = JSON.parse(row.dataset.selectedService);
            vatRate = selectedService.has_vat ? 5 : 0; // 5% if has_vat is true, 0% if false
            console.log(`Sale calculation for ${selectedService.service_name}: VAT rate = ${vatRate}%`);
        } catch (e) {
            console.error('Error parsing selected service data:', e);
        }
    }
    
    const amount = qty * rate;
    const vat = amount * (vatRate / 100);
    const total = amount + vat;
    
    const amountField = row.querySelector('.sale-amount');
    const vatField = row.querySelector('.sale-vat');
    const totalField = row.querySelector('.sale-total');
    
    if (amountField) amountField.value = amount.toFixed(2);
    if (vatField) vatField.value = vat.toFixed(2);
    if (totalField) totalField.value = total.toFixed(2);
    
    calculateTotals();
}

function updateSerialNumbers() {
    const tbody = document.getElementById('invoice-items-tbody');
    if (!tbody) return;
    
    const rows = tbody.querySelectorAll('tr');
    rows.forEach((row, index) => {
        const srNoField = row.querySelector('input[readonly]');
        if (srNoField) {
            srNoField.value = index + 1;
        }
    });
}

function calculateTotals() {
    const tbody = document.getElementById('invoice-items-tbody');
    if (!tbody) return;
    
    let totalCost = 0;
    let totalSale = 0;
    
    const rows = tbody.querySelectorAll('tr');
    rows.forEach(row => {
        const costTotal = parseFloat(row.querySelector('.cost-total')?.value) || 0;
        const saleTotal = parseFloat(row.querySelector('.sale-total')?.value) || 0;
        
        totalCost += costTotal;
        totalSale += saleTotal;
    });
    
    const profit = totalSale - totalCost;
    
    // Update display
    const totalCostElement = document.getElementById('total-cost');
    const totalSaleElement = document.getElementById('total-sale');
    const totalProfitElement = document.getElementById('total-profit');
    
    if (totalCostElement) totalCostElement.textContent = `AED ${totalCost.toFixed(2)}`;
    if (totalSaleElement) totalSaleElement.textContent = `AED ${totalSale.toFixed(2)}`;
    if (totalProfitElement) totalProfitElement.textContent = `AED ${profit.toFixed(2)}`;
    
    // Update items count in the form
    const itemsCountField = document.getElementById('id_items_count');
    if (itemsCountField) {
        itemsCountField.value = rows.length;
    }
}

// Form Validation
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

// Print Functionality
function initializePrintFunctionality() {
    const printButtons = document.querySelectorAll('.btn-print');
    
    printButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const url = this.getAttribute('href');
            if (url) {
                window.open(url, '_blank', 'width=800,height=600');
            }
        });
    });
}

// Search and Filter Enhancement
function initializeSearchAndFilter() {
    const searchInput = document.querySelector('input[name="search"]');
    const statusFilter = document.querySelector('select[name="status"]');
    
    // Debounced search
    let searchTimeout;
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                this.form.submit();
            }, 500);
        });
    }
    
    // Auto-submit on filter change
    if (statusFilter) {
        statusFilter.addEventListener('change', function() {
            this.form.submit();
        });
    }
}

// Table Row Actions
function initializeTableActions() {
    const actionButtons = document.querySelectorAll('.btn-group .btn');
    
    actionButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (this.classList.contains('btn-outline-danger')) {
                if (!confirm('Are you sure you want to delete this item?')) {
                    e.preventDefault();
                }
            }
        });
    });
}

// Utility Functions
function formatCurrency(amount, currency = 'AED') {
    return `${currency} ${parseFloat(amount).toFixed(2)}`;
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

// Export functions
function exportToPDF() {
    // Implementation for PDF export
    console.log('Exporting to PDF...');
}

function exportToExcel() {
    // Implementation for Excel export
    console.log('Exporting to Excel...');
}

// Fetch services for description dropdown
function fetchServices() {
    return fetch('/invoicing/invoice/ajax/get-services/')
        .then(response => {
            console.log('Service fetch response status:', response.status);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Service fetch response data:', data);
            if (data.error) {
                console.error('Error:', data.error);
                // Fallback to hardcoded services for testing
                availableServices = [
                    {id: 1, service_code: 'CUS0001', service_name: 'Transit in Boe'},
                    {id: 2, service_code: 'WAR0001', service_name: 'Handling in'}
                ];
                console.log('Using fallback services:', availableServices);
                return;
            }
            availableServices = data.services;
            console.log('Services loaded:', availableServices.length);
            
            // Populate existing rows with services
            populateExistingRowsWithServices();
        })
        .catch(error => {
            console.error('Error fetching services:', error);
            // Fallback to hardcoded services for testing
            availableServices = [
                {id: 1, service_code: 'CUS0001', service_name: 'Transit in Boe'},
                {id: 2, service_code: 'WAR0001', service_name: 'Handling in'}
            ];
            console.log('Using fallback services due to error:', availableServices);
        });
}

function populateExistingRowsWithServices() {
    const tbody = document.getElementById('invoice-items-tbody');
    if (!tbody) return;
    
    const rows = tbody.querySelectorAll('tr');
    rows.forEach(row => {
        // Populate service dropdown
        const serviceSelect = row.querySelector('.description-select');
        if (serviceSelect) {
            serviceSelect.innerHTML = `
                <option value="">Select a service</option>
                ${generateServiceOptions()}
            `;
        }
        
        // Populate vendor dropdown
        const vendorSelect = row.querySelector('.vendor-select');
        if (vendorSelect) {
            vendorSelect.innerHTML = `
                <option value="">Select account</option>
                ${generateVendorOptions()}
            `;
        }
    });
}

// Fetch vendors for vendor dropdown
function fetchVendors() {
    console.log('🔄 Fetching vendors...');
    const url = '/invoicing/invoice/ajax/get-vendors/';
    
    return fetch(url)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                console.error('Error:', data.error);
                availableVendors = [];
                return;
            }
            
            // Check if data.vendors exists and is an array
            if (data.vendors && Array.isArray(data.vendors)) {
                // Filter out ledger accounts, keep only vendors
                availableVendors = data.vendors.filter(item => item && item.type === 'vendor');
                console.log(`✅ Loaded ${availableVendors.length} vendors`);
            } else {
                console.error('❌ data.vendors is not an array:', data.vendors);
                availableVendors = [];
            }
            
            // Return the data to ensure Promise chain works
            return data;
        })
        .catch(error => {
            console.error('Error fetching vendors:', error);
            availableVendors = [];
            // Re-throw the error to maintain Promise chain
            throw error;
        });
}

// Fetch payment sources for payment source dropdown
function fetchPaymentSources() {
    console.log('🔄 Fetching payment sources...');
    const url = '/payment-source/api/payment-sources/';
    
    return fetch(url)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                console.error('Error:', data.error);
                availablePaymentSources = [];
                return;
            }
            
            availablePaymentSources = data.results || data || [];
            console.log(`✅ Loaded ${availablePaymentSources.length} payment sources`);
            
            return data;
        })
        .catch(error => {
            console.error('❌ Error fetching payment sources:', error);
            availablePaymentSources = [];
            throw error;
        });
}

// Note: DOMContentLoaded event listener is already defined at the top of the file
// This duplicate has been removed to prevent conflicts

// Initialize vendor selection handling
function initializeVendorHandling() {
    // Add event listeners to vendor selects for type-specific handling
    document.addEventListener('change', function(e) {
        if (e.target.classList.contains('vendor-select')) {
            handleVendorSelection(e.target);
        }
    });
}

// Refresh vendor dropdowns in existing rows
function refreshVendorDropdowns() {
    const tbody = document.getElementById('invoice-items-tbody');
    if (!tbody) return;
    
    const rows = tbody.querySelectorAll('tr');
    rows.forEach(row => {
        const vendorSelect = row.querySelector('.vendor-select');
        if (vendorSelect) {
            vendorSelect.innerHTML = `
                <option value="">Select account</option>
            ${generateVendorOptions()}
            `;
        }
    });
}

// Handle vendor selection
function handleVendorSelection(selectElement) {
    const selectedValue = selectElement.value;
    const selectedOption = selectElement.options[selectElement.selectedIndex];
    
    if (selectedValue && selectedOption) {
        const dataType = selectedOption.getAttribute('data-type');
        const displayText = selectedOption.text;
        
        console.log(`Selected ${dataType}: ${displayText}`);
        
        // You can add specific logic here based on the type
        if (dataType === 'payment_source') {
            // Handle payment source selection
            console.log('Payment source selected - this could trigger specific business logic');
        } else if (dataType === 'vendor') {
            // Handle vendor selection
            console.log('Vendor selected - this could trigger vendor-specific logic');
        }
    }
}

// Initialize form submission handling
function initializeFormSubmission() {
    console.log('Initializing form submission...');
    console.log('All forms on page:', document.querySelectorAll('form'));
    console.log('Forms with needs-validation class:', document.querySelectorAll('form.needs-validation'));
    
    const form = document.querySelector('form.needs-validation');
    if (form) {
        console.log('Found form:', form);
        console.log('Form action:', form.action);
        console.log('Form method:', form.method);
        
        form.addEventListener('submit', function(e) {
            console.log('Form submission started');
            
            // Check items_count field before submission
            const itemsCountField = document.getElementById('id_items_count');
            console.log('Items count field before submission:', itemsCountField?.value);
            
            // Collect invoice items data before submission
            collectInvoiceItemsData();
            
            // Add a small delay to ensure data is collected
            setTimeout(() => {
                console.log('Form submitting with data:', {
                    invoice_items: document.getElementById('id_invoice_items')?.value,
                    customer: document.getElementById('id_customer')?.value,
                    invoice_date: document.getElementById('id_invoice_date')?.value,
                    items_count: document.getElementById('id_items_count')?.value
                });
            }, 100);
        });
    } else {
        console.error('Form not found for submission handling');
        console.log('Available forms:', document.querySelectorAll('form'));
    }
}

// Collect invoice items data and populate hidden field
function collectInvoiceItemsData() {
    const tbody = document.getElementById('invoice-items-tbody');
    const hiddenField = document.getElementById('id_invoice_items');
    
    if (!tbody || !hiddenField) {
        console.error('Invoice items table or hidden field not found');
        return;
    }
    
    const rows = tbody.querySelectorAll('tr');
    const invoiceItems = [];
    
    console.log('Collecting data from', rows.length, 'rows');
    
    rows.forEach((row, index) => {
        const serviceSelect = row.querySelector('.description-select');
        const vendorSelect = row.querySelector('.vendor-select');
        
        // Get service name instead of ID
        let serviceName = '';
        if (serviceSelect && serviceSelect.value) {
            const selectedOption = serviceSelect.options[serviceSelect.selectedIndex];
            serviceName = selectedOption ? selectedOption.text : '';
            console.log('Service select value:', serviceSelect.value);
            console.log('Service select text:', selectedOption ? selectedOption.text : 'No option');
            console.log('Service name extracted:', serviceName);
        }
        
        // Get vendor name and payment source ID
        let vendorName = '';
        let paymentSourceId = null;
        if (vendorSelect && vendorSelect.value) {
            const selectedVendorOption = vendorSelect.options[vendorSelect.selectedIndex];
            const dataType = selectedVendorOption ? selectedVendorOption.getAttribute('data-type') : null;
            
            if (dataType === 'payment_source' && vendorSelect.value.startsWith('payment_source_')) {
                // Extract payment source ID from value like 'payment_source_123'
                paymentSourceId = vendorSelect.value.replace('payment_source_', '');
                vendorName = selectedVendorOption ? selectedVendorOption.text : '';
                console.log('Payment source selected - ID:', paymentSourceId, 'Name:', vendorName);
            } else {
                // Regular vendor
                vendorName = selectedVendorOption ? selectedVendorOption.text : '';
                console.log('Vendor selected - Name:', vendorName);
            }
        }
        
        const item = {
            sr_no: index + 1,
            description: serviceName,
            cost_qty: parseFloat(row.querySelector('.cost-qty')?.value || 0),
            cost_rate: parseFloat(row.querySelector('.cost-rate')?.value || 0),
            cost_amount: parseFloat(row.querySelector('.cost-amount')?.value || 0),
            cost_vat: parseFloat(row.querySelector('.cost-vat')?.value || 0),
            cost_total: parseFloat(row.querySelector('.cost-total')?.value || 0),
            vendor: vendorName,
            payment_source_id: paymentSourceId,
            sale_qty: parseFloat(row.querySelector('.sale-qty')?.value || 0),
            sale_rate: parseFloat(row.querySelector('.sale-rate')?.value || 0),
            sale_amount: parseFloat(row.querySelector('.sale-amount')?.value || 0),
            sale_vat: parseFloat(row.querySelector('.sale-vat')?.value || 0),
            sale_total: parseFloat(row.querySelector('.sale-total')?.value || 0),
            remark: row.querySelector('.remark')?.value || ''
        };
        
        // Only add items that have at least some data
        if (item.description || item.cost_qty > 0 || item.sale_qty > 0 || item.remark) {
            invoiceItems.push(item);
            console.log('Added item:', item);
            console.log('Item description type:', typeof item.description);
            console.log('Item description value:', item.description);
        }
    });
    
    // Update the hidden field with JSON data
    const jsonData = JSON.stringify(invoiceItems);
    hiddenField.value = jsonData;
    console.log('Invoice items data collected:', invoiceItems);
    console.log('JSON data length:', jsonData.length);
}

// Populate invoice items table with existing data (for editing)
function populateInvoiceItemsTable(existingItems) {
    if (!existingItems || !Array.isArray(existingItems) || existingItems.length === 0) {
        console.log('No existing invoice items to populate');
        return;
    }
    
    console.log('Populating invoice items table with:', existingItems);
    
    const tbody = document.getElementById('invoice-items-tbody');
    if (!tbody) {
        console.error('Invoice items table body not found');
        return;
    }
    
    // Clear existing rows
    tbody.innerHTML = '';
    
    // Add rows for each existing item
    existingItems.forEach((item, index) => {
        const newRow = addInvoiceItem();
        if (newRow) {
            // Populate the row with existing data
            populateInvoiceItemRow(newRow, item);
        }
    });
    
    // Update totals
    calculateTotals();
}

// Populate a single invoice item row with data
function populateInvoiceItemRow(row, item) {
    // Set service - find by name since we store the name, not ID
    const serviceSelect = row.querySelector('.description-select');
    if (serviceSelect && item.description) {
        // Find the option that matches the description (service name)
        for (let i = 0; i < serviceSelect.options.length; i++) {
            if (serviceSelect.options[i].text === item.description) {
                serviceSelect.selectedIndex = i;
        // Trigger change event to populate rates
        serviceSelect.dispatchEvent(new Event('change'));
                break;
            }
        }
    }
    
    // Set vendor - find by name since we store the name, not ID
    const vendorSelect = row.querySelector('.vendor-select');
    if (vendorSelect && item.vendor) {
        for (let i = 0; i < vendorSelect.options.length; i++) {
            if (vendorSelect.options[i].text === item.vendor) {
                vendorSelect.selectedIndex = i;
                break;
            }
        }
    }
    
    // Set cost fields
    if (item.cost_qty) row.querySelector('.cost-qty').value = item.cost_qty;
    if (item.cost_rate) row.querySelector('.cost-rate').value = item.cost_rate;
    if (item.cost_amount) row.querySelector('.cost-amount').value = item.cost_amount;
    if (item.cost_vat) row.querySelector('.cost-vat').value = item.cost_vat;
    if (item.cost_total) row.querySelector('.cost-total').value = item.cost_total;
    
    // Set sale fields
    if (item.sale_qty) row.querySelector('.sale-qty').value = item.sale_qty;
    if (item.sale_rate) row.querySelector('.sale-rate').value = item.sale_rate;
    if (item.sale_amount) row.querySelector('.sale-amount').value = item.sale_amount;
    if (item.sale_vat) row.querySelector('.sale-vat').value = item.sale_vat;
    if (item.sale_total) row.querySelector('.sale-total').value = item.sale_total;
    
    // Set remark
    if (item.remark) row.querySelector('.remark').value = item.remark;
}