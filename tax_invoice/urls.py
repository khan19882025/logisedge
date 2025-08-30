from django.urls import path
from . import views

app_name = 'tax_invoice'

urlpatterns = [
    # Dashboard
    path('', views.tax_invoice_dashboard, name='dashboard'),
    
    # Invoices
    path('invoices/', views.TaxInvoiceListView.as_view(), name='invoice_list'),
    path('invoices/create/', views.TaxInvoiceCreateView.as_view(), name='invoice_create'),
    path('invoices/<uuid:pk>/', views.TaxInvoiceDetailView.as_view(), name='invoice_detail'),
    path('invoices/<uuid:pk>/update/', views.TaxInvoiceUpdateView.as_view(), name='invoice_update'),
    path('invoices/<uuid:pk>/delete/', views.TaxInvoiceDeleteView.as_view(), name='invoice_delete'),
    path('invoices/<uuid:pk>/export/', views.export_tax_invoice, name='export_invoice'),
    
    # Templates
    path('templates/', views.TaxInvoiceTemplateListView.as_view(), name='template_list'),
    path('templates/create/', views.TaxInvoiceTemplateCreateView.as_view(), name='template_create'),
    path('templates/<uuid:pk>/', views.TaxInvoiceTemplateDetailView.as_view(), name='template_detail'),
    path('templates/<uuid:pk>/update/', views.TaxInvoiceTemplateUpdateView.as_view(), name='template_update'),
    path('templates/<uuid:pk>/delete/', views.TaxInvoiceTemplateDeleteView.as_view(), name='template_delete'),
    
    # Calculator
    path('calculator/', views.tax_invoice_calculator, name='calculator'),
    
    # Settings
    path('settings/', views.tax_invoice_settings, name='settings'),
    
    # API
    path('api/', views.tax_invoice_api, name='api'),
]
