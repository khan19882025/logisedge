from django.urls import path
from . import views

app_name = 'vendor_ledger'

urlpatterns = [
    path('', views.vendor_ledger_report, name='vendor_ledger_report'),
    path('export/excel/', views.export_excel, name='export_excel'),
    path('export/pdf/', views.export_pdf, name='export_pdf'),
    path('ajax/quick-filter/', views.ajax_quick_filter, name='ajax_quick_filter'),
]