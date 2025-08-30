from django.urls import path
from . import views

app_name = 'tax_filing'

urlpatterns = [
    # Dashboard
    path('', views.tax_filing_dashboard, name='dashboard'),
    
    # Reports
    path('reports/', views.TaxFilingReportListView.as_view(), name='report_list'),
    path('reports/create/', views.TaxFilingReportCreateView.as_view(), name='report_create'),
    path('reports/<uuid:pk>/', views.TaxFilingReportDetailView.as_view(), name='report_detail'),
    path('reports/<uuid:pk>/update/', views.TaxFilingReportUpdateView.as_view(), name='report_update'),
    path('reports/<uuid:pk>/delete/', views.TaxFilingReportDeleteView.as_view(), name='report_delete'),
    path('reports/<uuid:pk>/generate/', views.generate_tax_filing, name='generate_report'),
    path('reports/<uuid:pk>/transactions/', views.tax_filing_transactions, name='transactions'),
    path('reports/<uuid:pk>/validations/', views.tax_filing_validations, name='validations'),
    path('reports/<uuid:pk>/export/', views.export_tax_filing, name='export_report'),
    
    # API
    path('api/', views.tax_filing_api, name='api'),
]
