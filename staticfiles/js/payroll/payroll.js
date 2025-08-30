// Payroll Management System JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all components
    initializePayrollForms();
    initializeCalculations();
    initializeDataTables();
    initializeModals();
    initializeCharts();
    initializeFilters();
    initializePrint();
});

// Form Initialization
function initializePayrollForms() {
    // Salary structure form
    const salaryForm = document.getElementById('salary-structure-form');
    if (salaryForm) {
        setupSalaryFormValidation(salaryForm);
        setupSalaryCalculations(salaryForm);
    }

    // Employee salary form
    const employeeSalaryForm = document.getElementById('employee-salary-form');
    if (employeeSalaryForm) {
        setupEmployeeSalaryValidation(employeeSalaryForm);
        setupSalaryStructureChange(employeeSalaryForm);
    }

    // Payroll period form
    const periodForm = document.getElementById('payroll-period-form');
    if (periodForm) {
        setupPeriodFormValidation(periodForm);
        setupDateCalculations(periodForm);
    }

    // Bank account form
    const bankForm = document.getElementById('bank-account-form');
    if (bankForm) {
        setupBankFormValidation(bankForm);
        setupIBANValidation(bankForm);
    }

    // Loan form
    const loanForm = document.getElementById('loan-form');
    if (loanForm) {
        setupLoanFormValidation(loanForm);
        setupLoanCalculations(loanForm);
    }

    // Advance form
    const advanceForm = document.getElementById('advance-form');
    if (advanceForm) {
        setupAdvanceFormValidation(advanceForm);
    }

    // EOSB form
    const eosbForm = document.getElementById('eosb-form');
    if (eosbForm) {
        setupEOSBFormValidation(eosbForm);
        setupEOSBCalculations(eosbForm);
    }
}

// Salary Structure Form
function setupSalaryFormValidation(form) {
    form.addEventListener('submit', function(e) {
        if (!validateSalaryForm()) {
            e.preventDefault();
            return false;
        }
        
        showLoadingState(form);
    });
}

function validateSalaryForm() {
    let isValid = true;
    const errors = [];
    
    // Validate basic salary
    const basicSalary = document.getElementById('id_basic_salary');
    if (basicSalary && (!basicSalary.value || parseFloat(basicSalary.value) <= 0)) {
        basicSalary.classList.add('is-invalid');
        errors.push('Basic salary must be greater than zero');
        isValid = false;
    } else if (basicSalary) {
        basicSalary.classList.remove('is-invalid');
    }
    
    // Validate allowances (must be non-negative)
    const allowances = ['housing_allowance', 'transport_allowance', 'other_allowances'];
    allowances.forEach(fieldName => {
        const field = document.getElementById(`id_${fieldName}`);
        if (field && parseFloat(field.value) < 0) {
            field.classList.add('is-invalid');
            errors.push(`${fieldName.replace('_', ' ')} cannot be negative`);
            isValid = false;
        } else if (field) {
            field.classList.remove('is-invalid');
        }
    });
    
    if (!isValid) {
        showFormErrors(errors);
    }
    
    return isValid;
}

function setupSalaryCalculations(form) {
    const basicSalary = document.getElementById('id_basic_salary');
    const housingAllowance = document.getElementById('id_housing_allowance');
    const transportAllowance = document.getElementById('id_transport_allowance');
    const otherAllowances = document.getElementById('id_other_allowances');
    const totalCTC = document.getElementById('total-ctc');
    
    const fields = [basicSalary, housingAllowance, transportAllowance, otherAllowances];
    
    fields.forEach(field => {
        if (field) {
            field.addEventListener('input', calculateTotalCTC);
        }
    });
    
    function calculateTotalCTC() {
        const basic = parseFloat(basicSalary.value) || 0;
        const housing = parseFloat(housingAllowance.value) || 0;
        const transport = parseFloat(transportAllowance.value) || 0;
        const other = parseFloat(otherAllowances.value) || 0;
        
        const total = basic + housing + transport + other;
        
        if (totalCTC) {
            totalCTC.textContent = total.toFixed(2);
        }
    }
}

// Employee Salary Form
function setupEmployeeSalaryValidation(form) {
    form.addEventListener('submit', function(e) {
        if (!validateEmployeeSalaryForm()) {
            e.preventDefault();
            return false;
        }
        
        showLoadingState(form);
    });
}

