from django.urls import path
from . import views

app_name = 'tax_summary'

urlpatterns = [
    # Dashboard
    path('', views.tax_summary_dashboard, name='dashboard'),
    
    # Reports
    path('reports/', views.TaxSummaryReportListView.as_view(), name='report_list'),
    path('reports/create/', views.TaxSummaryReportCreateView.as_view(), name='report_create'),
    path('reports/<uuid:pk>/', views.TaxSummaryReportDetailView.as_view(), name='report_detail'),
    path('reports/<uuid:pk>/update/', views.TaxSummaryReportUpdateView.as_view(), name='report_update'),
    path('reports/<uuid:pk>/delete/', views.TaxSummaryReportDeleteView.as_view(), name='report_delete'),
    
    # Generate report
    path('reports/<uuid:pk>/generate/', views.generate_tax_summary, name='generate_report'),
    
    # Transactions
    path('reports/<uuid:pk>/transactions/', views.tax_summary_transactions, name='transactions'),
    
    # Export
    path('reports/<uuid:pk>/export/', views.export_tax_summary, name='export_report'),
    
    # API
    path('api/', views.tax_summary_api, name='api'),
]
