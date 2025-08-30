from django.urls import path
from . import views

app_name = 'tax_settings'

urlpatterns = [
    # Dashboard
    path('', views.tax_dashboard, name='dashboard'),
    
    # Tax Jurisdictions
    path('jurisdictions/', views.TaxJurisdictionListView.as_view(), name='jurisdiction_list'),
    path('jurisdictions/create/', views.TaxJurisdictionCreateView.as_view(), name='jurisdiction_create'),
    path('jurisdictions/<uuid:pk>/', views.TaxJurisdictionDetailView.as_view(), name='jurisdiction_detail'),
    path('jurisdictions/<uuid:pk>/update/', views.TaxJurisdictionUpdateView.as_view(), name='jurisdiction_update'),
    path('jurisdictions/<uuid:pk>/delete/', views.TaxJurisdictionDeleteView.as_view(), name='jurisdiction_delete'),
    
    # Tax Types
    path('tax-types/', views.TaxTypeListView.as_view(), name='tax_type_list'),
    path('tax-types/create/', views.TaxTypeCreateView.as_view(), name='tax_type_create'),
    path('tax-types/<uuid:pk>/', views.TaxTypeDetailView.as_view(), name='tax_type_detail'),
    path('tax-types/<uuid:pk>/update/', views.TaxTypeUpdateView.as_view(), name='tax_type_update'),
    path('tax-types/<uuid:pk>/delete/', views.TaxTypeDeleteView.as_view(), name='tax_type_delete'),
    
    # Tax Rates
    path('tax-rates/', views.TaxRateListView.as_view(), name='tax_rate_list'),
    path('tax-rates/create/', views.TaxRateCreateView.as_view(), name='tax_rate_create'),
    path('tax-rates/<uuid:pk>/', views.TaxRateDetailView.as_view(), name='tax_rate_detail'),
    path('tax-rates/<uuid:pk>/update/', views.TaxRateUpdateView.as_view(), name='tax_rate_update'),
    path('tax-rates/<uuid:pk>/delete/', views.TaxRateDeleteView.as_view(), name='tax_rate_delete'),
    
    # Product Tax Categories
    path('product-categories/', views.ProductTaxCategoryListView.as_view(), name='product_category_list'),
    path('product-categories/create/', views.ProductTaxCategoryCreateView.as_view(), name='product_category_create'),
    path('product-categories/<uuid:pk>/', views.ProductTaxCategoryDetailView.as_view(), name='product_category_detail'),
    path('product-categories/<uuid:pk>/update/', views.ProductTaxCategoryUpdateView.as_view(), name='product_category_update'),
    path('product-categories/<uuid:pk>/delete/', views.ProductTaxCategoryDeleteView.as_view(), name='product_category_delete'),
    
    # Customer Tax Profiles
    path('customer-profiles/', views.CustomerTaxProfileListView.as_view(), name='customer_profile_list'),
    path('customer-profiles/create/', views.CustomerTaxProfileCreateView.as_view(), name='customer_profile_create'),
    path('customer-profiles/<uuid:pk>/', views.CustomerTaxProfileDetailView.as_view(), name='customer_profile_detail'),
    path('customer-profiles/<uuid:pk>/update/', views.CustomerTaxProfileUpdateView.as_view(), name='customer_profile_update'),
    path('customer-profiles/<uuid:pk>/delete/', views.CustomerTaxProfileDeleteView.as_view(), name='customer_profile_delete'),
    
    # Supplier Tax Profiles
    path('supplier-profiles/', views.SupplierTaxProfileListView.as_view(), name='supplier_profile_list'),
    path('supplier-profiles/create/', views.SupplierTaxProfileCreateView.as_view(), name='supplier_profile_create'),
    path('supplier-profiles/<uuid:pk>/', views.SupplierTaxProfileDetailView.as_view(), name='supplier_profile_detail'),
    path('supplier-profiles/<uuid:pk>/update/', views.SupplierTaxProfileUpdateView.as_view(), name='supplier_profile_update'),
    path('supplier-profiles/<uuid:pk>/delete/', views.SupplierTaxProfileDeleteView.as_view(), name='supplier_profile_delete'),
    
    # Tax Calculator
    path('calculator/', views.tax_calculator, name='tax_calculator'),
    
    # VAT Reports
    path('vat-reports/', views.VATReportListView.as_view(), name='vat_report_list'),
    path('vat-reports/create/', views.VATReportCreateView.as_view(), name='vat_report_create'),
    path('vat-reports/<uuid:pk>/', views.VATReportDetailView.as_view(), name='vat_report_detail'),
    path('vat-reports/<uuid:pk>/update/', views.VATReportUpdateView.as_view(), name='vat_report_update'),
    path('vat-reports/<uuid:pk>/delete/', views.VATReportDeleteView.as_view(), name='vat_report_delete'),
    path('vat-reports/generate/', views.generate_vat_report, name='generate_vat_report'),
    
    # Audit Logs
    path('audit-logs/', views.AuditLogListView.as_view(), name='audit_log_list'),
    
    # API Endpoints
    path('api/tax-rates-by-jurisdiction/', views.get_tax_rates_by_jurisdiction, name='api_tax_rates_by_jurisdiction'),
    path('api/calculate-tax/', views.calculate_tax_ajax, name='api_calculate_tax'),
    
    # Export
    path('export/', views.export_tax_data, name='export_tax_data'),
]