function validateEmployeeSalaryForm() {
    let isValid = true;
    const errors = [];
    
    // Validate basic salary
    const basicSalary = document.getElementById('id_basic_salary');
    if (basicSalary && (!basicSalary.value || parseFloat(basicSalary.value) <= 0)) {
        basicSalary.classList.add('is-invalid');
        errors.push('Basic salary must be greater than zero');
        isValid = false;
    } else if (basicSalary) {
        basicSalary.classList.remove('is-invalid');
    }
    
    // Validate effective date
    const effectiveDate = document.getElementById('id_effective_date');
    if (effectiveDate && effectiveDate.value) {
        const selectedDate = new Date(effectiveDate.value);
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        
        if (selectedDate > today) {
            effectiveDate.classList.add('is-invalid');
            errors.push('Effective date cannot be in the future');
            isValid = false;
        } else {
            effectiveDate.classList.remove('is-invalid');
        }
    }
    
    if (!isValid) {
        showFormErrors(errors);
    }
    
    return isValid;
}

function setupSalaryStructureChange(form) {
    const structureSelect = document.getElementById('id_salary_structure');
    if (structureSelect) {
        structureSelect.addEventListener('change', function() {
            const structureId = this.value;
            if (structureId) {
                loadSalaryStructure(structureId);
            }
        });
    }
}

function loadSalaryStructure(structureId) {
    fetch(`/hr/payroll/salary-structure/${structureId}/data/`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                document.getElementById('id_basic_salary').value = data.structure.basic_salary;
                document.getElementById('id_housing_allowance').value = data.structure.housing_allowance;
                document.getElementById('id_transport_allowance').value = data.structure.transport_allowance;
                document.getElementById('id_other_allowances').value = data.structure.other_allowances;
                
                // Trigger calculation update
                const event = new Event('input');
                document.getElementById('id_basic_salary').dispatchEvent(event);
            }
        })
        .catch(error => console.error('Error loading salary structure:', error));
}

// Payroll Period Form
function setupPeriodFormValidation(form) {
    form.addEventListener('submit', function(e) {
        if (!validatePeriodForm()) {
            e.preventDefault();
            return false;
        }
        
        showLoadingState(form);
    });
}

function validatePeriodForm() {
    let isValid = true;
    const errors = [];
    
    // Validate dates
    const startDate = document.getElementById('id_start_date');
    const endDate = document.getElementById('id_end_date');
    
    if (startDate && endDate && startDate.value && endDate.value) {
        const start = new Date(startDate.value);
        const end = new Date(endDate.value);
        
        if (start >= end) {
            endDate.classList.add('is-invalid');
            errors.push('End date must be after start date');
            isValid = false;
        } else {
            endDate.classList.remove('is-invalid');
        }
    }
    
    // Validate year and month
    const year = document.getElementById('id_year');
    const month = document.getElementById('id_month');
    
    if (year && month && year.value && month.value) {
        const selectedYear = parseInt(year.value);
        const selectedMonth = parseInt(month.value);
        const currentYear = new Date().getFullYear();
        
        if (selectedYear < 2020 || selectedYear > currentYear + 1) {
            year.classList.add('is-invalid');
            errors.push('Year must be between 2020 and ' + (currentYear + 1));
            isValid = false;
        } else {
            year.classList.remove('is-invalid');
        }
        
        if (selectedMonth < 1 || selectedMonth > 12) {
            month.classList.add('is-invalid');
            errors.push('Month must be between 1 and 12');
            isValid = false;
        } else {
            month.classList.remove('is-invalid');
        }
    }
    
    if (!isValid) {
        showFormErrors(errors);
    }
    
    return isValid;
}

function setupDateCalculations(form) {
    const yearSelect = document.getElementById('id_year');
    const monthSelect = document.getElementById('id_month');
    const startDate = document.getElementById('id_start_date');
    const endDate = document.getElementById('id_end_date');
    
    if (yearSelect && monthSelect) {
        [yearSelect, monthSelect].forEach(select => {
            select.addEventListener('change', calculatePeriodDates);
        });
    }
    
    function calculatePeriodDates() {
        const year = yearSelect.value;
        const month = monthSelect.value;
        
        if (year && month) {
            const start = new Date(year, month - 1, 1);
            const end = new Date(year, month, 0);
            
            startDate.value = start.toISOString().split('T')[0];
            endDate.value = end.toISOString().split('T')[0];
        }
    }
}

