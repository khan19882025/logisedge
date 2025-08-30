// Payment Scheduling App JavaScript

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

    // Payment Schedule Status Change
    function initializeStatusChange() {
        const statusSelects = document.querySelectorAll('.status-change-select');
        statusSelects.forEach(function(select) {
            select.addEventListener('change', function() {
                const scheduleId = this.dataset.scheduleId;
                const newStatus = this.value;
                
                // Show loading spinner
                const originalText = this.innerHTML;
                this.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span> Loading...';
                this.disabled = true;
                
                // Send AJAX request
                fetch(`/accounting/payment-scheduling/schedules/${scheduleId}/status-change/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                        'X-CSRFToken': getCookie('csrftoken')
                    },
                    body: `status=${newStatus}`
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Show success message
                        showAlert('success', data.message);
                        
                        // Update the status badge
                        const statusBadge = document.querySelector(`[data-schedule-id="${scheduleId}"] .status-badge`);
                        if (statusBadge) {
                            statusBadge.className = `badge bg-${getBadgeClass(newStatus)}`;
                            statusBadge.textContent = getStatusDisplay(newStatus);
                        }
                    } else {
                        showAlert('danger', data.message);
                        // Revert the select
                        this.value = this.dataset.originalStatus;
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    showAlert('danger', 'An error occurred while updating the status.');
                    this.value = this.dataset.originalStatus;
                })
                .finally(() => {
                    // Restore original text
                    this.innerHTML = originalText;
                    this.disabled = false;
                });
            });
        });
    }

    // Get CSRF token from cookies
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

    // Show alert message
    function showAlert(type, message) {
        const alertContainer = document.createElement('div');
        alertContainer.className = `alert alert-${type} alert-dismissible fade show`;
        alertContainer.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        
        const container = document.querySelector('.container-fluid');
        if (container) {
            container.insertBefore(alertContainer, container.firstChild);
            
            // Auto-dismiss after 5 seconds
            setTimeout(() => {
                if (alertContainer.parentNode) {
                    alertContainer.remove();
                }
            }, 5000);
        }
    }

    // Get badge class based on status
    function getBadgeClass(status) {
        const statusClasses = {
            'paid': 'success',
            'overdue': 'danger',
            'partially_paid': 'warning',
            'pending': 'secondary',
            'draft': 'info'
        };
        return statusClasses[status] || 'secondary';
    }

    // Get status display text
    function getStatusDisplay(status) {
        const statusDisplay = {
            'paid': 'Paid',
            'overdue': 'Overdue',
            'partially_paid': 'Partially Paid',
            'pending': 'Pending',
            'draft': 'Draft',
            'cancelled': 'Cancelled'
        };
        return statusDisplay[status] || status;
    }

    // Initialize calendar if it exists
    function initializeCalendar() {
        const calendarEl = document.getElementById('calendar');
        if (calendarEl) {
            const calendar = new FullCalendar.Calendar(calendarEl, {
                initialView: 'dayGridMonth',
                headerToolbar: {
                    left: 'prev,next today',
                    center: 'title',
                    right: 'dayGridMonth,timeGridWeek,listWeek'
                },
                events: '/accounting/payment-scheduling/api/schedule-data/',
                eventClick: function(info) {
                    // Navigate to schedule detail
                    window.location.href = `/accounting/payment-scheduling/schedules/${info.event.id}/`;
                },
                eventClassNames: function(arg) {
                    return [arg.event.extendedProps.status];
                },
                eventColor: function(arg) {
                    const colors = {
                        'paid': '#1cc88a',
                        'overdue': '#e74a3b',
                        'pending': '#f6c23e',
                        'partially_paid': '#f6c23e',
                        'draft': '#36b9cc'
                    };
                    return colors[arg.event.extendedProps.status] || '#6c757d';
                }
            });
            calendar.render();
        }
    }

    // Initialize form validation
    function initializeFormValidation() {
        const forms = document.querySelectorAll('.needs-validation');
        forms.forEach(function(form) {
            form.addEventListener('submit', function(event) {
                if (!form.checkValidity()) {
                    event.preventDefault();
                    event.stopPropagation();
                }
                form.classList.add('was-validated');
            });
        });
    }

    // Initialize date pickers
    function initializeDatePickers() {
        const dateInputs = document.querySelectorAll('input[type="date"]');
        dateInputs.forEach(function(input) {
            // Set min date to today for future dates
            if (input.classList.contains('future-date')) {
                const today = new Date().toISOString().split('T')[0];
                input.min = today;
            }
        });
    }

    // Initialize amount calculations
    function initializeAmountCalculations() {
        const totalAmountInput = document.getElementById('id_total_amount');
        const vatRateInput = document.getElementById('id_vat_rate');
        const vatAmountDisplay = document.getElementById('vat_amount_display');
        const totalWithVatDisplay = document.getElementById('total_with_vat_display');

        if (totalAmountInput && vatRateInput) {
            function calculateAmounts() {
                const totalAmount = parseFloat(totalAmountInput.value) || 0;
                const vatRate = parseFloat(vatRateInput.value) || 0;
                
                const vatAmount = (totalAmount * vatRate) / 100;
                const totalWithVat = totalAmount + vatAmount;
                
                if (vatAmountDisplay) {
                    vatAmountDisplay.textContent = vatAmount.toFixed(2);
                }
                if (totalWithVatDisplay) {
                    totalWithVatDisplay.textContent = totalWithVat.toFixed(2);
                }
            }

            totalAmountInput.addEventListener('input', calculateAmounts);
            vatRateInput.addEventListener('input', calculateAmounts);
        }
    }

    // Initialize bulk actions
    function initializeBulkActions() {
        const selectAllCheckbox = document.getElementById('select-all');
        const scheduleCheckboxes = document.querySelectorAll('.schedule-checkbox');
        const bulkActionForm = document.getElementById('bulk-action-form');

        if (selectAllCheckbox) {
            selectAllCheckbox.addEventListener('change', function() {
                scheduleCheckboxes.forEach(function(checkbox) {
                    checkbox.checked = this.checked;
                });
                updateBulkActionButton();
            });
        }

        scheduleCheckboxes.forEach(function(checkbox) {
            checkbox.addEventListener('change', function() {
                updateBulkActionButton();
            });
        });

        function updateBulkActionButton() {
            const checkedBoxes = document.querySelectorAll('.schedule-checkbox:checked');
            const bulkActionButton = document.getElementById('bulk-action-button');
            
            if (bulkActionButton) {
                if (checkedBoxes.length > 0) {
                    bulkActionButton.disabled = false;
                    bulkActionButton.textContent = `Apply to ${checkedBoxes.length} selected`;
                } else {
                    bulkActionButton.disabled = true;
                    bulkActionButton.textContent = 'Apply to Selected';
                }
            }
        }
    }

    // Initialize payment reminder functionality
    function initializePaymentReminders() {
        const reminderButtons = document.querySelectorAll('.create-reminder-btn');
        reminderButtons.forEach(function(button) {
            button.addEventListener('click', function(e) {
                e.preventDefault();
                const scheduleId = this.dataset.scheduleId;
                const modal = new bootstrap.Modal(document.getElementById('reminderModal'));
                
                // Set the schedule ID in the form
                const form = document.getElementById('reminderForm');
                if (form) {
                    const scheduleIdInput = form.querySelector('input[name="schedule_id"]');
                    if (scheduleIdInput) {
                        scheduleIdInput.value = scheduleId;
                    }
                }
                
                modal.show();
            });
        });
    }

    // Initialize all functions
    initializeStatusChange();
    initializeCalendar();
    initializeFormValidation();
    initializeDatePickers();
    initializeAmountCalculations();
    initializeBulkActions();
    initializePaymentReminders();

    // Export functionality
    window.exportToExcel = function() {
        const table = document.querySelector('.table');
        if (table) {
            const wb = XLSX.utils.table_to_book(table, {sheet: "Payment Schedules"});
            XLSX.writeFile(wb, `payment_schedules_${new Date().toISOString().split('T')[0]}.xlsx`);
        }
    };

    window.exportToPDF = function() {
        const element = document.getElementById('printable-content');
        if (element) {
            html2pdf(element, {
                margin: 1,
                filename: `payment_schedules_${new Date().toISOString().split('T')[0]}.pdf`,
                image: { type: 'jpeg', quality: 0.98 },
                html2canvas: { scale: 2 },
                jsPDF: { unit: 'in', format: 'letter', orientation: 'portrait' }
            });
        }
    };
});
