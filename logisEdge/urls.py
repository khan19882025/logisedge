"""
URL configuration for logisEdge project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from accounts.views import CustomLoginView
from django.views.generic.base import RedirectView
from data_cleaning_tool.merge_duplicates import views as merge_views
from pdf_preview_tool.views import signature_uploader_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('dashboard.urls', namespace='dashboard')),
    path('accounts/', include('accounts.urls')),
    path('company/', include('company.company_urls')),
    path('user/', include('user.user_urls')),
    path('customer/', include('customer.urls')),
    path('service/', include('service.urls')),
    path('port/', include('port.urls')),
    path('salesman/', include('salesman.urls')),
    path('items/', include('items.urls')),
    path('facility/', include('facility.urls')),
    path('quotation/', include('quotation.urls')),
    path('job/', include('job.urls')),
    path('documentation/', include('documentation.urls')),
    path('crossstuffing/', include('crossstuffing.urls')),
    path('grn/', include('grn.urls')),
    path('putaways/', include('putaways.urls')),
    path('delivery_order/', include('delivery_order.urls')),
    path('dispatchnote/', include('dispatchnote.urls')),
    path('rf-scanner/', include('rf_scanner.urls')),
    path('invoicing/invoice/', include('invoice.urls')),
    path('accounting/customer-payments/', include('customer_payments.urls')),
    path('accounting/supplier-payments/', include('supplier_payments.urls')),
    path('accounting/credit-notes/', include('credit_note.urls', namespace='credit_note')),
    path('accounting/debit-notes/', include('debit_note.urls', namespace='debit_note')),
    path('accounting/supplier-bills/', include('supplier_bills.urls', namespace='supplier_bills')),
    path('accounting/dunning-letters/', include('dunning_letters.urls', namespace='dunning_letters')),
    path('accounting/payment-scheduling/', include('payment_scheduling.urls', namespace='payment_scheduling')),
    path('accounting/billing-payable-tracking/', include('billing_payable_tracking.urls', namespace='billing_payable_tracking')),
    path('multi-currency/', include('multi_currency.urls', namespace='multi_currency')),
    path('fiscal-year/', include('fiscal_year.urls', namespace='fiscal_year')),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('reports/accounts-receivable-aging/', include('accounts_receivable_aging.urls')),
    path('chart-of-accounts/', include('chart_of_accounts.urls', namespace='chart_of_accounts')),
    path('payment-source/', include('payment_source.urls', namespace='payment_source')),
    path('ledger/', include('ledger.urls', namespace='ledger')),
    path('accounting/general-journal/', include('general_journal.urls', namespace='general_journal')),
    path('reports/trial-balance-report/', include('trial_balance.urls', namespace='trial_balance')),
    path('reports/profit-loss-statement/', include('profit_loss_statement.urls', namespace='profit_loss_statement')),
    path('reports/balance-sheet/', include('balance_sheet.urls', namespace='balance_sheet')),
    path('reports/general-ledger/', include('general_ledger_report.urls', namespace='general_ledger_report')),
    path('reports/partner-ledger/', include('partner_ledger.urls', namespace='partner_ledger')),
    path('reports/vendor-ledger/', include('vendor_ledger.urls', namespace='vendor_ledger')),
    path('reports/source-payment-ledger/', include('source_payment_ledger.urls', namespace='source_payment_ledger')),
    path('reports/cash-flow/', include('cash_flow_statement.urls', namespace='cash_flow_statement')),
    path('reports/customs-boe-stock/', include('customs_BOE_report.urls', namespace='customs_BOE_report')),
    path('accounting/payment-voucher/', RedirectView.as_view(url='/accounting/payment-vouchers/', permanent=True)),
    path('accounting/payment-vouchers/', include('payment_voucher.urls', namespace='payment_voucher')),
    path('accounting/receipt-voucher/', RedirectView.as_view(url='/accounting/receipt-vouchers/', permanent=True)),
    path('accounting/receipt-vouchers/', include('receipt_voucher.urls', namespace='receipt_voucher')),
    path('accounting/contra-entry/', include('contra_entry.urls', namespace='contra_entry')),
    path('accounting/adjustment-entries/', include('adjustment_entry.urls', namespace='adjustment_entry')),
    path('accounting/opening-balances/', RedirectView.as_view(url='/accounting/opening-balance/', permanent=True)),
    path('accounting/opening-balance/', include('opening_balance.urls', namespace='opening_balance')),
    path('accounting/all-transactions/', include('all_transactions.urls', namespace='all_transactions')),
    path('accounting/manual-journal-entry/', include('manual_journal_entry.urls', namespace='manual_journal_entry')),
    path('accounting/recurring-entries/', RedirectView.as_view(url='/accounting/recurring-journal-entry/', permanent=True)),
    path('accounting/recurring-journal-entry/', include('recurring_journal_entry.urls', namespace='recurring_journal_entry')),
    path('accounting/bank-accounts/', include('bank_accounts.urls', namespace='bank_accounts')),
    path('accounting/bank-reconciliation/', include('bank_reconciliation.urls', namespace='bank_reconciliation')),
    path('accounting/cheque-register/', include('cheque_register.urls', namespace='cheque_register')),
    path('accounting/deposit-slips/', include('deposit_slip.urls', namespace='deposit_slip')),
    path('accounting/bank-transfers/', include('bank_transfer.urls', namespace='bank_transfer')),
    path('accounting/cash-transactions/', include('cash_transactions.urls', namespace='cash_transactions')),
    path('accounting/petty-cash/', include('petty_cash.urls', namespace='petty_cash')),
    path('accounting/asset-register/', include('asset_register.urls', namespace='asset_register')),
    path('accounting/dispose-asset/', include('dispose_asset.urls', namespace='dispose_asset')),
    path('accounting/define-cost-centers/', include('cost_center_management.urls', namespace='cost_center_management')),
    path('accounting/assign-transactions/', include('cost_center_transaction_tagging.urls', namespace='cost_center_transaction_tagging')),
    path('accounting/cost-center-reports/', include('cost_center_reports.urls', namespace='cost_center_reports')),
    path('accounting/budget-planning/', include('budget_planning.urls', namespace='budget_planning')),
    path('accounting/budget-vs-actual/', RedirectView.as_view(url='/accounting/budget-planning/budget-vs-actual/', permanent=True)),
    path('accounting/variance-reports/', RedirectView.as_view(url='/accounting/budget-planning/reports/variance/', permanent=True)),
    path('stock-transfer/', include('stock_transfer.urls', namespace='stock_transfer')),
    path('location-transfer/', include('location_transfer.urls', namespace='location_transfer')),
    path('storage-invoice/', include('storage_invoice.urls', namespace='storage_invoice')),
    path('charges/', include('charges.urls', namespace='charges')),
    path('hr/employee-management/', include('employees.urls', namespace='employees')),
    path('utilities/manual-backup/', include('manual_backup.urls', namespace='manual_backup')),
    path('hr/attendance/', include('attendance.urls', namespace='attendance')),
    path('hr/leave-management/', include('leave_management.urls', namespace='leave_management')),
    path('hr/payroll/', include('payroll.urls', namespace='payroll')),
    path('hr/recruitment/', include('recruitment.urls', namespace='recruitment')),
    path('hr/disciplinary-grievance/', include('disciplinary_grievance.urls', namespace='disciplinary_grievance')),
    path('hr/letters-documents/', include('hr_letters_documents.urls', namespace='hr_letters_documents')),
    path('hr/exit-management/', include('exit_management.urls', namespace='exit_management')),
    path('freight-quotation/', include('freight_quotation.urls', namespace='freight_quotation')),
    path('freight-booking/', include('freight_booking.urls', namespace='freight_booking')),
    path('container-management/', include('container_management.urls', namespace='container_management')),
    path('shipment-tracking/', include('shipment_tracking.urls', namespace='shipment_tracking')),
    path('tax-settings/', include('tax_settings.urls', namespace='tax_settings')),
    path('tax-summary/', include('tax_summary.urls', namespace='tax_summary')),
    path('tax-filing/', include('tax_filing.urls', namespace='tax_filing')),
    path('tax-invoice/', include('tax_invoice.urls', namespace='tax_invoice')),
    path('depreciation-schedule/', include('depreciation_schedule.urls', namespace='depreciation_schedule')),
    path('asset-movement-log/', include('asset_movement_log.urls', namespace='asset_movement_log')),
    path('bill-of-lading/', include('bill_of_lading.urls', namespace='bill_of_lading')),
    path('settings/approval-workflows/', include('approval_workflow.urls', namespace='approval_workflow')),
    path('settings/roles-permissions/', include('roles_permissions.urls', namespace='roles_permissions')),
    path('settings/master-data-import/', include('master_data_import.urls', namespace='master_data_import')),
    path('utilities/import-master-data/', include('master_data_import.urls', namespace='master_data_import_utilities')),
    path('utilities/bulk-export/', include('bulk_export.urls', namespace='bulk_export')),
    path('utilities/data-cleaning/', include('data_cleaning_tool.urls', namespace='data_cleaning_tool')),
    path('utilities/merge-duplicates/', merge_views.merge_duplicates_dashboard, name='merge_duplicates_dashboard'),
    path('utilities/backup-scheduler/', include('backup_scheduler.urls', namespace='backup_scheduler')),
    path('utilities/activity-logs/', include('activity_logs.urls', namespace='activity_logs')),
    path('utilities/log-history/', include('log_history.urls', namespace='log_history')),
    path('utilities/system-logs/', include('system_logs.urls', namespace='system_logs')),
    path('utilities/email-configuration/', include('email_configuration.urls', namespace='email_configuration')),
    path('utilities/sms-gateway/', include('sms_gateway.urls', namespace='sms_gateway')),
    path('utilities/bulk-email-sender/', include('bulk_email_sender.urls', namespace='bulk_email_sender')),
    path('utilities/notification-templates/', include('notification_templates.urls', namespace='notification_templates')),
    path('utilities/print-queue/', RedirectView.as_view(url='/utilities/print-queue-management/', permanent=False)),
    path('print-queue/', RedirectView.as_view(url='/utilities/print-queue-management/', permanent=False)),
    path('utilities/print-queue-management/', include('print_queue_management.urls', namespace='print_queue_management')),
    path('utilities/pdf-preview/', RedirectView.as_view(url='/utilities/pdf-preview-tool/', permanent=False)),
    path('utilities/pdf-preview-tool/', include('pdf_preview_tool.urls', namespace='pdf_preview_tool')),
    path('utilities/signature-stamp/', signature_uploader_view, name='signature_stamp'),
    path('utilities/auto-task-scheduler/', include('auto_task_scheduler.urls', namespace='auto_task_scheduler')),
    path('utilities/cron-job-viewer/', include('cron_job_viewer.urls', namespace='cron_job_viewer')),
    path('lgp/', include('lgp.urls', namespace='lgp')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