// Bank Account Form
function setupBankFormValidation(form) {
    form.addEventListener('submit', function(e) {
        if (!validateBankForm()) {
            e.preventDefault();
            return false;
        }
        
        showLoadingState(form);
    });
}

function validateBankForm() {
    let isValid = true;
    const errors = [];
    
    // Validate IBAN
    const iban = document.getElementById('id_iban');
    if (iban && iban.value) {
        if (!iban.value.startsWith('AE')) {
            iban.classList.add('is-invalid');
            errors.push('IBAN must start with AE for UAE accounts');
            isValid = false;
        } else if (iban.value.length !== 23) {
            iban.classList.add('is-invalid');
            errors.push('UAE IBAN must be 23 characters long');
            isValid = false;
        } else {
            iban.classList.remove('is-invalid');
        }
    }
    
    if (!isValid) {
        showFormErrors(errors);
    }
    
    return isValid;
}

function setupIBANValidation(form) {
    const iban = document.getElementById('id_iban');
    if (iban) {
        iban.addEventListener('input', function() {
            this.value = this.value.toUpperCase();
            
            // Remove spaces and special characters
            this.value = this.value.replace(/[^A-Z0-9]/g, '');
            
            // Format IBAN with spaces every 4 characters
            if (this.value.length > 4) {
                this.value = this.value.replace(/(.{4})/g, '$1 ').trim();
            }
        });
    }
}

// Loan Form
function setupLoanFormValidation(form) {
    form.addEventListener('submit', function(e) {
        if (!validateLoanForm()) {
            e.preventDefault();
            return false;
        }
        
        showLoadingState(form);
    });
}

function validateLoanForm() {
    let isValid = true;
    const errors = [];
    
    // Validate loan amount
    const loanAmount = document.getElementById('id_loan_amount');
    if (loanAmount && (!loanAmount.value || parseFloat(loanAmount.value) <= 0)) {
        loanAmount.classList.add('is-invalid');
        errors.push('Loan amount must be greater than zero');
        isValid = false;
    } else if (loanAmount) {
        loanAmount.classList.remove('is-invalid');
    }
    
    // Validate monthly installment
    const monthlyInstallment = document.getElementById('id_monthly_installment');
    if (monthlyInstallment && (!monthlyInstallment.value || parseFloat(monthlyInstallment.value) <= 0)) {
        monthlyInstallment.classList.add('is-invalid');
        errors.push('Monthly installment must be greater than zero');
        isValid = false;
    } else if (monthlyInstallment) {
        monthlyInstallment.classList.remove('is-invalid');
    }
    
    // Validate total installments
    const totalInstallments = document.getElementById('id_total_installments');
    if (totalInstallments && (!totalInstallments.value || parseInt(totalInstallments.value) <= 0)) {
        totalInstallments.classList.add('is-invalid');
        errors.push('Total installments must be greater than zero');
        isValid = false;
    } else if (totalInstallments) {
        totalInstallments.classList.remove('is-invalid');
    }
    
    // Validate loan calculation
    if (loanAmount && monthlyInstallment && totalInstallments) {
        const amount = parseFloat(loanAmount.value) || 0;
        const installment = parseFloat(monthlyInstallment.value) || 0;
        const installments = parseInt(totalInstallments.value) || 0;
        
        const expectedTotal = installment * installments;
        if (Math.abs(expectedTotal - amount) > 1) {
            errors.push('Loan amount should equal monthly installment × total installments');
            isValid = false;
        }
    }
    
    if (!isValid) {
        showFormErrors(errors);
    }
    
    return isValid;
}

function setupLoanCalculations(form) {
    const loanAmount = document.getElementById('id_loan_amount');
    const monthlyInstallment = document.getElementById('id_monthly_installment');
    const totalInstallments = document.getElementById('id_total_installments');
    
    const fields = [loanAmount, monthlyInstallment, totalInstallments];
    
    fields.forEach(field => {
        if (field) {
            field.addEventListener('input', calculateLoanDetails);
        }
    });
    
    function calculateLoanDetails() {
        const amount = parseFloat(loanAmount.value) || 0;
        const installment = parseFloat(monthlyInstallment.value) || 0;
        const installments = parseInt(totalInstallments.value) || 0;
        
        // Calculate remaining amount
        const remainingAmount = amount - (installment * installments);
        
        // Update display
        const remainingDisplay = document.getElementById('remaining-amount');
        if (remainingDisplay) {
            remainingDisplay.textContent = remainingAmount.toFixed(2);
        }
    }
}

