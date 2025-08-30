from django.urls import path
from . import views

app_name = 'partner_ledger'

urlpatterns = [
    # Main report view
    path('', views.partner_ledger_report, name='report'),
    
    # Export views
    path('export/excel/', views.export_partner_ledger_excel, name='export_excel'),
    path('export/pdf/', views.export_partner_ledger_pdf, name='export_pdf'),
    
    # AJAX endpoints
    path('ajax/quick-filter/', views.ajax_quick_filter, name='ajax_quick_filter'),
    path('ajax/customer-search/', views.ajax_customer_search, name='ajax_customer_search'),
]