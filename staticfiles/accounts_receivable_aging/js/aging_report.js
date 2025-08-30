/**
 * Accounts Receivable Aging Report JavaScript
 * Handles form interactions, AJAX requests, and dynamic updates
 */

(function($) {
    'use strict';

    // Initialize when document is ready
    $(document).ready(function() {
        AgingReport.init();
    });

    // Main AgingReport object
    window.AgingReport = {
        // Configuration
        config: {
            urls: {
                agingSummary: '/reports/accounts-receivable-aging/api/summary/',
                exportReport: '/reports/accounts-receivable-aging/export/',
                emailReport: '/reports/accounts-receivable-aging/email/'
            },
            selectors: {
                filterForm: '#aging-form',
                exportForm: '#export-form',
                loadingSpinner: '.loading-spinner',
                summaryCards: '.summary-cards',
                reportTable: '#aging-report-table',
                exportButton: '#export-btn'
            }
        },

        // Initialize the application
        init: function() {
            this.bindEvents();
            this.initializeDatePickers();
            this.loadInitialData();
        },

        // Bind event handlers
        bindEvents: function() {
            var self = this;

            // Filter form submission - allow normal submission for Generate Report button
            $(this.config.selectors.filterForm).on('submit', function(e) {
                // Allow normal form submission for Generate Report
                // The form will submit normally to reload the page with new data
            });

            // Export button event handlers
            $('#export-excel').on('click', function() {
                self.exportReport('excel');
            });

            $('#export-pdf').on('click', function() {
                self.exportReport('pdf');
            });

            $('#send-email').on('click', function() {
                self.sendEmailReport();
            });

            // Bind email modal send button
            $('#sendEmailBtn').on('click', function(e) {
                e.preventDefault();
                self.handleEmailSubmission();
            });

            // Real-time filter updates
            $(this.config.selectors.filterForm + ' input, ' + this.config.selectors.filterForm + ' select').on('change', function() {
                self.debounce(function() {
                    self.applyFilters();
                }, 500)();
            });

            // Reset filters
            $('#reset-filters').on('click', function() {
                self.resetFilters();
            });

            // Table sorting
            $('.sortable').on('click', function() {
                self.sortTable($(this));
            });

            // Row selection for bulk actions
            $('.row-checkbox').on('change', function() {
                self.updateBulkActions();
            });

            // Select all checkbox
            $('#select-all').on('change', function() {
                self.toggleSelectAll($(this).is(':checked'));
            });
        },

        // Initialize date pickers
        initializeDatePickers: function() {
            if ($.fn.datepicker) {
                $('#as_of_date').datepicker({
                    format: 'yyyy-mm-dd',
                    autoclose: true,
                    todayHighlight: true
                });
            }
        },

        // Load initial data
        loadInitialData: function() {
            this.updateSummaryCards();
        },

        // Apply filters and refresh data
        applyFilters: function() {
            var self = this;
            var formData = $(this.config.selectors.filterForm).serialize();

            this.showLoading();

            // Update summary cards
            this.updateSummaryCards(formData);

            // Update table (if using AJAX)
            this.updateReportTable(formData);
        },

        // Update summary cards via AJAX
        updateSummaryCards: function(formData) {
            var self = this;
            
            // If no formData provided, get current form data or use defaults
            if (!formData) {
                formData = $(this.config.selectors.filterForm).serialize();
                // If form is empty, provide default as_of_date
                if (!formData) {
                    var today = new Date().toISOString().split('T')[0];
                    formData = 'as_of_date=' + today;
                }
            }
            
            console.log('Making AJAX request with data:', formData);
            
            $.ajax({
                url: this.config.urls.agingSummary,
                type: 'GET',
                data: formData,
                success: function(response) {
                    console.log('AJAX success response:', response);
                    if (response.summary) {
                        // Update default currency if provided in response
                        if (response.default_currency) {
                            window.DEFAULT_CURRENCY = response.default_currency;
                        }
                        self.renderSummaryCards(response.summary);
                    }
                },
                error: function(xhr, status, error) {
                    console.error('AJAX error details:', {
                        status: xhr.status,
                        statusText: xhr.statusText,
                        responseText: xhr.responseText,
                        error: error
                    });
                    console.error('Error updating summary cards:', error);
                    self.showError('Failed to update summary data');
                },
                complete: function() {
                    self.hideLoading();
                }
            });
        },

        // Render summary cards
        renderSummaryCards: function(data) {
            var summaryHtml = '<div class="row mb-4 summary-cards">';
            
            // Current (0-30 days)
            summaryHtml += this.createSummaryCard(
                'Current',
                this.formatCurrency(data.current || 0),
                'current'
            );

            // 1-30 days
            summaryHtml += this.createSummaryCard(
                '1-30 Days',
                this.formatCurrency(data.days_1_30 || 0),
                '30-days'
            );

            // 31-60 days
            summaryHtml += this.createSummaryCard(
                '31-60 Days',
                this.formatCurrency(data.days_31_60 || 0),
                '30-days'
            );

            // 61-90 days
            summaryHtml += this.createSummaryCard(
                '61-90 Days',
                this.formatCurrency(data.days_61_90 || 0),
                '60-days'
            );

            // Over 90 days
            summaryHtml += this.createSummaryCard(
                'Over 90 Days',
                this.formatCurrency(data.over_90 || 0),
                'overdue'
            );

            // Total Outstanding
            summaryHtml += this.createSummaryCard(
                'Total Outstanding',
                this.formatCurrency(data.total_outstanding || 0),
                'total'
            );
            
            summaryHtml += '</div>';

            $(this.config.selectors.summaryCards).html(summaryHtml);
        },

        // Create summary card HTML
        createSummaryCard: function(title, amount, type) {
            var colorClass = 'text-primary';
            if (type === 'current') colorClass = 'text-success';
            else if (type === '30-days' || type === '60-days') colorClass = 'text-warning';
            else if (type === 'overdue') colorClass = 'text-danger';
            
            var borderClass = type === 'total' ? 'border-primary' : '';
            var customerCount = type === 'total' ? '<small class="text-muted">customers</small>' : '';
            
            return `
                <div class="col-xl-2 col-lg-2 col-md-4 col-sm-6 col-12 mb-3">
                    <div class="card summary-card text-center ${borderClass}">
                        <div class="card-body">
                            <h6 class="card-title text-muted">${title}</h6>
                            <h4 class="${colorClass}">${amount}</h4>
                            ${customerCount}
                        </div>
                    </div>
                </div>
            `;
        },

        // Update report table
        updateReportTable: function(formData) {
            // If using AJAX for table updates, implement here
            // For now, we'll submit the form to reload the page
            if (formData) {
                $(this.config.selectors.filterForm)[0].submit();
            }
        },

        // Export report
        exportReport: function(format) {
            var self = this;
            format = format || 'pdf';
            
            // Get the appropriate form based on format
            var formId = '#export-' + format + '-form';
            var $form = $(formId);
            
            if ($form.length === 0) {
                console.error('Export form not found for format:', format);
                return;
            }

            // Update form with current filter values
            this.updateExportFormData($form);

            // Show loading state on the clicked button
            var $exportBtn = $('#export-' + format);
            var originalText = $exportBtn.text();
            $exportBtn.text('Exporting...').prop('disabled', true);

            // Submit the form
            $form.submit();

            // Reset button state
            setTimeout(function() {
                $exportBtn.text(originalText).prop('disabled', false);
            }, 2000);
        },

        // Update export form data with current filter values
        updateExportFormData: function($form) {
            var $filterForm = $(this.config.selectors.filterForm);
            
            // Update hidden fields with current filter values
            $form.find('input[name="as_of_date"]').val($filterForm.find('input[name="as_of_date"]').val() || '');
            $form.find('input[name="customer"]').val($filterForm.find('select[name="customer"]').val() || '');
            $form.find('input[name="salesman"]').val($filterForm.find('select[name="salesman"]').val() || '');
            $form.find('input[name="customer_code"]').val($filterForm.find('input[name="customer_code"]').val() || '');
            $form.find('input[name="min_amount"]').val($filterForm.find('input[name="min_amount"]').val() || '');
            $form.find('input[name="aging_bucket"]').val($filterForm.find('select[name="aging_bucket"]').val() || '');
            $form.find('input[name="show_zero_balances"]').val($filterForm.find('input[name="show_zero_balances"]').is(':checked') ? 'true' : 'false');
        },

        // Send email report
        sendEmailReport: function() {
            // Update email form with current filter values
            this.updateEmailFormData();
            
            // Show the email modal
            var emailModal = new bootstrap.Modal(document.getElementById('emailModal'));
            emailModal.show();
        },

        // Update email form data with current filter values
        updateEmailFormData: function() {
            var $filterForm = $(this.config.selectors.filterForm);
            
            // Update hidden fields in email form
            $('#email_as_of_date').val($filterForm.find('input[name="as_of_date"]').val() || '');
            $('#email_customer').val($filterForm.find('select[name="customer"]').val() || '');
            $('#email_customer_code').val($filterForm.find('input[name="customer_code"]').val() || '');
            $('#email_min_amount').val($filterForm.find('input[name="min_amount"]').val() || '');
            $('#email_aging_bucket').val($filterForm.find('select[name="aging_bucket"]').val() || '');
            $('#email_show_zero_balances').val($filterForm.find('input[name="show_zero_balances"]').is(':checked') ? 'on' : 'off');
        },

        // Handle email form submission
        handleEmailSubmission: function() {
            var self = this;
            var $emailForm = $('#emailForm');
            var $sendBtn = $('#sendEmailBtn');
            var originalText = $sendBtn.html();
            
            // Validate required fields
            var recipientEmail = $('#recipient_email').val().trim();
            var subject = $('#email_subject').val().trim();
            
            if (!recipientEmail || !subject) {
                alert('Please fill in all required fields (Recipient Email and Subject)');
                return;
            }
            
            // Show loading state
            $sendBtn.prop('disabled', true);
            $sendBtn.html('<i class="bi bi-hourglass-split me-1"></i>Sending...');
            
            // Prepare form data
            var formData = new FormData($emailForm[0]);
            
            // Send AJAX request
            $.ajax({
                url: self.config.urls.emailReport,
                type: 'POST',
                data: formData,
                processData: false,
                contentType: false,
                headers: {
                    'X-CSRFToken': $('[name=csrfmiddlewaretoken]').val()
                },
                success: function(data) {
                    if (data.success) {
                        alert('Email sent successfully!');
                        // Close modal
                        var emailModal = bootstrap.Modal.getInstance(document.getElementById('emailModal'));
                        emailModal.hide();
                        // Reset form
                        $emailForm[0].reset();
                        $('#email_subject').val('Accounts Receivable Aging Report');
                        $('#email_message').val('Please find attached the Accounts Receivable Aging Report.');
                    } else {
                        alert('Error sending email: ' + (data.error || 'Unknown error'));
                    }
                },
                error: function(xhr, status, error) {
                    console.error('Error:', error);
                    alert('Error sending email. Please try again.');
                },
                complete: function() {
                    // Reset button state
                    $sendBtn.prop('disabled', false);
                    $sendBtn.html(originalText);
                }
            });
        },

        // Reset all filters
        resetFilters: function() {
            $(this.config.selectors.filterForm)[0].reset();
            this.applyFilters();
        },

        // Sort table by column
        sortTable: function($header) {
            var table = $header.closest('table');
            var columnIndex = $header.index();
            var isAscending = !$header.hasClass('sort-asc');
            
            // Remove existing sort classes
            table.find('th').removeClass('sort-asc sort-desc');
            
            // Add new sort class
            $header.addClass(isAscending ? 'sort-asc' : 'sort-desc');
            
            // Sort rows
            var rows = table.find('tbody tr').toArray();
            rows.sort(function(a, b) {
                var aValue = $(a).find('td').eq(columnIndex).text().trim();
                var bValue = $(b).find('td').eq(columnIndex).text().trim();
                
                // Try to parse as numbers
                var aNum = parseFloat(aValue.replace(/[^\d.-]/g, ''));
                var bNum = parseFloat(bValue.replace(/[^\d.-]/g, ''));
                
                if (!isNaN(aNum) && !isNaN(bNum)) {
                    return isAscending ? aNum - bNum : bNum - aNum;
                } else {
                    return isAscending ? 
                        aValue.localeCompare(bValue) : 
                        bValue.localeCompare(aValue);
                }
            });
            
            table.find('tbody').html(rows);
        },

        // Update bulk action buttons
        updateBulkActions: function() {
            var selectedCount = $('.row-checkbox:checked').length;
            var $bulkActions = $('.bulk-actions');
            
            if (selectedCount > 0) {
                $bulkActions.show();
                $('.selected-count').text(selectedCount);
            } else {
                $bulkActions.hide();
            }
        },

        // Toggle select all checkboxes
        toggleSelectAll: function(checked) {
            $('.row-checkbox').prop('checked', checked);
            this.updateBulkActions();
        },

        // Show loading spinner
        showLoading: function() {
            $(this.config.selectors.loadingSpinner).show();
        },

        // Hide loading spinner
        hideLoading: function() {
            $(this.config.selectors.loadingSpinner).hide();
        },

        // Show error message
        showError: function(message) {
            // You can implement a toast notification or alert here
            console.error(message);
            alert('Error: ' + message);
        },

        // Format currency
        formatCurrency: function(amount) {
            var currency = window.DEFAULT_CURRENCY || 'USD';
            // Extract just the currency code if it contains additional description
            // e.g., "AED - AED - UAE Dirham" -> "AED"
            if (currency.includes(' - ')) {
                currency = currency.split(' - ')[0];
            }
            return new Intl.NumberFormat('en-US', {
                style: 'currency',
                currency: currency
            }).format(amount || 0);
        },

        // Debounce function
        debounce: function(func, wait) {
            var timeout;
            return function() {
                var context = this, args = arguments;
                clearTimeout(timeout);
                timeout = setTimeout(function() {
                    func.apply(context, args);
                }, wait);
            };
        },

        // Utility function to get URL parameters
        getUrlParameter: function(name) {
            name = name.replace(/[\[]/, '\\[').replace(/[\]]/, '\\]');
            var regex = new RegExp('[\\?&]' + name + '=([^&#]*)');
            var results = regex.exec(location.search);
            return results === null ? '' : decodeURIComponent(results[1].replace(/\+/g, ' '));
        },

        // Print report
        printReport: function() {
            window.print();
        },

        // Refresh data
        refreshData: function() {
            this.applyFilters();
        }
    };

    // Add CSS for sorting indicators
    var sortingCSS = `
        <style>
        .sortable {
            cursor: pointer;
            position: relative;
            user-select: none;
        }
        .sortable:hover {
            background-color: #f8f9fa;
        }
        .sortable::after {
            content: '\u2195';
            position: absolute;
            right: 8px;
            opacity: 0.5;
        }
        .sortable.sort-asc::after {
            content: '\u2191';
            opacity: 1;
        }
        .sortable.sort-desc::after {
            content: '\u2193';
            opacity: 1;
        }
        .bulk-actions {
            display: none;
            background: #e3f2fd;
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 15px;
        }
        </style>
    `;
    
    $('head').append(sortingCSS);

})(jQuery);

// Global functions for template use
function applyFilters() {
    AgingReport.applyFilters();
}

function exportReport() {
    AgingReport.exportReport();
}

function printReport() {
    AgingReport.printReport();
}

function refreshData() {
    AgingReport.refreshData();
}