// Advance Form
function setupAdvanceFormValidation(form) {
    form.addEventListener('submit', function(e) {
        if (!validateAdvanceForm()) {
            e.preventDefault();
            return false;
        }
        
        showLoadingState(form);
    });
}

function validateAdvanceForm() {
    let isValid = true;
    const errors = [];
    
    // Validate amount
    const amount = document.getElementById('id_amount');
    if (amount && (!amount.value || parseFloat(amount.value) <= 0)) {
        amount.classList.add('is-invalid');
        errors.push('Advance amount must be greater than zero');
        isValid = false;
    } else if (amount) {
        amount.classList.remove('is-invalid');
    }
    
    // Validate reason
    const reason = document.getElementById('id_reason');
    if (reason && !reason.value.trim()) {
        reason.classList.add('is-invalid');
        errors.push('Reason is required');
        isValid = false;
    } else if (reason) {
        reason.classList.remove('is-invalid');
    }
    
    if (!isValid) {
        showFormErrors(errors);
    }
    
    return isValid;
}

// EOSB Form
function setupEOSBFormValidation(form) {
    form.addEventListener('submit', function(e) {
        if (!validateEOSBForm()) {
            e.preventDefault();
            return false;
        }
        
        showLoadingState(form);
    });
}

function validateEOSBForm() {
    let isValid = true;
    const errors = [];
    
    // Validate dates
    const joiningDate = document.getElementById('id_joining_date');
    const terminationDate = document.getElementById('id_termination_date');
    
    if (joiningDate && terminationDate && joiningDate.value && terminationDate.value) {
        const joining = new Date(joiningDate.value);
        const termination = new Date(terminationDate.value);
        
        if (joining >= termination) {
            terminationDate.classList.add('is-invalid');
            errors.push('Termination date must be after joining date');
            isValid = false;
        } else {
            terminationDate.classList.remove('is-invalid');
        }
    }
    
    // Validate basic salary for gratuity
    const basicSalary = document.getElementById('id_basic_salary_for_gratuity');
    if (basicSalary && (!basicSalary.value || parseFloat(basicSalary.value) <= 0)) {
        basicSalary.classList.add('is-invalid');
        errors.push('Basic salary for gratuity must be greater than zero');
        isValid = false;
    } else if (basicSalary) {
        basicSalary.classList.remove('is-invalid');
    }
    
    if (!isValid) {
        showFormErrors(errors);
    }
    
    return isValid;
}

function setupEOSBCalculations(form) {
    const joiningDate = document.getElementById('id_joining_date');
    const terminationDate = document.getElementById('id_termination_date');
    const basicSalary = document.getElementById('id_basic_salary_for_gratuity');
    
    const fields = [joiningDate, terminationDate, basicSalary];
    
    fields.forEach(field => {
        if (field) {
            field.addEventListener('change', calculateEOSB);
        }
    });
    
    function calculateEOSB() {
        const joining = new Date(joiningDate.value);
        const termination = new Date(terminationDate.value);
        const salary = parseFloat(basicSalary.value) || 0;
        
        if (joining && termination && salary > 0) {
            const yearsOfService = (termination - joining) / (1000 * 60 * 60 * 24 * 365.25);
            
            let gratuityDaysPerYear;
            if (yearsOfService <= 5) {
                gratuityDaysPerYear = 21;
            } else {
                gratuityDaysPerYear = 30;
            }
            
            const totalGratuityDays = yearsOfService * gratuityDaysPerYear;
            const gratuityAmount = (salary / 30) * totalGratuityDays;
            
            // Update display
            const yearsDisplay = document.getElementById('years-of-service');
            const gratuityDisplay = document.getElementById('gratuity-amount');
            
            if (yearsDisplay) {
                yearsDisplay.textContent = yearsOfService.toFixed(2);
            }
            if (gratuityDisplay) {
                gratuityDisplay.textContent = gratuityAmount.toFixed(2);
            }
        }
    }
}

// Calculations
function initializeCalculations() {
    // Payroll calculations
    setupPayrollCalculations();
    
    // WPS calculations
    setupWPSCalculations();
    
    // GPSSA calculations
    setupGPSSACalculations();
}

function setupPayrollCalculations() {
    const payrollForm = document.getElementById('payroll-record-form');
    if (payrollForm) {
        const fields = [
            'basic_salary', 'housing_allowance', 'transport_allowance', 'other_allowances',
            'overtime_pay', 'bonus', 'commission', 'other_earnings',
            'loan_deduction', 'advance_deduction', 'absence_deduction', 'other_deductions'
        ];
        
        fields.forEach(fieldName => {
            const field = document.getElementById(`id_${fieldName}`);
            if (field) {
                field.addEventListener('input', calculatePayrollTotals);
            }
        });
    }
}

function calculatePayrollTotals() {
    // Calculate gross salary
    const earnings = [
        'basic_salary', 'housing_allowance', 'transport_allowance', 'other_allowances',
        'overtime_pay', 'bonus', 'commission', 'other_earnings'
    ];
    
    let grossSalary = 0;
    earnings.forEach(fieldName => {
        const field = document.getElementById(`id_${fieldName}`);
        if (field) {
            grossSalary += parseFloat(field.value) || 0;
        }
    });
    
    // Calculate total deductions
    const deductions = [
        'loan_deduction', 'advance_deduction', 'absence_deduction', 'other_deductions'
    ];
    
    let totalDeductions = 0;
    deductions.forEach(fieldName => {
        const field = document.getElementById(`id_${fieldName}`);
        if (field) {
            totalDeductions += parseFloat(field.value) || 0;
        }
    });
    
    // Calculate net salary
    const netSalary = grossSalary - totalDeductions;
    
    // Update display
    const grossDisplay = document.getElementById('gross-salary');
    const deductionsDisplay = document.getElementById('total-deductions');
    const netDisplay = document.getElementById('net-salary');
    
    if (grossDisplay) grossDisplay.textContent = grossSalary.toFixed(2);
    if (deductionsDisplay) deductionsDisplay.textContent = totalDeductions.toFixed(2);
    if (netDisplay) netDisplay.textContent = netSalary.toFixed(2);
}

function setupWPSCalculations() {
    // WPS specific calculations
    const wpsForm = document.getElementById('wps-form');
    if (wpsForm) {
        const salaryField = document.getElementById('id_salary_amount');
        if (salaryField) {
            salaryField.addEventListener('input', function() {
                const amount = parseFloat(this.value) || 0;
                // Format for WPS display
                const formattedAmount = amount.toFixed(2);
                const displayField = document.getElementById('wps-amount-display');
                if (displayField) {
                    displayField.textContent = formattedAmount;
                }
            });
        }
    }
}

function setupGPSSACalculations() {
    // GPSSA calculations for UAE nationals
    const gpssaForm = document.getElementById('gpssa-form');
    if (gpssaForm) {
        const employeeContribution = document.getElementById('id_employee_contribution');
        const employerContribution = document.getElementById('id_employer_contribution');
        
        [employeeContribution, employerContribution].forEach(field => {
            if (field) {
                field.addEventListener('input', calculateTotalContribution);
            }
        });
        
        function calculateTotalContribution() {
            const employee = parseFloat(employeeContribution.value) || 0;
            const employer = parseFloat(employerContribution.value) || 0;
            const total = employee + employer;
            
            const totalDisplay = document.getElementById('total-contribution');
            if (totalDisplay) {
                totalDisplay.textContent = total.toFixed(2);
            }
        }
    }
}

// Data Tables
function initializeDataTables() {
    // Initialize DataTables if available
    if (typeof $.fn.DataTable !== 'undefined') {
        $('.payroll-table').DataTable({
            responsive: true,
            pageLength: 25,
            order: [[0, 'desc']],
            language: {
                search: "Search:",
                lengthMenu: "Show _MENU_ entries per page",
                info: "Showing _START_ to _END_ of _TOTAL_ entries",
                paginate: {
                    first: "First",
                    last: "Last",
                    next: "Next",
                    previous: "Previous"
                }
            }
        });
    }
}

// Modals
function initializeModals() {
    // Initialize Bootstrap modals
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        const modalInstance = new bootstrap.Modal(modal);
        
        // Handle modal events
        modal.addEventListener('show.bs.modal', function() {
            // Initialize form validation when modal opens
            const form = this.querySelector('form');
            if (form) {
                setupFormValidation(form);
            }
        });
    });
}

// Charts
function initializeCharts() {
    // Initialize charts if Chart.js is available
    if (typeof Chart !== 'undefined') {
        // Payroll summary chart
        const payrollChart = document.getElementById('payroll-chart');
        if (payrollChart) {
            new Chart(payrollChart, {
                type: 'bar',
                data: {
                    labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                    datasets: [{
                        label: 'Total Payroll',
                        data: [12000, 19000, 3000, 5000, 2000, 3000],
                        backgroundColor: 'rgba(0, 123, 255, 0.8)'
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
        
        // Employee distribution chart
        const employeeChart = document.getElementById('employee-chart');
        if (employeeChart) {
            new Chart(employeeChart, {
                type: 'doughnut',
                data: {
                    labels: ['With Salary', 'With Bank', 'Active Loans', 'Pending Advances'],
                    datasets: [{
                        data: [85, 78, 12, 5],
                        backgroundColor: [
                            '#28a745',
                            '#17a2b8',
                            '#ffc107',
                            '#dc3545'
                        ]
                    }]
                },
                options: {
                    responsive: true
                }
            });
        }
    }
}

// Filters
function initializeFilters() {
    // Search and filter functionality
    const searchForm = document.getElementById('search-form');
    if (searchForm) {
        setupFilterAutoSubmit(searchForm);
        setupFilterReset(searchForm);
    }
}

function setupFilterAutoSubmit(form) {
    const filterInputs = form.querySelectorAll('select, input[type="date"]');
    filterInputs.forEach(input => {
        input.addEventListener('change', function() {
            form.submit();
        });
    });
}

function setupFilterReset(form) {
    const resetBtn = form.querySelector('#reset-filters');
    if (resetBtn) {
        resetBtn.addEventListener('click', function(e) {
            e.preventDefault();
            form.reset();
            form.submit();
        });
    }
}

// Print functionality
function initializePrint() {
    const printBtns = document.querySelectorAll('.print-btn');
    printBtns.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            window.print();
        });
    });
}

// Utility Functions
function showFormErrors(errors) {
    // Remove existing error alerts
    const existingAlerts = document.querySelectorAll('.alert-danger');
    existingAlerts.forEach(alert => alert.remove());
    
    // Create error alert
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-danger alert-dismissible fade show';
    alertDiv.innerHTML = `
        <strong>Please correct the following errors:</strong>
        <ul class="mb-0 mt-2">
            ${errors.map(error => `<li>${error}</li>`).join('')}
        </ul>
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    const form = document.querySelector('form');
    if (form) {
        form.insertBefore(alertDiv, form.firstChild);
    }
}

function showLoadingState(form) {
    const submitBtn = form.querySelector('button[type="submit"]');
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Processing...';
    }
}

function showSuccessMessage(message) {
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-success alert-dismissible fade show';
    alertDiv.innerHTML = `
        <i class="fas fa-check-circle me-2"></i>${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    const container = document.querySelector('.container-fluid') || document.body;
    container.insertBefore(alertDiv, container.firstChild);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}

function showErrorMessage(message) {
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-danger alert-dismissible fade show';
    alertDiv.innerHTML = `
        <i class="fas fa-exclamation-triangle me-2"></i>${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    const container = document.querySelector('.container-fluid') || document.body;
    container.insertBefore(alertDiv, container.firstChild);
}

function formatCurrency(amount) {
    return new Intl.NumberFormat('en-AE', {
        style: 'currency',
        currency: 'AED'
    }).format(amount);
}

function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString('en-AE');
}

// AJAX Functions
function loadEmployeeData(employeeId) {
    return fetch(`/hr/payroll/employee/${employeeId}/data/`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                return data.employee;
            } else {
                throw new Error(data.error);
            }
        });
}

function savePayrollRecord(formData) {
    return fetch('/hr/payroll/record/save/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify(formData)
    })
    .then(response => response.json());
}

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

// Export functions for use in other scripts
window.PayrollSystem = {
    showSuccessMessage,
    showErrorMessage,
    formatCurrency,
    formatDate,
    loadEmployeeData,
    savePayrollRecord,
    calculatePayrollTotals
}; 